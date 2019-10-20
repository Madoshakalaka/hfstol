#!/usr/bin/env python3
import argparse
import atexit
import queue
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import List, Iterable, Dict, Set, Tuple, Union
from weakref import WeakSet

from hfstol.shared import Header, Alphabet
from hfstol.transducer import Transducer

PathLike = Union[Path, str]  # python 3.5 compatibility


class HFSTOL:
    # All HFSTOL objects that gets created are added to this
    # weakset. If Python begins tearing down and an HFSTOL process is still in
    # referenced in memory, then all its processes are automatically
    # terminated, before the garbage collector gets involved.
    # _terminate_all_active_hfstol_processes().
    # Once an HFSTOL instance is no longer referenced any more, it is
    # automagically~~ removed from this set!
    ACTIVE_HFSTOL_INSTANCES = WeakSet()  # type: WeakSet

    def __init__(self, header, alphabet, transducer, hfstol_file_path):
        """
        Read a transducer from filename
        """
        self._header = header
        self._alphabet = alphabet
        self._transducer = transducer

        self._hfstol_exe_path = shutil.which("hfst-optimized-lookup")
        self._hfstol_file_path = hfstol_file_path

        self._hfstol_processes = []  # type: List[subprocess.Popen]

        # Keep track of this object, so that if it hasn't been garbage
        # collected by the time the Python process is shutting down, we
        # can terminate all processes before Python starts deleting all the
        # references we need to do so!
        self.ACTIVE_HFSTOL_INSTANCES.add(self)

    def feed(
        self, surface_form: str, concat: bool = True
    ) -> Tuple[Tuple[str, ...], ...]:
        """
        feed surface form to hfst

        :param surface_form: the surface form
        :param concat: whether to concatenate single characters

            example output for `surface_form` = 'niskak', with `crk-descriptive-analyzer.hfstol`
            - True: (('niska', '+N', '+A', '+Pl'), ('nîskâw', '+V', '+II', '+II', '+Cnj', '+Prs', '+3Sg'))
            - False: (('n', 'i', 's', 'k', 'a', '+N', '+A', '+Pl'), ('n', 'î', 's', 'k', 'â', 'w', '+V', '+II', '+II', '+Cnj', '+Prs', '+3Sg'))

            example output for `surface_form` = 'niska+N+A+Pl' with `crk-normative-generator.hfstol`
            - True: (('niskak',),)
            - False: (('n', 'i', 's', 'k', 'a', 'k'),)

            example output for `surface_form` = 'niska+N+A+Pl' with `crk-normative-generator.hfstol` (an inflection that has two spellings)
            - True: (('kinipânaw',), ('kinipânânaw',))
            -False: (('k', 'i', 'n', 'i', 'p', 'â', 'n', 'a', 'w'), ('k', 'i', 'n', 'i', 'p', 'â', 'n', 'â', 'n', 'a', 'w'))
        """
        if surface_form == "":
            return tuple()
        if self._transducer.analyze(surface_form):
            if concat:
                return tuple(concat_res(i) for i in self._transducer.output_list)
            else:
                return tuple(tuple(i) for i in self._transducer.output_list)
        else:
            return tuple()

    def feed_in_bulk(
        self, surface_forms: Iterable[str], concat=True
    ) -> Dict[str, Set[Tuple[str, ...]]]:
        """
        feed a multiple of surface forms to hfst at once

        :param surface_forms:
        :return: a dictionary with keys being each surface form fed in, values being their corresponding deep forms
        """
        res = {
            string: set() for string in surface_forms
        }  # type: Dict[str, Set[Tuple[str,...]]]
        for string in surface_forms:
            res[string] |= set(tuple(self.feed(string, concat)))
        return res

    def feed_in_bulk_fast(
        self, strings: Iterable[str], multi_process: int = 1
    ) -> Dict[str, Set[str]]:
        """
        calls `hfstol-optimized-lookup`. Evaluation is magnitudes faster. Note the generated symbols will all be all concatenated.
        e.g. instead of ['n', 'i', 's', 'k', 'a', '+N', '+A', '+Pl'] it returns ['niska+N+A+Pl']

        :keyword multi_process: Defaults to 1. Specify how many parallel processes you want to speed up computation. A rule is to have processes at most your machine core count.
        """

        if self._hfstol_exe_path is None:
            raise ImportError(
                "hfst-optimized-lookup is not installed.\n"
                "Please install the HFST suite on your system "
                "before using hfstol.\n"
                "See: https://github.com/hfst/hfst#installation"
            )

        while len(self._hfstol_processes) < multi_process:
            proc = subprocess.Popen(
                args=[
                    str(self._hfstol_exe_path),
                    "--quiet",
                    "--pipe-mode",
                    str(self._hfstol_file_path),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                universal_newlines=True,
                bufsize=-1,
            )
            self._hfstol_processes.append(proc)

        return self._call_hfstol(list(strings), multi_process)

    @classmethod
    def from_file(cls, filename: PathLike):
        """
        :param filename: the `.hfstol` file
        :return: an `HFSTOL` instance, which you can use to convert surface forms to deep forms
        """
        handle = open(str(filename), "rb")
        header = Header(handle)
        alphabet = Alphabet(handle, header.number_of_symbols)
        if header.weighted:
            raise NotImplementedError("weighted hfstol is not implemented")
            # todo: refer to https://github.com/hfst/hfst-optimized-lookup/tree/master/hfst-optimized-lookup-python/hfst_lookup and implement
            # self.transducer = TransducerW(handle, self.header, self.alphabet)
        else:
            transducer = Transducer(handle, header, alphabet)
        handle.close()
        return cls(header, alphabet, transducer, filename)

    def _call_hfstol(
        self, inputs: List[str], multi_process: int
    ) -> Dict[str, Set[str]]:
        """
        call hfstol and return concatenated results
        """

        length = len(inputs)
        words_per_process = [
            inputs[length * i // multi_process : length * (i + 1) // multi_process]
            for i in range(multi_process)
        ]

        message_queue = queue.Queue()  # type: queue.Queue

        def interact_with_process(
            p: subprocess.Popen, mq: queue.Queue, words: List[str]
        ):
            def _write_lines(stdin, lines):
                for line in lines:
                    stdin.write(line + "\n")
                p.stdin.flush()

            received_count = 0
            old_line = ""
            m_lines = []  # type: List[str]
            threading.Thread(target=_write_lines, args=(p.stdin, words)).start()

            while received_count < len(words):
                line = p.stdout.readline().strip("\r\n")
                if line:
                    mq.put(line)
                elif old_line:
                    received_count += 1
                old_line = line
            mq.put(None)

        for i, proc in enumerate(self._hfstol_processes[:multi_process]):
            threading.Thread(
                target=interact_with_process,
                args=(proc, message_queue, words_per_process[i]),
            ).start()

        results = {original: set() for original in inputs}  # type: Dict[str, Set[str]]

        ended_count = 0

        while ended_count != multi_process:
            line = message_queue.get()
            if line is None:
                ended_count += 1
                continue
            # Each line will be in this form:
            #    <original_input>\t<res>
            # e.g. in the case of analyzer file
            # nôhkominân    nôhkom+N+A+D+Px1Pl+Sg
            # e.g. in the case of generator file
            # nôhkom+N+A+D+Px1Pl+Sg     nôhkominân
            # If the hfstol can't compute, the transduction will have +?:
            # e.g.,
            #   sadijfijfe	sadijfijfe	+?
            original_input, res, *rest = line.split("\t")

            if "+?" not in rest and "+?" not in res:
                results[original_input].add(res)

        return results

    def __del__(self):
        self._terminate_all_processes()

    def _terminate_all_processes(self):
        """
        Terminates all active hfst-optimized-lookup processes created by this
        instance.
        """
        while self._hfstol_processes:
            proc = self._hfstol_processes.pop()
            proc.terminate()

    @staticmethod
    @atexit.register
    def _terminate_all_active_hfstol_processes():
        """
        Terminates any hfst-optimized-lookup process that have not yet been
        garbage collected.
        """
        for instance in HFSTOL.ACTIVE_HFSTOL_INSTANCES:
            instance._terminate_all_processes()


def cmd():
    parser = argparse.ArgumentParser(description="hfst-optimized-lookup in python")

    parser.add_argument(
        "filename", action="store", type=str, help="The file path of the .hfstol file"
    )

    argv = parser.parse_args()

    transducerfile = open(argv.filename, "rb")
    header = Header(transducerfile)
    print("header read")
    alphabet = Alphabet(transducerfile, header.number_of_symbols)
    print("alphabet read")
    if header.weighted:
        # transducer = TransducerW(transducerfile, header, alphabet)
        # todo: refer to https://github.com/hfst/hfst-optimized-lookup/tree/master/hfst-optimized-lookup-python/hfst_lookup and implement
        raise NotImplementedError("weighted hfstol is not implemented")
    else:
        transducer = Transducer(transducerfile, header, alphabet)
    print("transducer ready")
    print()

    while True:
        try:
            string = input()
        except EOFError:
            sys.exit(0)
        print(string + ":")
        if transducer.analyze(string):
            transducer.printAnalyses()
            print()
        else:
            # tokenization failed
            pass


def concat_res(i) -> Tuple[str, ...]:
    res = []  # type: List[str]
    buffer = ""

    encountered = False
    for symbol in i:
        # print(symbol)
        if len(symbol) == 1:
            encountered = True
            buffer += symbol
        else:
            if encountered:
                res.append(buffer)
                encountered = False
            res.append(symbol)
    if encountered:
        res.append(buffer)
    return tuple(res)


if __name__ == "__main__":
    # just to provide a way to test the cmd entry point
    cmd()

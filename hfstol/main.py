#!/usr/bin/env python3
import argparse
import queue
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import List, Iterable, Dict, Set, Tuple, Union

from hfstol.shared import Header, Alphabet
from hfstol.transducer import Transducer

PathLike = Union[Path, str]  # python 3.5 compatibility


class HFSTOL:
    def __init__(self, header, alphabet, transducer, hfstol_file_path):
        """
        Read a transducer from filename
        """
        self._header = header
        self._alphabet = alphabet
        self._transducer = transducer

        self._hfstol_exe_path = shutil.which("hfst-optimized-lookup")
        self._hfstol_file_path = hfstol_file_path

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

        # hfst-optimized-lookup expects each analysis on a separate line:
        # lines = "\n".join(inputs).encode("UTF-8")
        length = len(inputs)
        lines_per_process = [
            "\n".join(
                inputs[length * i // multi_process : length * (i + 1) // multi_process]
            ).encode("UTF-8")
            for i in range(multi_process)
        ]

        procs = [
            subprocess.Popen(
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
            )
            for _ in range(multi_process)
        ]

        message_queue = queue.Queue()  # type: queue.Queue

        for i, proc in enumerate(procs):
            proc.stdin.write(lines_per_process[i])

            threading.Thread(
                target=lambda p: message_queue.put(p.communicate()), args=(proc,)
            ).start()

        returned_process_count = 0

        results = {original: set() for original in inputs}  # type: Dict[str, Set[str]]

        while returned_process_count != len(lines_per_process):
            outs, err = message_queue.get()
            returned_process_count += 1

            for line in outs.decode("UTF-8").splitlines():
                # Remove extraneous whitespace.
                line = line.strip()
                # Skip empty lines.
                if not line:
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

            # yield tuple(res_buffer)

        return results


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

#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Union, List, Iterable

from hfstol.shared import Header, Alphabet
from hfstol.transducer import Transducer

PathLike = Union[str, Path]  # stupid python 3.5


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

    def analyze(self, string) -> List[List[str]]:
        """
        Take string to analyse
        """
        if self._transducer.analyze(string):
            return self._transducer.output_list
        else:
            return []

    def analyze_in_bulk(self, strings) -> List[List[List[str]]]:
        """

        :param strings:
        :return:
        """
        res = []
        for string in strings:
            res.append(self.analyze(string))
        return res

    def analyze_in_bulk_fast(self, strings) -> List[List[str]]:
        """
        returns the concatenated version, e.g. instead of ['n', 'i', 's', 'k', 'a', '+N', '+A', '+Pl'] it returns ['niska+N+A+Pl']
        """

        if self._hfstol_exe_path is None:
            raise ImportError(
                "hfst-optimized-lookup is not installed.\n"
                "Please install the HFST suite on your system "
                "before using hfstol.\n"
                "See: https://github.com/hfst/hfst#installation"
            )

        return self._call_hfstol(strings)

    @classmethod
    def from_file(cls, filename: PathLike):
        handle = open(filename, "rb")
        header = Header(handle)
        alphabet = Alphabet(handle, header.number_of_symbols)
        if header.weighted:
            raise NotImplementedError('weighted hfstol is not implemented')
            # todo: refer to https://github.com/hfst/hfst-optimized-lookup/tree/master/hfst-optimized-lookup-python/hfst_lookup and implement
            # self.transducer = TransducerW(handle, self.header, self.alphabet)
        else:
            transducer = Transducer(handle, header, alphabet)
        handle.close()
        return cls(header, alphabet, transducer, filename)

    def _call_hfstol(self, inputs: Iterable[str]) -> List[List[str]]:
        """
        call hfstol and return concatenated results
        """

        # hfst-optimized-lookup expects each analysis on a separate line:
        lines = "\n".join(inputs).encode("UTF-8")

        status = subprocess.run(
            [
                str(self._hfstol_exe_path),
                "--quiet",
                "--pipe-mode",
                str(self._hfstol_file_path),
            ],
            input=lines,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )

        results = {original: set() for original in inputs}

        res_buffer = []  # type: List[str]
        for line in status.stdout.decode("UTF-8").splitlines():
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

            if '+?' not in rest and '+?' not in res:
                results[original_input].add(tuple(res_buffer))

        # yield tuple(res_buffer)

        return results


def cmd():
    parser = argparse.ArgumentParser(
        description="hfst-optimized-lookup in python"
    )

    parser.add_argument(
        "filename",
        action="store",
        type=str,
        help="The file path of the .hfstol file",
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
        raise NotImplementedError('weighted hfstol is not implemented')
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


if __name__ == "__main__":
    # just to provide a way to test the cmd entry point
    cmd()

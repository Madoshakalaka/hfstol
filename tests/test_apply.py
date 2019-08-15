import os
import subprocess
import sys
import unittest
from os import path

import pytest

from hfstol import main


@pytest.mark.parametrize(
    "surface_form,result",
    [
        ("nîskâw", (("nîskâw", "+V", "+II", "+Ind", "+Prs", "+3Sg"),)),
        ("nipâw", (("nipâw", "+V", "+AI", "+Ind", "+Prs", "+3Sg"),)),
    ],
)
def test_single_analysis_single_deep_form(cree_analyzer, surface_form, result):
    assert cree_analyzer.feed(surface_form) == result


@pytest.mark.parametrize(
    "surface_form,result",
    [
        (
            "nîskâw",
            (("n", "î", "s", "k", "â", "w", "+V", "+II", "+Ind", "+Prs", "+3Sg"),),
        ),
        ("nipâw", (("n", "i", "p", "â", "w", "+V", "+AI", "+Ind", "+Prs", "+3Sg"),)),
    ],
)
def test_single_analysis_single_deep_form_split(cree_analyzer, surface_form, result):
    assert cree_analyzer.feed(surface_form, concat=False) == result


@pytest.mark.parametrize(
    "surface_form,result",
    [("niska", (("niska", "+N", "+A", "+Sg"), ("niska", "+N", "+A", "+Obv")))],
)
def test_singled_analysis_multiple_deep_form(cree_analyzer, surface_form, result):
    assert cree_analyzer.feed(surface_form) == result


@pytest.mark.parametrize(
    "surface_form,result",
    [
        (
            "niska",
            (
                ("n", "i", "s", "k", "a", "+N", "+A", "+Sg"),
                ("n", "i", "s", "k", "a", "+N", "+A", "+Obv"),
            ),
        )
    ],
)
def test_singled_analysis_multiple_deep_form_split(cree_analyzer, surface_form, result):
    assert cree_analyzer.feed(surface_form, concat=False) == result


@pytest.mark.parametrize("surface_form,result", [("abcdefg", ()), ("", ())])
def test_singled_analysis_out_side_alphabet(cree_analyzer, surface_form, result):
    assert cree_analyzer.feed(surface_form) == result
    assert cree_analyzer.feed(surface_form, concat=False) == result


@pytest.mark.parametrize(
    "surface_forms,result",
    [
        (
            ("niskak", "nîskâw", "nipâw", "abcdefg"),
            {
                "niskak": {
                    ("niska", "+N", "+A", "+Pl"),
                    ("nîskâw", "+V", "+II", "+Cnj", "+Prs", "+3Sg"),
                },
                "nîskâw": {("nîskâw", "+V", "+II", "+Ind", "+Prs", "+3Sg")},
                "nipâw": {("nipâw", "+V", "+AI", "+Ind", "+Prs", "+3Sg")},
                "abcdefg": set(),
            },
        )
    ],
)
def test_multiple_analyses(cree_analyzer, surface_forms, result):
    assert cree_analyzer.feed_in_bulk(surface_forms) == result


@pytest.mark.parametrize(
    "surface_forms,result",
    [
        (
            ("niskak", "nîskâw", "nipâw", "abcdefg"),
            {
                "niskak": {
                    ("n", "i", "s", "k", "a", "+N", "+A", "+Pl"),
                    ("n", "î", "s", "k", "â", "w", "+V", "+II", "+Cnj", "+Prs", "+3Sg"),
                },
                "nîskâw": {
                    ("n", "î", "s", "k", "â", "w", "+V", "+II", "+Ind", "+Prs", "+3Sg")
                },
                "nipâw": {
                    ("n", "i", "p", "â", "w", "+V", "+AI", "+Ind", "+Prs", "+3Sg")
                },
                "abcdefg": set(),
            },
        )
    ],
)
def test_multiple_analyses_split(cree_analyzer, surface_forms, result):
    assert cree_analyzer.feed_in_bulk(surface_forms, concat=False) == result


@pytest.mark.parametrize(
    "surface_forms,result",
    [
        (
            ("niskak", "nîskâw", "nipâw", "abcdefg"),
            {
                "niskak": {"niska+N+A+Pl", "nîskâw+V+II+Cnj+Prs+3Sg"},
                "nîskâw": {"nîskâw+V+II+Ind+Prs+3Sg"},
                "nipâw": {"nipâw+V+AI+Ind+Prs+3Sg"},
                "abcdefg": set(),
            },
        )
    ],
)
def test_multiple_analyses_fast(cree_analyzer, surface_forms, result):
    assert cree_analyzer.feed_in_bulk_fast(surface_forms) == result
    assert cree_analyzer.feed_in_bulk_fast(surface_forms, multi_process=2) == result


@pytest.mark.parametrize("surface_form,result", [("niska+N+A+Pl", (("niskak",),))])
def test_single_generation_single_deep_form(cree_generator, surface_form, result):
    assert cree_generator.feed(surface_form) == result


@pytest.mark.parametrize(
    "surface_form,result", [("niska+N+A+Pl", (("n", "i", "s", "k", "a", "k"),))]
)
def test_single_generation_single_deep_form_split(cree_generator, surface_form, result):
    assert cree_generator.feed(surface_form, concat=False) == result


@pytest.mark.parametrize(
    "surface_form,result",
    [("nipâw+V+AI+Ind+Prs+12Pl", (("kinipânaw",), ("kinipânânaw",)))],
)
def test_single_generation_multiple_deep_form(cree_generator, surface_form, result):
    assert cree_generator.feed(surface_form) == result


@pytest.mark.parametrize(
    "surface_form,result",
    [
        (
            "nipâw+V+AI+Ind+Prs+12Pl",
            (
                ("k", "i", "n", "i", "p", "â", "n", "a", "w"),
                ("k", "i", "n", "i", "p", "â", "n", "â", "n", "a", "w"),
            ),
        )
    ],
)
def test_single_generation_multiple_deep_form_split(
    cree_generator, surface_form, result
):
    assert cree_generator.feed(surface_form, concat=False) == result


@pytest.mark.parametrize("surface_form,result", [("abcdefg", ()), ("", ())])
def test_single_generation_outside_of_alphabet(cree_generator, surface_form, result):
    # fixme: 'I+lov` hangs, 'i+lov' doesn't
    assert cree_generator.feed(surface_form) == result
    assert cree_generator.feed(surface_form, concat=False) == result


@pytest.mark.parametrize(
    "surface_forms,result",
    [
        (
            ["niska+N+A+Pl", "nipâw+V+AI+Ind+Prs+12Pl", "abcdefg", ""],
            {
                "niska+N+A+Pl": {("niskak",)},
                "nipâw+V+AI+Ind+Prs+12Pl": {("kinipânaw",), ("kinipânânaw",)},
                "abcdefg": set(),
                "": set(),
            },
        )
    ],
)
def test_multiple_generation(cree_generator, surface_forms, result):
    assert cree_generator.feed_in_bulk(surface_forms) == result


@pytest.mark.parametrize(
    "surface_forms,result",
    [
        (
            ["niska+N+A+Pl", "nipâw+V+AI+Ind+Prs+12Pl", "abcdefg", ""],
            {
                "niska+N+A+Pl": {("n", "i", "s", "k", "a", "k")},
                "nipâw+V+AI+Ind+Prs+12Pl": {
                    ("k", "i", "n", "i", "p", "â", "n", "a", "w"),
                    ("k", "i", "n", "i", "p", "â", "n", "â", "n", "a", "w"),
                },
                "abcdefg": set(),
                "": set(),
            },
        )
    ],
)
def test_multiple_generation_split(cree_generator, surface_forms, result):
    assert cree_generator.feed_in_bulk(surface_forms, concat=False) == result


@pytest.mark.parametrize(
    "surface_forms,result",
    [
        (
            ["niska+N+A+Pl", "nipâw+V+AI+Ind+Prs+12Pl", "abcdefg", ""],
            {
                "niska+N+A+Pl": {"niskak"},
                "nipâw+V+AI+Ind+Prs+12Pl": {"kinipânaw", "kinipânânaw"},
                "abcdefg": set(),
                "": set(),
            },
        )
    ],
)
def test_multiple_generation_fast(cree_generator, surface_forms, result):
    assert cree_generator.feed_in_bulk_fast(surface_forms) == result

import os
import subprocess
import sys
import unittest
from os import path

import pytest

from hfstol import main


# analysis

@pytest.mark.parametrize('surface_form,result', [
    (
            'nîskâw', (('nîskâw', '+V', '+II', '+Ind', '+Prs', '+3Sg'),)
    ),
    (
            'nipâw', (('nipâw', '+V', '+AI', '+Ind', '+Prs', '+3Sg'),)
    )
])
def test_single_analysis_single_deep_form(cree_analyzer, surface_form, result):
    assert cree_analyzer.feed(surface_form) == result


@pytest.mark.parametrize('surface_form,result', [
    (
            'nîskâw', (('n', 'î', 's', 'k', 'â', 'w', '+V', '+II', '+Ind', '+Prs', '+3Sg'),)
    ),
    (
            'nipâw', (('n', 'i', 'p', 'â', 'w', '+V', '+AI', '+Ind', '+Prs', '+3Sg'),)
    )
])
def test_single_analysis_single_deep_form_split(cree_analyzer, surface_form, result):
    assert cree_analyzer.feed(surface_form, concat=False) == result


@pytest.mark.parametrize('surface_form,result', [
    (
            'niska', (('niska', '+N', '+A', '+Sg'), ('niska', '+N', '+A', '+Obv'))
    ),
])
def test_singled_analysis_multiple_deep_form(cree_analyzer, surface_form, result):
    assert cree_analyzer.feed(surface_form) == result


@pytest.mark.parametrize('surface_form,result', [
    (
            'niska', (('n', 'i', 's', 'k', 'a', '+N', '+A', '+Sg'), ('n', 'i', 's', 'k', 'a', '+N', '+A', '+Obv'))
    ),
])
def test_singled_analysis_multiple_deep_form_split(cree_analyzer, surface_form, result):
    assert cree_analyzer.feed(surface_form, concat=False) == result


@pytest.mark.parametrize('surface_form,result', [
    (
            'abcdefg', ()
    ),
    (
            '', ()
    ),
])
def test_singled_analysis_out_side_alphabet(cree_analyzer, surface_form, result):
    assert cree_analyzer.feed(surface_form) == result
    assert cree_analyzer.feed(surface_form, concat=False) == result


@pytest.mark.parametrize('surface_form,result', [
    (
            ('niskak', 'nîskâw', 'nipâw', 'abcdefg'),
            {'niskak': {('niska', '+N', '+A', '+Pl'), ('nîskâw', '+V', '+II', '+Cnj', '+Prs', '+3Sg')},
             'nîskâw': {('nîskâw', '+V', '+II', '+Ind', '+Prs', '+3Sg')},
             'nipâw': {('nipâw', '+V', '+AI', '+Ind', '+Prs', '+3Sg')},
             'abcdefg': set()}
    )
])
def test_multiple_analyses(cree_analyzer, surface_form, result):
    assert cree_analyzer.feed_in_bulk(surface_form) == result


@pytest.mark.parametrize('surface_form,result', [
    (
            ('niskak', 'nîskâw', 'nipâw', 'abcdefg'),
            {'niskak': {('n', 'i', 's', 'k', 'a', '+N', '+A', '+Pl'),
                        ('n', 'î', 's', 'k', 'â', 'w', '+V', '+II', '+Cnj', '+Prs', '+3Sg')},
             'nîskâw': {('n', 'î', 's', 'k', 'â', 'w', '+V', '+II', '+Ind', '+Prs', '+3Sg')},
             'nipâw': {('n', 'i', 'p', 'â', 'w', '+V', '+AI', '+Ind', '+Prs', '+3Sg')},
             'abcdefg': set()}
    )
])
def test_multiple_analyses_split(cree_analyzer, surface_form, result):
    assert cree_analyzer.feed_in_bulk(surface_form, concat=False) == result


@pytest.mark.parametrize('surface_form,result', [
    (
            ('niskak', 'nîskâw', 'nipâw', 'abcdefg'),
            {'niskak': {'niska+N+A+Pl', 'nîskâw+V+II+Cnj+Prs+3Sg'}, 'nîskâw': {'nîskâw+V+II+Ind+Prs+3Sg'},
             'nipâw': {'nipâw+V+AI+Ind+Prs+3Sg'}, 'abcdefg': set()}
    )
])
def test_multiple_analyses_fast(cree_analyzer, surface_form, result):
    assert cree_analyzer.feed_in_bulk_fast(surface_form) == result

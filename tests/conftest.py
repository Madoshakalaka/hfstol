#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


from pathlib import Path
import pytest  # type: ignore


from hfstol import HFSTOL


@pytest.fixture
def cree_analyzer(shared_datadir: Path) -> HFSTOL:
    """
    Return the FST that deals with the cree language
    """
    return HFSTOL.from_file(shared_datadir / 'crk-descriptive-analyzer.hfstol')


@pytest.fixture
def cree_generator(shared_datadir: Path) -> HFSTOL:
    """
    Return the FST that deals with the cree language
    """
    return HFSTOL.from_file(shared_datadir / 'crk-normative-generator.hfstol')
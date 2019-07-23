#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


from pathlib import Path
import pytest  # type: ignore

from fst_lookup import FST

from hfstol import HFSTOL


@pytest.fixture
def cree_hfstol_analyzer(shared_datadir: Path) -> FST:
    """
    Return the FST that deals with the cree language
    """
    return HFSTOL.from_file(shared_datadir / 'crk-descriptive-analyzer.hfstol')
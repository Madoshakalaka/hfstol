#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from pathlib import Path

import psutil  # type: ignore
import pytest  # type: ignore

from hfstol import HFSTOL


def test_process_decreases_after_del(shared_datadir: Path):
    """
    Check that any processes started by HFSTOL are

    This test is not valid when using multi-threading!
    """
    processes_before = count_child_processes()
    hfst = HFSTOL.from_file(shared_datadir / "crk-descriptive-analyzer.hfstol")
    # By calling analyze, we are forcing a new hfstol process to start!
    hfst.feed_in_bulk_fast(["êkwa"])
    processes_during = count_child_processes()
    assert processes_during > processes_before, "expected at least one more process than before"

    # There should be no more references to the hfst... hopefully.
    del hfst
    # By removing this reference, hfst SHOULD have terminated all of its
    # processes; we should be back where we started.
    processes_after = count_child_processes()
    assert processes_after == processes_before, "expected new processes to be terminated"


def count_child_processes() -> int:
    return len(psutil.Process().children())

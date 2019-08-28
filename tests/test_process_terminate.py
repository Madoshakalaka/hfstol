#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import gc
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
    """
    Counts all "active" child processes.
    """
    # Count all children, as long as they're not zombies.
    # What are zombie processes? They're any process that has terminated,
    # yet, they have no been wait()'d by the parent process. Before the parent
    # calls wait() on a child process, its return status and other metadata
    # still have to be stored by the kernel so that the kernel can return it
    # upon a call to wait(); however, the kernel marks such a process as a
    # "zombie", because it is effectively dead, but waiting to be released by
    # its parent :/
    children = [child for child in  psutil.Process().children()
                if child.status() != psutil.STATUS_ZOMBIE]
    print(children)
    return len(children)

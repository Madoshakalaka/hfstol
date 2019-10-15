# noinspection Mypy
import pytest


# noinspection PyStatementEffect,DuplicatedCode
def test_consecutive_analyses_fast(cree_analyzer):
    cree_analyzer.feed_in_bulk_fast(["a"])["a"]
    cree_analyzer.feed_in_bulk_fast(["ac"])["ac"]
    cree_analyzer.feed_in_bulk_fast(["acâ"])["acâ"]
    cree_analyzer.feed_in_bulk_fast(["acâh"])["acâh"]
    cree_analyzer.feed_in_bulk_fast(["acâhk"])["acâhk"]
    cree_analyzer.feed_in_bulk_fast(["acâhko"])["acâhko"]
    cree_analyzer.feed_in_bulk_fast(["ac"])["ac"]
    cree_analyzer.feed_in_bulk_fast(["acâ"])["acâ"]
    cree_analyzer.feed_in_bulk_fast(["acâh"])["acâh"]
    cree_analyzer.feed_in_bulk_fast(["acâhk"])["acâhk"]
    cree_analyzer.feed_in_bulk_fast(["acâhko"])["acâhko"]
    cree_analyzer.feed_in_bulk_fast(["acâhkos"])["acâhkos"]
    cree_analyzer.feed_in_bulk_fast(["a"])["a"]
    cree_analyzer.feed_in_bulk_fast(["ac"])["ac"]
    cree_analyzer.feed_in_bulk_fast(["acâ"])["acâ"]
    cree_analyzer.feed_in_bulk_fast(["acâh"])["acâh"]
    cree_analyzer.feed_in_bulk_fast(["acâhk"])["acâhk"]
    cree_analyzer.feed_in_bulk_fast(["misc"])["misc"]
    cree_analyzer.feed_in_bulk_fast(["ac"])["ac"]
    cree_analyzer.feed_in_bulk_fast(["acâ"])["acâ"]
    cree_analyzer.feed_in_bulk_fast(["acâh"])["acâh"]
    cree_analyzer.feed_in_bulk_fast(["acâhk"])["acâhk"]
    cree_analyzer.feed_in_bulk_fast(["acâhko"])["acâhko"]
    cree_analyzer.feed_in_bulk_fast(["acâhkos"])["acâhkos"]

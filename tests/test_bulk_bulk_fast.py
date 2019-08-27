import pytest


@pytest.mark.parametrize(
    "surface_forms,result",
    [
        (
            ("niskak", "nîskâw", "nipâw", "abcdefg") * 3000,
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
    assert cree_analyzer.feed_in_bulk_fast(surface_forms, multi_process=1) == result

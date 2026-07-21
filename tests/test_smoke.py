"""Smoke test: proves the packaging/test harness works end to end.

Data-free — checks only pure functions and package metadata, so it runs anywhere (no parquet
under data/ required). Real unit tests come in a later step.
"""

import pandas as pd

import credit_policy
from credit_policy import woe


def test_package_imports_and_shortlist_frozen():
    """The package is importable and the frozen shortlist is intact."""
    assert credit_policy.VAR_SELECTION == [
        "classe_social",
        "Capacidade Financeira",
        "score_klavi_2",
        "status_empregaticio",
    ]


def test_psi_zero_for_identical_distributions():
    """PSI of a binned count vector against itself is 0 (a known invariant)."""
    counts = pd.Series({"bin_a": 100, "bin_b": 50, "bin_c": 25})
    assert woe.psi(counts, counts) == 0.0

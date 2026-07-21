"""Unit tests for credit_policy.binning.apply_spec.

Fixture-based (no data/ parquet). Each test pairs a value oracle (exact expected bin per row)
with independent invariants (bin order, partition, dtype). Sentinel bin labels come from
binning.MISSING / binning.OUTROS rather than being hardcoded.
"""

import numpy as np
import pandas as pd

from credit_policy import binning


def test_apply_spec_numeric():
    spec = {"type": "numeric", "cuts": [500, 600]}
    s = pd.Series([400, 500, 550, 600, 700, np.nan])

    out = binning.apply_spec(s, spec)

    # --- value oracle: right=True -> 500 lands in bin 1, 600 in bin 2; NaN -> (missing).
    # Asserting these strings also pins the _numeric_labels format.
    assert out.tolist() == [
        "1: ≤500", "1: ≤500", "2: 500–600", "2: 500–600", "3: >600", binning.MISSING,
    ]

    # --- invariants ---
    assert out.cat.categories.tolist() == [
        "1: ≤500", "2: 500–600", "3: >600", binning.MISSING,
    ]                                          # order stable; (missing) appended last
    assert out.cat.ordered is True
    assert out.notna().all()                   # every row got a bin
    assert out.value_counts().sum() == len(s)  # bins partition the sample


def test_apply_spec_categorical():
    spec = {"type": "categorical", "groups": {"B_C": ["B", "C"], "D": ["D"]}}
    s = pd.Series(["B", "C", "D", "Z", np.nan])   # Z unlisted, last is missing

    out = binning.apply_spec(s, spec)

    # --- value oracle: group mapping + unlisted->(outros) + NaN->(missing) ---
    assert out.tolist() == ["B_C", "B_C", "D", binning.OUTROS, binning.MISSING]

    # --- invariants ---
    assert out.cat.categories.tolist() == [
        "B_C", "D", binning.OUTROS, binning.MISSING,
    ]                                          # group order kept; (outros) then (missing) last
    assert out.cat.ordered is True
    assert out.index.equals(s.index)           # function rebuilds a Series on the input index


def test_apply_spec_categorical_no_outros():
    # Every value is listed and nothing is NaN -> (outros) must not be appended,
    # but (missing) still is (guards the conditional append in binning.py:121).
    spec = {"type": "categorical", "groups": {"B_C": ["B", "C"], "D": ["D"]}}
    s = pd.Series(["B", "C", "D"])

    out = binning.apply_spec(s, spec)

    assert out.tolist() == ["B_C", "B_C", "D"]
    assert binning.OUTROS not in out.cat.categories
    assert out.cat.categories.tolist() == ["B_C", "D", binning.MISSING]

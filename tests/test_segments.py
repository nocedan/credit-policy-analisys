"""Unit tests for credit_policy.segments.apply_segment.

Fixture-based (no data/ parquet). The binned frame is built by hand as ordered categoricals
(what binning.apply_spec would produce). Each test pairs a value oracle (exact cell per row)
with invariants (product order, partition, dtype). Sentinels come from binning.MISSING /
binning.OUTROS and the separator from segments.SEP rather than being hardcoded.
"""

import pandas as pd

from credit_policy import binning, segments


def _binned(values, categories):
    return pd.Series(pd.Categorical(values, categories=categories, ordered=True))


def _frame():
    M = binning.MISSING
    return pd.DataFrame({
        "classe_social": _binned(
            ["A", "B", "A", M, M], categories=["A", "B", M],
        ),
        "status": _binned(
            ["Formal", "Autônomo", M, "Formal", M], categories=["Formal", "Autônomo", M],
        ),
    })


def test_apply_segment_labels_and_missing():
    binned = _frame()
    out = segments.apply_segment(binned, {"dims": ["classe_social", "status"]})

    M = binning.MISSING
    sep = segments.SEP
    # --- value oracle: <bin> · <bin>; missing in ANY dim -> (missing) ---
    assert out.tolist() == [
        f"A{sep}Formal", f"B{sep}Autônomo", M, M, M,
    ]

    # --- invariants ---
    assert out.cat.categories.tolist() == [
        f"A{sep}Formal", f"A{sep}Autônomo", f"B{sep}Formal", f"B{sep}Autônomo", M,
    ]                                          # full product order, (missing) last
    assert out.cat.ordered is True
    assert binning.OUTROS not in out.cat.categories   # every observed cell is in the product
    assert out.value_counts().sum() == len(binned)    # cells partition the sample


def test_apply_segment_merged_groups():
    binned = _frame()
    sep = segments.SEP
    seg_spec = {
        "dims": ["classe_social", "status"],
        "groups": {f"A/B{sep}Formal": [f"A{sep}Formal", f"B{sep}Formal"]},
    }
    out = segments.apply_segment(binned, seg_spec)

    M = binning.MISSING
    # --- value oracle: A·Formal and B·Formal collapse into the merged cell ---
    assert out.tolist() == [
        f"A/B{sep}Formal", f"B{sep}Autônomo", M, M, M,
    ]

    # --- invariant: merge sits at its first member's product position; B·Formal is gone ---
    assert out.cat.categories.tolist() == [
        f"A/B{sep}Formal", f"A{sep}Autônomo", f"B{sep}Autônomo", M,
    ]
    assert out.cat.ordered is True

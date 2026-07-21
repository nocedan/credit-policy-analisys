"""Unit tests for credit_policy.woe.

Fixture-based (no data/ parquet). "bad" = OVER30M2 == 1; WoE convention: positive = safer.
"""

import numpy as np
import pandas as pd
from pytest import approx

from credit_policy import woe


def _binned(values, categories):
    return pd.Series(pd.Categorical(values, categories=categories, ordered=True))


def test_woe_table():
    # high: 3 bad / 1 good, low: 1 bad / 5 good, mid: deliberately empty.
    # totals: G (goods) = 6, B (bads) = 4.
    binned = _binned(["high"] * 4 + ["low"] * 6, categories=["high", "mid", "low"])
    y = pd.Series([1, 1, 1, 0] + [1, 0, 0, 0, 0, 0])

    t = woe.woe_table(binned, y)

    # --- structure / bookkeeping ---
    assert list(t.index) == ["high", "mid", "low"]        # order kept, empty mid retained
    assert t["n"].tolist() == [4, 0, 6]
    assert t["bads"].tolist() == [3, 0, 1]
    assert (t["goods"] == t["n"] - t["bads"]).all()
    assert t.loc["high", "bad_rate"] == approx(3 / 4)
    assert t.loc["low", "bad_rate"] == approx(1 / 6)
    assert t["n"].sum() == len(binned)                    # bins partition the sample

    # --- value oracle: recompute the smoothed stats from the counts ---
    G, B = 6, 4
    for b in ["high", "low"]:
        goods, bads = t.loc[b, "goods"], t.loc[b, "bads"]
        pg = (goods + 0.5) / (G + 0.5)
        pb = (bads + 0.5) / (B + 0.5)
        assert t.loc[b, "pct_goods"] == approx(pg)
        assert t.loc[b, "pct_bads"] == approx(pb)
        assert t.loc[b, "woe"] == approx(np.log(pg / pb))
        assert t.loc[b, "iv_contrib"] == approx((pg - pb) * np.log(pg / pb))

    # --- independent checks the recompute can't satisfy by coincidence ---
    # IV contribution is >= 0 for every occupied bin (invariant of (pg - pb) * ln(pg/pb)).
    assert (t.loc[t["n"] > 0, "iv_contrib"] >= -1e-12).all()
    # sign convention: safer bin (more goods) positive, riskier bin negative.
    assert t.loc["low", "woe"] > 0 > t.loc["high", "woe"]
    # the empty mid bin still gets a finite WoE -> the +0.5 smoothing is live (else 0/0).
    assert t.loc["mid", "n"] == 0
    assert np.isfinite(t.loc["mid", "woe"])


def test_psi():
    e = pd.Series({"a": 60, "b": 40})
    a_small = pd.Series({"a": 50, "b": 50})
    a_big = pd.Series({"a": 20, "b": 80})
    a_disjoint = pd.Series({"a": 60, "c": 40})   # bin b only in expected, c only in actual

    # --- value oracle: recompute PSI = Σ (a% - e%)·ln(a%/e%) from the formula ---
    idx = e.index.union(a_small.index)
    ev = e.reindex(idx).fillna(0) + 0.5
    ev /= ev.sum()
    av = a_small.reindex(idx).fillna(0) + 0.5
    av /= av.sum()
    assert woe.psi(e, a_small) == approx(float(((av - ev) * np.log(av / ev)).sum()))

    # --- independent invariants the recompute can't satisfy by coincidence ---
    assert woe.psi(e, e) == 0.0                                 # identical -> 0
    assert woe.psi(e, a_small) >= 0                             # non-negative
    assert woe.psi(e, a_small) < woe.psi(e, a_big)             # grows with the shift
    assert woe.psi(e, a_small) == approx(woe.psi(a_small, e))   # symmetric
    # disjoint bins: +0.5 smoothing + fillna(0) keep it finite (no ln(0) / div-0).
    d = woe.psi(e, a_disjoint)
    assert np.isfinite(d) and d > 0

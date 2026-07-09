"""WoE / IV machinery for univariate signal analysis.

"bad" = ``OVER30M2 == 1``, "good" = ``OVER30M2 == 0``, always on the labeled ``Contratado``
sample. Convention: ``WoE = ln(%goods / %bads)`` — **positive = safer** than average, negative
= riskier. See ``references/information-value.md``. Used by notebooks 2.0 (binning workbench)
and 2.1 (univariate signal); binning lives in :mod:`credit_policy.binning`.
"""

import numpy as np
import pandas as pd

# IV verdict thresholds (upper bound, label). > last bound => "suspicious (check leakage)".
IV_THRESHOLDS = [(0.02, "useless"), (0.1, "weak"), (0.3, "medium"), (0.5, "strong")]


def woe_table(binned, y):
    """Per-bin counts, bad rate, WoE (0.5-smoothed) and IV contribution. Keeps empty bins."""
    t = pd.DataFrame({"bin": binned.values, "bad": np.asarray(y, dtype=int)})
    g = t.groupby("bin", observed=False)["bad"].agg(n="size", bads="sum")
    g["goods"] = g["n"] - g["bads"]
    G, B = g["goods"].sum(), g["bads"].sum()
    g["bad_rate"] = g["bads"] / g["n"]
    g["pct_goods"] = (g["goods"] + 0.5) / (G + 0.5)
    g["pct_bads"] = (g["bads"] + 0.5) / (B + 0.5)
    g["woe"] = np.log(g["pct_goods"] / g["pct_bads"])
    g["iv_contrib"] = (g["pct_goods"] - g["pct_bads"]) * g["woe"]
    assert g["n"].sum() == len(binned), "bins do not partition the sample"
    assert (g.loc[g["n"] > 0, "iv_contrib"] >= -1e-12).all(), "negative IV contribution"
    return g


def iv_of(g):
    """IV over occupied bins only (empty bins would add smoothing noise)."""
    return g.loc[g["n"] > 0, "iv_contrib"].sum()


def woe_over_time(binned, y, safra, min_n=10):
    """Within-safra WoE per bin (safras x bins); bins with n < min_n masked to NaN."""
    out = {}
    for sf in sorted(safra.unique()):
        m = (safra == sf).values
        g = woe_table(binned[m], y[m])
        out[sf] = g["woe"].where(g["n"] >= min_n)
    wt = pd.DataFrame(out).T
    wt.index = wt.index.astype(str)
    return wt


def iv_verdict(iv):
    """Map an IV value to its conventional verdict label."""
    for thr, name in IV_THRESHOLDS:
        if iv < thr:
            return name
    return "suspicious (check leakage)"


def woe_encode(binned, y):
    """Per-row WoE: map each observation to its bin's WoE (0.5-smoothed). Turns any binned
    variable into a numeric log-odds column — used for redundancy correlation (2.2) and the
    scorecard (Fase 3)."""
    g = woe_table(binned, y)
    return binned.astype(object).map(g["woe"]).astype(float)


def woe_frame(binned, y):
    """WoE-encode a dict of binned Series into a DataFrame (one WoE column per variable)."""
    return pd.DataFrame({v: woe_encode(b, y) for v, b in binned.items()})


def psi(expected, actual, eps=0.5):
    """Population Stability Index between two binned count vectors, aligned on their bins:
    ``PSI = Σ (a% − e%)·ln(a%/e%)``. 0.5 smoothing avoids div/log of zero. Conventional bands:
    < 0.1 stable, 0.1–0.25 moderate shift, > 0.25 significant shift. Returns 0 for identical
    distributions."""
    idx = expected.index.union(actual.index)
    e = expected.reindex(idx).fillna(0) + eps
    a = actual.reindex(idx).fillna(0) + eps
    e, a = e / e.sum(), a / a.sum()
    return float(((a - e) * np.log(a / e)).sum())

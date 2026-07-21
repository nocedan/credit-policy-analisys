"""Unit tests for credit_policy.policy (excluding save_policy).

Fixture-based (no data/ parquet). `approve` is checked against a hand-built df spanning every
rule variant; `policy_at` / `frontier` against a hand-built cutoff menu with a value oracle for
kept counts plus the sweep invariants (floor always kept, cutoff monotone in τ, edge τ).
"""

import numpy as np
import pandas as pd

from credit_policy import policy


# --------------------------------------------------------------------------- approve

def test_approve_rule_variants():
    # One row per case, across four segments exercising every rule branch.
    df = pd.DataFrame({
        "segmento": [
            "gate", "gate", "gate", "gate",           # score_min=500, scoreless=deny
            "all_scored", "all_scored",               # score_min=None, scoreless=approve
            "deny_scored", "deny_scored",             # score_min=inf, scoreless=approve
            "keep", "keep", "keep",                   # mode=keep_current
        ],
        "score_klavi_2": [
            600, 500, 400, np.nan,
            100, np.nan,
            900, np.nan,
            np.nan, 999, 999,
        ],
        "STATUS": [
            "Negado", "Negado", "Negado", "Negado",
            "Negado", "Negado",
            "Negado", "Negado",
            "Contratado", "Aprovado", "Negado",
        ],
    })
    pol = {"segments": {
        "gate": {"score_min": 500, "scoreless": "deny"},
        "all_scored": {"score_min": None, "scoreless": "approve"},
        "deny_scored": {"score_min": policy.INF, "scoreless": "approve"},
        "keep": {"mode": "keep_current"},
    }}

    ok = policy.approve(df, pol)

    # --- value oracle, row by row ---
    expected = [
        True,    # gate 600 >= 500
        True,    # gate 500 >= 500 (boundary is inclusive)
        False,   # gate 400 < 500
        False,   # gate scoreless -> deny
        True,    # all_scored: score_min None approves any scored row
        True,    # all_scored scoreless -> approve
        False,   # deny_scored: score_min inf denies every scored row
        True,    # deny_scored scoreless -> approve
        True,    # keep_current: STATUS Contratado (score ignored)
        True,    # keep_current: STATUS Aprovado (score ignored)
        False,   # keep_current: STATUS Negado
    ]
    assert ok.tolist() == expected

    # --- invariants ---
    assert ok.dtype == bool
    assert ok.index.equals(df.index)


# --------------------------------------------------------------------------- policy_at / frontier

def _menus():
    # One named segment "A": one row per score, sorted descending, with cumulative-from-top
    # n / bads / rate. rate rises as lower scores are admitted.
    return {"A": pd.DataFrame({
        "score": [800, 700, 600, 500],
        "n":     [10,  20,  30,  40],
        "bads":  [0,   1,   3,   8],
        "rate":  [0.0, 0.05, 0.10, 0.20],
    })}


def test_policy_at_cutoffs_and_kept_counts():
    menus = _menus()
    blocks = {"blk": (10, 2)}          # scoreless block, rate 0.2
    floor = (5, 1)                     # (missing) floor, always kept

    # τ=0.0 : only the rate-0 top row qualifies; block (0.2) denied.
    kept_n, kept_b, cuts, keeps = policy.policy_at(0.0, menus, blocks, floor)
    assert cuts == {"A": 800}
    assert keeps == {"blk": False}
    assert (kept_n, kept_b) == (5 + 10, 1 + 0)

    # τ=0.1 : admits down to score 600; block still denied.
    kept_n, kept_b, cuts, keeps = policy.policy_at(0.1, menus, blocks, floor)
    assert cuts == {"A": 600}
    assert keeps == {"blk": False}
    assert (kept_n, kept_b) == (5 + 30, 1 + 3)

    # τ=0.2 (max) : whole menu admitted; block (0.2 <= 0.2) now approved.
    kept_n, kept_b, cuts, keeps = policy.policy_at(0.2, menus, blocks, floor)
    assert cuts == {"A": 500}
    assert keeps == {"blk": True}
    assert (kept_n, kept_b) == (5 + 40 + 10, 1 + 8 + 2)

    # edge τ below the safest rate : no scored row qualifies -> deny-all cutoff = inf,
    # only the floor is kept.
    kept_n, kept_b, cuts, keeps = policy.policy_at(-1.0, menus, blocks, floor)
    assert cuts == {"A": policy.INF}
    assert keeps == {"blk": False}
    assert (kept_n, kept_b) == floor


def test_policy_at_floor_and_monotonicity():
    menus, blocks, floor = _menus(), {"blk": (10, 2)}, (5, 1)
    taus = [-1.0, 0.0, 0.05, 0.10, 0.20]

    results = [policy.policy_at(t, menus, blocks, floor) for t in taus]
    kept_ns = [r[0] for r in results]
    cutoffs = [r[2]["A"] for r in results]

    # floor always kept: every kept count includes the floor's n.
    assert all(n >= floor[0] for n in kept_ns)
    # more tolerance -> weakly more admitted, weakly lower cutoff.
    assert kept_ns == sorted(kept_ns)
    assert cutoffs == sorted(cutoffs, reverse=True)   # inf, 800, 700, 600, 500


def test_frontier_sweep():
    menus, blocks, floor = _menus(), {"blk": (10, 2)}, (5, 1)
    taus = [0.0, 0.1, 0.2]

    df = policy.frontier(taus, menus, blocks, floor, n_total=100)

    assert list(df.columns) == ["tau", "n", "bads", "kept", "default"]
    assert len(df) == len(taus)                       # one row per τ
    assert df["tau"].tolist() == taus
    assert df["n"].tolist() == [15, 35, 55]           # matches policy_at kept_n above
    assert df["bads"].tolist() == [1, 4, 11]
    assert df["kept"].tolist() == [0.15, 0.35, 0.55]  # n / n_total
    assert df["default"].tolist() == [1 / 15, 4 / 35, 11 / 55]
    # sweep is monotone: kept share non-decreasing in τ.
    assert df["n"].is_monotonic_increasing

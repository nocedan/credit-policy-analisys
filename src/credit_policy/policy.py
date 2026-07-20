"""Policy spec: per-segment score cutoffs + explicit scoreless paths.

Hand-editable YAML (``references/policy_v1.yaml``), written by notebook 3.2 (operating point)
and consumed downstream. Schema — one rule per segment of the persisted segmentation:

    segments:
      <segment>:
        score_min: <float|null>     # null = no score gate (approve all scored); .inf = deny scored
        scoreless: approve|deny     # path for rows with no score in this segment
      <segment>:
        mode: keep_current           # no score/demographics to condition on (the `(missing)`
                                      # segment): defer to whatever the client already decided —
                                      # approve iff STATUS in {Aprovado, Contratado}. Overrides
                                      # score_min/scoreless for that segment.

``approve`` turns a policy into the boolean approval mask — the single place the rules execute.

The **operating point** behind such a spec comes from a risk-tolerance sweep: :func:`policy_at`
resolves one τ into a cutoff per named segment (plus the ``(missing)`` floor that rides along
unchanged), and :func:`frontier` runs that over a τ grid to build the approval × default
trade-off curve (notebook 3.2). Both are pure — they take the pre-built per-segment cutoff
``menus`` and scoreless ``blocks``, never a DataFrame or globals.
"""

from pathlib import Path

import pandas as pd
import yaml

INF = float("inf")

_HEADER = """\
# Política v1 — ponto de operação escolhido no notebook 3.2 (fonte única de verdade).
# Por segmento: score_min (null = sem gate; .inf = nega os com-score) e o caminho dos sem-score.
# Cutoffs medidos no book Contratado; arredondar/recalibrar antes de produção.
"""


def save_policy(policy, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.safe_dump(policy, sort_keys=False, allow_unicode=True)
    path.write_text(_HEADER + body, encoding="utf-8")


def policy_at(tau, menus, blocks, floor, named=None):
    """Resolve one risk tolerance ``tau`` into a policy over the named segments + fixed floor.

    Parameters
    ----------
    tau : float
        Risk tolerance — approve every admission unit whose measured default rate ≤ ``tau``.
    menus : dict[str, pandas.DataFrame]
        Per named segment, its nested cutoff menu: one row per distinct ``score`` (sorted
        descending) with cumulative-from-top ``n``, ``bads`` and ``rate`` columns.
    blocks : dict[str, tuple[int, int]]
        Per scoreless block, its ``(n, bads)`` counts.
    floor : tuple[int, int]
        The ``(missing)`` floor's ``(n, bads)`` — always kept, never swept by ``tau``.
    named : list[str], optional
        Named segments to sweep, in output order. Defaults to ``menus`` insertion order.

    Returns
    -------
    tuple
        ``(kept_n, kept_bads, cuts, keeps)`` — total kept counts (floor included), the
        ``{segment: score_min or inf}`` cutoff per named segment (``inf`` = deny all scored),
        and the ``{block: bool}`` approve/deny decision per scoreless block.
    """
    miss_n, miss_b = floor
    kept_n, kept_b = miss_n, miss_b                       # (missing) floor: always in
    cuts, keeps = {}, {}
    for s in (list(menus) if named is None else named):
        m = menus[s]
        ok = m[m["rate"] <= tau]
        cuts[s] = ok["score"].iloc[-1] if len(ok) else INF
        if len(ok):
            kept_n += int(ok["n"].iloc[-1])
            kept_b += int(ok["bads"].iloc[-1])
    for k, (n, b) in blocks.items():
        keeps[k] = b / n <= tau
        if keeps[k]:
            kept_n += n
            kept_b += b
    return kept_n, kept_b, cuts, keeps


def frontier(taus, menus, blocks, floor, n_total, named=None):
    """Sweep ``taus`` into the approval × default trade-off curve on the labeled book.

    One row per τ: ``tau``, kept count ``n`` and ``bads`` (floor included), the kept ``share``
    of the ``n_total``-row book, and the ``default`` rate of the kept book.
    """
    rows = [(t, *policy_at(t, menus, blocks, floor, named)[:2]) for t in taus]
    df = pd.DataFrame(rows, columns=["tau", "n", "bads"])
    df["kept"] = df["n"] / n_total
    df["default"] = df["bads"] / df["n"]
    return df


def approve(df, policy, seg_col="segmento", score_col="score_klavi_2", status_col="STATUS"):
    """Boolean approval mask for `df` under `policy`."""
    ok = pd.Series(False, index=df.index)
    score = df[score_col]
    for seg, rule in policy["segments"].items():
        m = df[seg_col] == seg
        if rule.get("mode") == "keep_current":
            ok |= m & df[status_col].isin(["Contratado", "Aprovado"])
            continue
        gate = score.notna() if rule["score_min"] is None else score >= rule["score_min"]
        ok |= m & score.notna() & gate
        if rule["scoreless"] == "approve":
            ok |= m & score.isna()
    return ok

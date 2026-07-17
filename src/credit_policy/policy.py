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
"""

from pathlib import Path

import pandas as pd
import yaml

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

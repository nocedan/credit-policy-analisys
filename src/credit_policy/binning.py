"""Bin-spec lifecycle: estimate -> persist -> load -> apply.

The bin spec is a hand-tunable YAML file (``references/bin_spec.yaml``) that is the single
source of truth for how every variable is binned into WoE bins across the analysis (notebooks
2.0, 2.1 and downstream). Schema (cut-point form, optimized for manual merging):

    <var>:
      type: numeric
      cuts: [400, 450, 500, 550, 600]   # interior cut points; N cuts -> N+1 bins
                                         # delete a value to MERGE two adjacent bins
    <var>:
      type: categorical
      groups:                            # order = plot order
        B_C: [B, C]                      # merge two categories = put them in one list
        D_E: [D, E]

``(missing)`` (NaN) and ``(outros)`` (categories not listed in any group) are implicit and
always appended as their own bins. The WoE/IV of a binned series is computed with
:mod:`credit_policy.woe`.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

MISSING = "(missing)"
OUTROS = "(outros)"

_HEADER = """\
# Binning das variáveis para WoE/IV — fonte única de verdade (notebooks 2.0, 2.1, e diante).
# Para FUNDIR dois bins adjacentes:
#   - numérica  : apague um valor da lista `cuts`  (N cuts -> N+1 bins)
#   - categórica: junte duas categorias numa mesma lista em `groups`
#                 (a ordem dos grupos define a ordem no gráfico)
# (missing) [NaN] e (outros) [categorias não listadas] são bins implícitos.
# Após editar, reexecute as células de load+plot do notebook 2.0 para revisar.
"""


# --------------------------------------------------------------------------- estimate

def _round_int_cuts(interior):
    """Round cut points to ints, keeping them strictly increasing (drop collapsed dups)."""
    cuts = []
    for c in interior:
        ci = int(round(float(c)))
        if not cuts or ci > cuts[-1]:
            cuts.append(ci)
    return cuts


def estimate_spec(lab, numeric_vars, categorical_vars, min_rows_per_bin=200,
                  max_bins=10, min_share=0.02):
    """Initial bin spec from the labeled sample: adaptive quantile cuts for numerics,
    one group per (non-rare) category for categoricals. Meant to be hand-tuned afterwards."""
    spec = {}
    for v in numeric_vars:
        s = lab[v].dropna()
        n_bins = int(np.clip(len(s) // min_rows_per_bin, 2, max_bins))
        _, edges = pd.qcut(s, q=n_bins, retbins=True, duplicates="drop")
        spec[v] = {"type": "numeric", "cuts": _round_int_cuts(edges[1:-1])}
    for v in categorical_vars:
        s = lab[v].astype("string")
        share = s.value_counts(normalize=True)               # excludes NaN, sorted desc
        kept = [c for c in share.index if share[c] >= min_share]
        spec[v] = {"type": "categorical", "groups": {c: [c] for c in kept}}
    return spec


# --------------------------------------------------------------------------- persist

def save_spec(spec, path):
    """Write the spec to YAML with an explanatory header; scalar lists rendered inline."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.safe_dump(spec, sort_keys=False, default_flow_style=None, allow_unicode=True)
    path.write_text(_HEADER + body, encoding="utf-8")


def load_spec(path):
    """Load the spec dict from YAML."""
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- apply

def _numeric_labels(cuts):
    """Human-readable, order-stable bin labels for edges [-inf, *cuts, inf]."""
    edges = [-np.inf, *cuts, np.inf]
    labels = []
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        if lo == -np.inf:
            labels.append(f"{i+1}: ≤{hi:,.0f}")
        elif hi == np.inf:
            labels.append(f"{i+1}: >{lo:,.0f}")
        else:
            labels.append(f"{i+1}: {lo:,.0f}–{hi:,.0f}")
    return edges, labels


def apply_spec(series, var_spec):
    """Bin a Series per its var spec into an ordered categorical with an explicit (missing)
    bin (and (outros) for categoricals). Bin order matches the spec, so WoE tables/plots are
    stable across re-runs."""
    if var_spec["type"] == "numeric":
        edges, labels = _numeric_labels(var_spec["cuts"])
        cut = pd.cut(series, bins=edges, labels=labels, right=True)
        return cut.cat.add_categories([MISSING]).fillna(MISSING)

    # categorical: map each category to its group; unlisted -> (outros); NaN -> (missing)
    groups = var_spec["groups"]
    mapping = {str(c): glabel for glabel, cats in groups.items() for c in cats}
    s = series.astype("string")
    out = s.map(mapping)
    out = out.where(~(s.notna() & out.isna()), OUTROS)   # listed-but-unmatched -> (outros)
    out = out.where(s.notna(), MISSING)                   # NaN -> (missing)
    order = list(groups.keys())
    if (out == OUTROS).any():
        order.append(OUTROS)
    order.append(MISSING)
    return pd.Series(pd.Categorical(out, categories=order, ordered=True), index=series.index)


def transform(df, spec):
    """Apply the full spec, returning a DataFrame of binned columns (one per spec variable)."""
    return pd.DataFrame({v: apply_spec(df[v], var_spec) for v, var_spec in spec.items()})

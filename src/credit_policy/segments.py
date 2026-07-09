"""Composite segmentations: cross binned variables into policy-segment columns.

Parallel to :mod:`credit_policy.binning`: the segment spec is a hand-authored YAML
(``references/segment_spec.yaml``, read with :func:`credit_policy.binning.load_spec`) and each
segmentation is just another ordered categorical — the WoE/IV/PSI machinery applies unchanged.
Schema (one entry per segmentation; extensible beyond ``segmento``):

    <segment>:
      dims: [classe_social, status_empregaticio]  # columns of the BINNED frame, in cell order
      groups:                                     # optional; same schema as bin_spec categoricals
        D/E · Autônomo/Formal: [D/E · Autônomo, D/E · Formal]   # one list = one merged cell;
                                                  # unlisted cells keep their own name; a merge
                                                  # sits at its first member's product position

Cells are labeled ``<bin> · <bin>``; a row that is ``(missing)`` in ANY dim lands in the
``(missing)`` cell — the policy gets one explicit no-data path, not a lattice of partial ones.
"""

from itertools import product

import pandas as pd

from .binning import MISSING, apply_spec

SEP = " · "


def _cells(binned, dims):
    """Cell universe in product order (each dim in its bin order, missing excluded)."""
    orders = [[str(c) for c in binned[d].cat.categories if c != MISSING] for d in dims]
    return [SEP.join(combo) for combo in product(*orders)]


def _full_groups(cells, groups):
    """Complete a partial merge mapping with identity groups, preserving product order."""
    member_of = {cell: g for g, cs in groups.items() for cell in cs}
    full = {}
    for cell in cells:
        g = member_of.get(cell, cell)
        full.setdefault(g, groups.get(g, [cell]))
    return full


def apply_segment(binned, seg_spec):
    """Cross binned dims into one ordered categorical (parallel to binning.apply_spec)."""
    parts = [binned[d].astype("string") for d in seg_spec["dims"]]
    parts = [p.where(p != MISSING) for p in parts]        # missing in any dim -> NaN cell
    raw = parts[0].str.cat(parts[1:], sep=SEP)
    groups = _full_groups(_cells(binned, seg_spec["dims"]), seg_spec.get("groups") or {})
    return apply_spec(raw, {"type": "categorical", "groups": groups})


def make_segments(binned, spec):
    """Build every segmentation in the spec from a binned frame (parallel to binning.transform)."""
    return pd.DataFrame({name: apply_segment(binned, s) for name, s in spec.items()})

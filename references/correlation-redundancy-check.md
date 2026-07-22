# |r| redundancy check between shortlisted variables

Where it runs: `notebooks/2.2-dn-shortlist-validation.ipynb` (cell "## 2. Redundancy — WoE
correlation")

## Method

Each shortlisted variable is already binned (`references/bin_spec.yaml`). Bins are converted to
numeric WoE (log-odds) columns, then correlated with plain Pearson `.corr()` — not Cramér's V/phi,
because the question is "do these two order risk the same way," not raw category association.

```python
binned = {v: binning.apply_spec(lab[v], spec[v]) for v in VAR_SELECTION}
W = woe.woe_frame(binned, y)   # one WoE column per variable
```

`woe.woe_frame` → `woe.woe_encode` → `woe.woe_table` (`src/credit_policy/woe.py`): each bin's WoE
is `ln(%goods / %bads)`, 0.5-smoothed; every row is mapped to its bin's WoE value.

## Naive vs. overlap-only

Missing values are their own explicit bin (`"(missing)"`), which itself has a WoE value. Two
variables missing on the same rows will correlate on that alone — so the naive number is inflated
by co-missingness, not real overlap:

```python
R_naive = W.corr()                                    # all rows, incl. co-missing "(missing)" bin

notmiss = pd.DataFrame({v: binned[v].astype(object).ne("(missing)") for v in VAR_SELECTION})
for a in VAR_SELECTION:
    for b in VAR_SELECTION:
        m = notmiss[a] & notmiss[b]                    # both observed
        R_over.loc[a, b] = W.loc[m, a].corr(W.loc[m, b])
```

`R_naive` = the 0.73 figure; `R_over` (restricted to rows where both variables are observed) = the
0.39 figure cited in `key_takeaways.md`.

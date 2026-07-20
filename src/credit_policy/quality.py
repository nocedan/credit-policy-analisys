"""Data-quality profiling — coverage/missingness/dtype summary for a raw or interim table.

One row per column: its dtype, missing count/share and cardinality. Used by notebook 1.0 to
audit the two raw files (performance vs application features) before any modeling, and to size
the selection-bias problem that drives the deck (§"The data & the catch").
"""

import pandas as pd


def quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """Per-column dtype, missing count, missing %, and unique-value count for `df`."""
    return pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "n_missing": df.isna().sum(),
        "pct_missing": (df.isna().mean() * 100).round(2),
        "n_unique": df.nunique(),
    })

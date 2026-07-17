"""Figure export helper — one place controlling how deck figures are written to disk.

Notebooks render charts inline; the business deck needs them as files under
`reports/figures/`. `save_fig` centralises the write settings (dpi, tight bbox, white
background) so every exported figure is slide-legible and consistent regardless of which
notebook produced it. See `reports/presentation-outline.md` for the figure-to-slide map.
"""

from pathlib import Path


def save_fig(fig, name, fig_dir, *, dpi=150):
    """Save a Matplotlib figure to `fig_dir / name` with slide-friendly defaults.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure handle (e.g. from `fig, ax = plt.subplots(...)`).
    name : str
        File name including extension, e.g. ``"fig_iv_ranking.png"``.
    fig_dir : str | pathlib.Path
        Target directory; created if missing.
    dpi : int
        Output resolution (default 150).

    Returns
    -------
    pathlib.Path
        The path written.
    """
    fig_dir = Path(fig_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)
    path = fig_dir / name
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    return path

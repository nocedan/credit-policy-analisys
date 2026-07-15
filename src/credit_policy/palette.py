"""Shared color palette and Matplotlib styling for the credit-policy deck.

Single source of truth for every figure in `reports/figures/` and the slide deck
(`reports/presentation.md`), so charts and slides read as one visual system.
Colors are grouped by the *job* they do:

- **Brand / ink** — navy structural colors for headings, surfaces, and text.
- **RISK ramp** — teal -> amber -> red for anything encoding default risk
  (tier risk, default rate, score gradient).
- **FUNNEL** — a blue ordinal ramp for the STATUS pipeline (Reprovado ->
  Aprovado -> Contratado), an identity scale, never reused for risk.
- **Grays** — neutral context (reference lines, baselines, background stock).

Palette validated with the dataviz skill's `validate_palette.js` against a white
chart surface (RISK ramp: all checks pass, amber relies on the bars' own value
labels for contrast; FUNNEL: passes the ordinal checks).

`apply_style()` replaces the bare `sns.set_theme(style="whitegrid")` in each
notebook setup cell, keeping seaborn's whitegrid base and overriding the grid,
axis, and ink colors to the navy system.
"""

from __future__ import annotations

from matplotlib.colors import LinearSegmentedColormap

# --- Brand / structural (navy) ---
BRAND = "#123a5e"       # headings, title bg, callout border, funnel dark end
BRAND_DARK = "#0d2740"  # title-gradient end
PANEL = "#eef2f7"       # callout / panel fill
INK = "#16202b"         # primary text
INK_2 = "#51606e"       # secondary text
MUTED = "#7b8794"       # axis labels, reference lines
GRID = "#e3e8ee"        # hairline gridlines
SURFACE = "#ffffff"     # chart surface

# --- Risk ramp (low -> high), validated ---
RISK_LOW = "#0d9488"    # teal
RISK_MID = "#d98a00"    # amber
RISK_HIGH = "#d03b3b"   # red
RISK = {"low": RISK_LOW, "mid": RISK_MID, "high": RISK_HIGH}

# --- Funnel / STATUS ordinal (blue), validated ---
FUNNEL = {"Reprovado": "#86b6ef", "Aprovado": "#4a89e0", "Contratado": BRAND}

# --- Neutral context grays ---
REF_LINE = MUTED        # dashed averages / thresholds
NEUTRAL = "#9aa5b1"     # a neutral baseline bar (e.g. "keep all")
STOCK_BG = GRID         # faint background stock bars


# --- IV quality bands (sequential blue; darker = stronger signal) ---
# Conventional IV scale (references/information-value.md): useless / weak / medium /
# strong / suspicious. Blue steps drawn from the dataviz skill's validated blue ramp;
# ordinal, light end clears 2:1 on white.
IV_BLUES = {
    "useless": "#86b6ef",     # < 0.02   (light)
    "weak": "#1c5cab",        # 0.02 - 0.1
    "medium": "#123a5e",      # 0.1 - 0.3
    "strong": "#0d2b4a",      # 0.3 - 0.5
    "suspicious": "#081a2f",  # > 0.5 (leakage suspicion)
}


def iv_color(iv) -> str:
    """Blue step for an IV value, graded by its conventional quality band."""
    if iv < 0.02:
        return IV_BLUES["useless"]
    if iv < 0.1:
        return IV_BLUES["weak"]
    if iv < 0.3:
        return IV_BLUES["medium"]
    if iv < 0.5:
        return IV_BLUES["strong"]
    return IV_BLUES["suspicious"]


def risk_cmap():
    """Continuous teal->amber->red colormap for risk graded by magnitude."""
    return LinearSegmentedColormap.from_list("risk", [RISK_LOW, RISK_MID, RISK_HIGH])


def risk_tier_color(label) -> str:
    """Map a segment label to its risk-tier color.

    A/B/C -> low (teal), D/E -> high (red), `(missing)` and anything else -> mid (amber).
    Mirrors the three measured tiers (A/B/C 6.5-7.8% < (missing) 11.5% < D/E 15.5-16.4%).
    """
    s = str(label)
    if s.startswith("A/B/C"):
        return RISK_LOW
    if s.startswith("D/E"):
        return RISK_HIGH
    return RISK_MID


def apply_style():
    """Apply the deck's navy/ink Matplotlib theme (call once in a notebook setup cell)."""
    import seaborn as sns  # local import: palette.py stays usable without seaborn

    sns.set_theme(style="whitegrid", rc={
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "grid.color": GRID,
        "font.family": "sans-serif",
    })

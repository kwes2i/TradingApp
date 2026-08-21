"""
Annotated chart rendering for the chart-quiz windows.

Everything drawn here is computed from the candles. Nothing is interpreted.

    swings      local extremes (fractal: extreme vs N bars either side)
    liquidity   swing levels price has NOT yet traded through, i.e. where
                resting stops sit. Drawn as horizontal rays.
    trendline   line through the last two swing lows (up) or highs (down)
    sweep       on the reveal only: where price took out a liquidity level
    outcome     on the reveal only: arrow from decision close to final close
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np

UP, DOWN = "#2E8B7A", "#C4544B"
INK, MUTED, FAINT = "#1c1c1c", "#8a8a8a", "#d8d8d8"
LIQ, SWEPT, PATH = "#B8860B", "#C4544B", "#3A6EA5"

STYLE = mpf.make_marketcolors(up=UP, down=DOWN, edge={"up": UP, "down": DOWN},
                              wick={"up": UP, "down": DOWN}, volume={"up": UP, "down": DOWN})
MPF = mpf.make_mpf_style(marketcolors=STYLE, facecolor="white", edgecolor=FAINT,
                         gridcolor=FAINT, gridstyle=":", y_on_right=True,
                         rc={"font.size": 9, "axes.labelcolor": MUTED,
                             "xtick.color": MUTED, "ytick.color": MUTED})


def find_swings(df, span=4):
    """Fractal swings: a high with no higher high within `span` bars either side."""
    h, l = df["High"].values, df["Low"].values
    highs, lows = [], []
    for i in range(span, len(df) - span):
        w = slice(i - span, i + span + 1)
        if h[i] == h[w].max() and (h[w] == h[i]).sum() == 1:
            highs.append(i)
        if l[i] == l[w].min() and (l[w] == l[i]).sum() == 1:
            lows.append(i)
    return highs, lows


def liquidity(df, highs, lows):
    """Swing levels price never traded back through — where stops rest."""
    h, l = df["High"].values, df["Low"].values
    above = [(i, h[i]) for i in highs if h[i + 1:].max(initial=-np.inf) < h[i]]
    below = [(i, l[i]) for i in lows if l[i + 1:].min(initial=np.inf) > l[i]]
    return above, below


def trendline(df, highs, lows):
    """Line through the last two swing lows if rising, last two highs if falling."""
    if len(lows) >= 2:
        a, b = lows[-2], lows[-1]
        if df["Low"].values[b] > df["Low"].values[a]:
            return a, df["Low"].values[a], b, df["Low"].values[b], UP
    if len(highs) >= 2:
        a, b = highs[-2], highs[-1]
        if df["High"].values[b] < df["High"].values[a]:
            return a, df["High"].values[a], b, df["High"].values[b], DOWN
    return None


def _base(df, show_dates, figsize=(11, 6.5)):
    kw = dict(type="candle", style=MPF, figsize=figsize, returnfig=True,
              volume=bool(df["Volume"].sum() > 0), tight_layout=True,
              xrotation=0, ylabel="", ylabel_lower="",
              scale_padding={"left": 0.4, "right": 1.0, "top": 0.6, "bottom": 0.5})
    if not show_dates:
        kw["datetime_format"] = " "
    fig, axes = mpf.plot(df, **kw)
    ax = axes[0]
    if not show_dates:
        for a in axes:
            a.set_yticklabels([])
            a.set_xticklabels([])
            a.tick_params(length=0)
    ax.grid(axis="y", alpha=0.25)
    return fig, ax


def _draw_context(ax, df, n):
    """Swings, liquidity rays and trendline — all visible at decision time."""
    highs, lows = find_swings(df.iloc[:n])
    above, below = liquidity(df.iloc[:n], highs, lows)

    for i, y in above + below:
        ax.hlines(y, i, n - 1, color=LIQ, lw=0.9, ls=(0, (5, 3)), alpha=0.85, zorder=1)
    if above or below:
        ax.hlines([], [], [], color=LIQ, lw=0.9, ls=(0, (5, 3)), label="resting liquidity")

    for i in highs:
        ax.plot(i, df["High"].values[i] * 1.004, marker="v", ms=4, color=MUTED, zorder=3)
    for i in lows:
        ax.plot(i, df["Low"].values[i] * 0.996, marker="^", ms=4, color=MUTED, zorder=3)

    t = trendline(df.iloc[:n], highs, lows)
    if t:
        x1, y1, x2, y2 = t[:4]
        if x2 > x1:
            slope = (y2 - y1) / (x2 - x1)
            ax.plot([x1, n - 1], [y1, y1 + slope * (n - 1 - x1)],
                    color=t[4], lw=1.3, alpha=0.75, zorder=2, label="trend")
    return above, below


def _legend(ax):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.01), ncol=3, fontsize=8,
              frameon=False, labelcolor=MUTED, handlelength=1.6, columnspacing=1.4)


def render_setup(df, n, path, title=""):
    fig, ax = _base(df.iloc[:n], show_dates=False)
    _draw_context(ax, df, n)
    ax.set_title(title, fontsize=11, color=INK, loc="left", pad=26)
    _legend(ax)
    fig.savefig(path, dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def render_reveal(df, n, path, title=""):
    fig, ax = _base(df, show_dates=True)
    above, below = _draw_context(ax, df, n)

    ax.axvspan(n - 0.5, len(df) - 0.5, color="#000000", alpha=0.04, zorder=0)
    ax.axvline(n - 0.5, color=MUTED, lw=1, ls="--", alpha=0.7)

    fut_h, fut_l = df["High"].values[n:], df["Low"].values[n:]
    for i, y in above:
        hit = np.argmax(fut_h > y) if (fut_h > y).any() else None
        if hit is not None:
            ax.plot(n + hit, y, marker="x", ms=9, mew=2, color=SWEPT, zorder=5)
    for i, y in below:
        hit = np.argmax(fut_l < y) if (fut_l < y).any() else None
        if hit is not None:
            ax.plot(n + hit, y, marker="x", ms=9, mew=2, color=SWEPT, zorder=5)
    ax.plot([], [], marker="x", ls="none", ms=8, mew=2, color=SWEPT, label="liquidity taken")

    start, end = df["Close"].values[n - 1], df["Close"].values[-1]
    ax.annotate("", xy=(len(df) - 1, end), xytext=(n - 1, start),
                arrowprops=dict(arrowstyle="-|>", lw=2, color=PATH, alpha=0.9,
                                connectionstyle="arc3,rad=0.12"), zorder=6)
    pct = (end / start - 1) * 100
    ax.annotate(f"{pct:+.1f}%", xy=(len(df) - 1, end), xytext=(6, 0),
                textcoords="offset points", va="center", fontsize=10,
                color=PATH, fontweight="medium")

    ax.set_title(title, fontsize=11, color=INK, loc="left", pad=26)
    _legend(ax)
    fig.savefig(path, dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def annotations(df, n):
    """The same features as structured data, for the breakdown text."""
    highs, lows = find_swings(df.iloc[:n])
    above, below = liquidity(df.iloc[:n], highs, lows)
    fut_h, fut_l = df["High"].values[n:], df["Low"].values[n:]

    taken = []
    for i, y in above:
        if (fut_h > y).any():
            taken.append({"side": "above", "level": round(float(y), 4),
                          "candles_later": int(np.argmax(fut_h > y)) + 1})
    for i, y in below:
        if (fut_l < y).any():
            taken.append({"side": "below", "level": round(float(y), 4),
                          "candles_later": int(np.argmax(fut_l < y)) + 1})

    t = trendline(df.iloc[:n], highs, lows)
    return {
        "swing_highs": len(highs), "swing_lows": len(lows),
        "resting_above": [round(float(y), 4) for _, y in above],
        "resting_below": [round(float(y), 4) for _, y in below],
        "liquidity_taken": sorted(taken, key=lambda d: d["candles_later"]),
        "trend_at_decision": ("up" if t and t[4] == UP else
                              "down" if t else "none"),
    }

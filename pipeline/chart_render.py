"""
Chart rendering, dark theme.

setup  — bare candles. No annotations, no dates, no price axis. The user reads
         the chart with no hints.
reveal — real prices, dates, swings, liquidity, sweeps, trend, outcome arrow,
         and a clear divider between what they saw and what happened.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np

BG = "#131722"
GRID = "#1e222d"
UP, DOWN = "#26a69a", "#ef5350"
TEXT, DIM = "#d1d4dc", "#787b86"
LIQ, SWEPT, PATH, DIV = "#e0a800", "#ef5350", "#2962ff", "#d1d4dc"

MC = mpf.make_marketcolors(up=UP, down=DOWN, edge={"up": UP, "down": DOWN},
                           wick={"up": UP, "down": DOWN},
                           volume={"up": "#1b5e57", "down": "#7a2c2b"})
MPF = mpf.make_mpf_style(
    marketcolors=MC, facecolor=BG, figcolor=BG, edgecolor=BG,
    gridcolor=GRID, gridstyle="-", y_on_right=True,
    rc={"font.size": 9, "text.color": TEXT, "axes.labelcolor": DIM,
        "xtick.color": DIM, "ytick.color": DIM, "axes.edgecolor": BG,
        "axes.linewidth": 0, "savefig.facecolor": BG, "figure.facecolor": BG})

MAX_STOP_PCT = 15.0
MAX_TARGET_PCT = 30.0

WIDTHS = dict(candle_linewidth=0.85, candle_width=0.76,
              volume_width=0.76, volume_linewidth=0.0)


def find_swings(df, span=4):
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
    h, l = df["High"].values, df["Low"].values
    above = [(i, h[i]) for i in highs if h[i + 1:].max(initial=-np.inf) < h[i]]
    below = [(i, l[i]) for i in lows if l[i + 1:].min(initial=np.inf) > l[i]]
    return above, below


def trendline(df, highs, lows):
    if len(lows) >= 2:
        a, b = lows[-2], lows[-1]
        if df["Low"].values[b] > df["Low"].values[a]:
            return a, df["Low"].values[a], b, df["Low"].values[b], UP
    if len(highs) >= 2:
        a, b = highs[-2], highs[-1]
        if df["High"].values[b] < df["High"].values[a]:
            return a, df["High"].values[a], b, df["High"].values[b], DOWN
    return None


def _base(df, show_axes, figsize=(11, 7.6)):
    has_vol = bool(df["Volume"].sum() > 0)
    kw = dict(type="candle", style=MPF, figsize=figsize, returnfig=True,
              volume=has_vol, tight_layout=True, xrotation=0,
              ylabel="", ylabel_lower="", update_width_config=WIDTHS,
              scale_padding={"left": 0.05, "right": 0.85, "top": 0.45, "bottom": 0.35})
    if has_vol:
        kw["panel_ratios"] = (8, 1)
    if not show_axes:
        kw["datetime_format"] = " "
    fig, axes = mpf.plot(df, **kw)
    ax = axes[0]
    if not show_axes:
        for a in axes:
            a.set_yticklabels([])
            a.set_xticklabels([])
            a.tick_params(length=0)
    if has_vol and len(axes) > 2:
        for p in axes[2].patches:
            p.set_edgecolor(p.get_facecolor())
            p.set_linewidth(0)
    for a in axes:
        a.set_facecolor(BG)
        a.grid(False)
        a.grid(axis="y", color=GRID, lw=0.5, alpha=0.55)
        for sp in a.spines.values():
            sp.set_visible(False)
        a.tick_params(length=0, pad=6)
    return fig, axes, ax


def _price_tag(ax, df, colour):
    """TradingView-style price label pinned to the right axis."""
    last = float(df["Close"].iloc[-1])
    ax.annotate(f"{last:,.2f}", xy=(1.0, last), xycoords=("axes fraction", "data"),
                xytext=(4, 0), textcoords="offset points", va="center", ha="left",
                fontsize=9, color="#ffffff", zorder=10, annotation_clip=False,
                bbox=dict(boxstyle="square,pad=0.35", fc=colour, ec="none"))
    ax.axhline(last, color=colour, lw=0.7, ls=(0, (4, 3)), alpha=0.6, zorder=1)


def render_setup(df, n, path, title="", headroom_pct=None):
    """
    Bare chart, nothing drawn on it.

    Returns the geometry the client needs to overlay stop/target lines on the
    saved PNG: the price panel's rectangle as fractions of the image, and the
    y-axis limits in data units. Saved WITHOUT bbox_inches="tight" so those
    fractions stay valid — tight cropping would invalidate them.
    """
    sub = df.iloc[:n]
    fig, axes, ax = _base(sub, show_axes=False)
    entry = float(sub["Close"].iloc[-1])
    c = UP if sub["Close"].iloc[-1] >= sub["Open"].iloc[-1] else DOWN
    ax.axhline(entry, color=c, lw=0.7, ls=(0, (4, 3)), alpha=0.6, zorder=1)

    # Reserve vertical room so the widest stop and target both stay on screen.
    # Values are normalised percent, so a pct move off entry is compounded.
    def moved(pct):
        return ((1 + entry / 100) * (1 + pct / 100) - 1) * 100

    room = headroom_pct if headroom_pct else MAX_TARGET_PCT
    lo, hi = ax.get_ylim()
    need_hi = moved(room)
    need_lo = moved(-room)
    lo, hi = min(lo, need_lo), max(hi, need_hi)
    pad = (hi - lo) * 0.02
    ax.set_ylim(lo - pad, hi + pad)

    # Empty space on the right where the hidden candles will appear.
    x0, x1 = ax.get_xlim()
    ax.set_xlim(x0, x1 + (x1 - x0) * 0.12)

    if title:
        ax.set_title(title, fontsize=11, color=TEXT, loc="left", pad=10)

    fig.canvas.draw()
    pos = ax.get_position()
    ymin, ymax = ax.get_ylim()
    fig.savefig(path, dpi=130, facecolor=BG)
    plt.close(fig)

    return {
        "left": round(pos.x0, 5),
        "width": round(pos.width, 5),
        "top": round(1 - pos.y1, 5),
        "height": round(pos.height, 5),
        "ymin": round(float(ymin), 6),
        "ymax": round(float(ymax), 6),
    }


def render_reveal(df, n, path, title=""):
    fig, axes, ax = _base(df, show_axes=True)
    highs, lows = find_swings(df.iloc[:n])
    above, below = liquidity(df.iloc[:n], highs, lows)
    last = len(df) - 1

    for i, y in above + below:
        ax.hlines(y, i, last, color=LIQ, lw=0.9, ls=(0, (5, 3)), alpha=0.75, zorder=2)
    if above or below:
        ax.hlines([], [], [], color=LIQ, lw=0.9, ls=(0, (5, 3)), label="resting liquidity")

    for i in highs:
        ax.plot(i, df["High"].values[i] * 1.004, marker="v", ms=4, color=DIM, zorder=3)
    for i in lows:
        ax.plot(i, df["Low"].values[i] * 0.996, marker="^", ms=4, color=DIM, zorder=3)

    t = trendline(df.iloc[:n], highs, lows)
    if t and t[2] > t[0]:
        x1, y1, x2, y2 = t[:4]
        slope = (y2 - y1) / (x2 - x1)
        ax.plot([x1, n - 1], [y1, y1 + slope * (n - 1 - x1)],
                color=t[4], lw=1.6, alpha=0.9, zorder=3, label="trend")

    ax.axvspan(-0.5, n - 0.5, color=BG, alpha=0.45, zorder=4)
    ax.axvline(n - 0.5, color=DIV, lw=1.4, alpha=0.9, zorder=7)
    bb = dict(boxstyle="round,pad=0.35", fc=BG, ec=GRID, alpha=0.95)
    ax.annotate("decision point", xy=(n - 0.5, 1.0), xycoords=("data", "axes fraction"),
                xytext=(-8, -14), textcoords="offset points", ha="right", va="top",
                fontsize=9, color=TEXT, zorder=8, bbox=bb)
    ax.annotate("what happened next", xy=(n - 0.5, 1.0), xycoords=("data", "axes fraction"),
                xytext=(10, -14), textcoords="offset points", ha="left", va="top",
                fontsize=9, color=PATH, zorder=8, bbox=bb)

    fut_h, fut_l = df["High"].values[n:], df["Low"].values[n:]
    for i, y in above:
        if (fut_h > y).any():
            ax.plot(n + int(np.argmax(fut_h > y)), y, marker="x", ms=11, mew=2.5,
                    color=SWEPT, zorder=8)
    for i, y in below:
        if (fut_l < y).any():
            ax.plot(n + int(np.argmax(fut_l < y)), y, marker="x", ms=11, mew=2.5,
                    color=SWEPT, zorder=8)
    ax.plot([], [], marker="x", ls="none", ms=9, mew=2, color=SWEPT, label="liquidity taken")

    start, end = df["Close"].values[n - 1], df["Close"].values[-1]
    ax.annotate("", xy=(last, end), xytext=(n - 1, start),
                arrowprops=dict(arrowstyle="-|>", lw=2.4, color=PATH,
                                connectionstyle="arc3,rad=0.12"), zorder=9)
    mid = n - 1 + (last - n + 1) * 0.55
    ax.annotate(f"{(end / start - 1) * 100:+.1f}%", xy=(mid, max(start, end)),
                xytext=(0, 26), textcoords="offset points", ha="center",
                va="bottom", fontsize=13, color=PATH, zorder=10, bbox=bb)

    _price_tag(ax, df, UP if end >= start else DOWN)
    if title:
        ax.set_title(title, fontsize=11, color=TEXT, loc="left", pad=26)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.01), ncol=3, fontsize=8,
              frameon=False, labelcolor=DIM, handlelength=1.6, columnspacing=1.4)
    fig.savefig(path, dpi=130, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def annotations(df, n):
    highs, lows = find_swings(df.iloc[:n])
    above, below = liquidity(df.iloc[:n], highs, lows)
    fut_h, fut_l = df["High"].values[n:], df["Low"].values[n:]

    taken = []
    for _, y in above:
        if (fut_h > y).any():
            taken.append({"side": "above", "level": round(float(y), 4),
                          "candles_later": int(np.argmax(fut_h > y)) + 1})
    for _, y in below:
        if (fut_l < y).any():
            taken.append({"side": "below", "level": round(float(y), 4),
                          "candles_later": int(np.argmax(fut_l < y)) + 1})

    t = trendline(df.iloc[:n], highs, lows)
    return {
        "swing_highs": len(highs), "swing_lows": len(lows),
        "resting_above": [round(float(y), 4) for _, y in above],
        "resting_below": [round(float(y), 4) for _, y in below],
        "liquidity_taken": sorted(taken, key=lambda d: d["candles_later"]),
        "trend_at_decision": "up" if t and t[4] == UP else "down" if t else "none",
    }

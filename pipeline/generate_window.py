"""
Generates ONE chart-quiz window end to end.

Output for a single window:
    out/<id>_setup.png    what the user sees (future hidden, axes stripped)
    out/<id>_reveal.png   what happened next
    out/<id>.json         question, ground-truth answer, computed facts

Real run (needs internet, no API key):
    python generate_window.py --symbol BTCUSDT --interval 1d --end 2019-07-10

Offline demo (synthetic candles, for testing the pipeline):
    python generate_window.py --demo
"""

import argparse, json, os, urllib.request, urllib.parse
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import mplfinance as mpf
import chart_render as cr

SETUP_CANDLES = 90    # what the user sees
HIDDEN_CANDLES = 30   # what they're predicting
OUT = "out"


# ---------------------------------------------------------------- data

COLS = ["Open", "High", "Low", "Close", "Volume"]


def fetch_binance(symbol, interval, end, limit):
    """Crypto. No key. Use data-api.binance.vision if api.binance.com is geo-blocked."""
    url = (f"https://api.binance.com/api/v3/klines?symbol={symbol}"
           f"&interval={interval}&endTime={int(end.timestamp() * 1000)}&limit={limit}")
    with urllib.request.urlopen(url, timeout=20) as r:
        raw = json.load(r)
    df = pd.DataFrame(raw, columns=[
        "open_time", "Open", "High", "Low", "Close", "Volume",
        "close_time", "qav", "trades", "tbb", "tbq", "ignore"])
    df["Date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    for c in COLS:
        df[c] = df[c].astype(float)
    return df.set_index("Date")[COLS]


TD_INTERVAL = {"1h": "1h", "4h": "4h", "1d": "1day"}


def fetch_twelvedata(symbol, interval, end, limit):
    """Forex and metals. Free key from twelvedata.com, set TWELVEDATA_KEY."""
    key = os.environ.get("TWELVEDATA_KEY")
    if not key:
        raise SystemExit("Set TWELVEDATA_KEY (free key from twelvedata.com)")
    url = ("https://api.twelvedata.com/time_series"
           f"?symbol={urllib.parse.quote(symbol)}"
           f"&interval={TD_INTERVAL[interval]}&outputsize={limit}"
           f"&end_date={end.strftime('%Y-%m-%d')}&order=ASC&apikey={key}")
    with urllib.request.urlopen(url, timeout=20) as r:
        raw = json.load(r)
    if raw.get("status") == "error":
        raise SystemExit(f"Twelve Data: {raw.get('message')}")
    df = pd.DataFrame(raw["values"])
    df["Date"] = pd.to_datetime(df["datetime"], utc=True)
    for c in COLS:
        # spot FX and metals have no real volume — zero-fill so the shape matches
        df[c] = df[c.lower()].astype(float) if c.lower() in df else 0.0
    return df.set_index("Date")[COLS]


PROVIDERS = {"binance": fetch_binance, "twelvedata": fetch_twelvedata}


def demo_klines(n, seed=7):
    """Deterministic synthetic candles so the pipeline runs without network."""
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.002, 0.035, n)))
    spread = close * rng.uniform(0.005, 0.03, n)
    open_ = np.r_[close[0], close[:-1]]
    df = pd.DataFrame({
        "Open": open_,
        "High": np.maximum(open_, close) + spread,
        "Low": np.minimum(open_, close) - spread,
        "Close": close,
        "Volume": rng.uniform(500, 3000, n),
    }, index=pd.date_range("2019-01-01", periods=n, freq="D", tz="UTC"))
    return df


# ---------------------------------------------------------------- indicators

def rsi(series, period=14):
    d = series.diff()
    gain = d.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    return 100 - 100 / (1 + gain / loss)


def facts(setup, future):
    """Everything computable. No interpretation, no narrative."""
    last = setup["Close"].iloc[-1]
    hi, lo = setup["High"].max(), setup["Low"].min()
    end = future["Close"].iloc[-1]

    peak = future["High"].cummax()
    max_dd = float(((future["Low"] - peak) / peak).min() * 100)

    broke_hi = future["High"].gt(hi)
    broke_lo = future["Low"].lt(lo)

    return {
        "change_pct": round((end / last - 1) * 100, 2),
        "direction": "up" if end > last else "down",
        "max_gain_pct": round((future["High"].max() / last - 1) * 100, 2),
        "max_loss_pct": round((future["Low"].min() / last - 1) * 100, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "setup_high": round(float(hi), 2),
        "setup_low": round(float(lo), 2),
        "broke_setup_high": bool(broke_hi.any()),
        "candles_to_break_high": int(broke_hi.argmax()) + 1 if broke_hi.any() else None,
        "broke_setup_low": bool(broke_lo.any()),
        "rsi_at_decision": round(float(rsi(setup["Close"]).iloc[-1]), 1),
        "close_vs_ma20_pct": round(float(
            (last / setup["Close"].rolling(20).mean().iloc[-1] - 1) * 100), 2),
        "vol_vs_20d_avg": round(float(
            setup["Volume"].iloc[-1] / setup["Volume"].rolling(20).mean().iloc[-1]), 2)
            if has_volume(setup) else None,
        "setup_range_pct": round(float((hi / lo - 1) * 100), 2),
    }


def has_volume(df):
    return bool(df["Volume"].sum() > 0)


# ---------------------------------------------------------------- rendering

def normalise(df):
    """Percent change from first close. Kills the price-level giveaway."""
    base = df["Close"].iloc[0]
    out = df.copy()
    for c in ["Open", "High", "Low", "Close"]:
        out[c] = (out[c] / base - 1) * 100
    return out


STYLE = mpf.make_mpf_style(
    base_mpf_style="charles",
    rc={"axes.labelsize": 0, "xtick.labelsize": 0, "ytick.labelsize": 0},
    y_on_right=False,
)


def render(df, path, hidden_from=None, title=""):
    kw = dict(type="candle", style=STYLE, volume=has_volume(df), figsize=(9, 6),
              xrotation=0, tight_layout=True, returnfig=True,
              axisoff=True, title=title)
    if hidden_from is not None:
        shade = [(hidden_from, df.index[-1])]
        kw["fill_between"] = dict(
            y1=float(df["Low"].min()), y2=float(df["High"].max()),
            where=df.index >= hidden_from, alpha=0.12, color="grey")
    fig, _ = mpf.plot(df, **kw)
    fig.savefig(path, dpi=110, bbox_inches="tight")
    matplotlib.pyplot.close(fig)


# ---------------------------------------------------------------- assembly

ASSET_CLASS = {"binance": "crypto", "twelvedata": "forex_metals", "demo": "demo"}


def build(df, wid, symbol="DEMO", interval="1d", provider="demo"):
    setup, future = df.iloc[:SETUP_CANDLES], df.iloc[SETUP_CANDLES:]
    f = facts(setup, future)

    os.makedirs(OUT, exist_ok=True)
    cr.render_setup(normalise(df), SETUP_CANDLES, f"{OUT}/{wid}_setup.png",
                    f"{interval} candles \u2014 what happens over the next {HIDDEN_CANDLES}?")
    cr.render_reveal(normalise(df), SETUP_CANDLES, f"{OUT}/{wid}_reveal.png",
                     f"{symbol} {interval} \u2014 revealed")
    anno = cr.annotations(df, SETUP_CANDLES)

    brief = (
        f"Price closed {abs(f['change_pct'])}% "
        f"{'higher' if f['direction'] == 'up' else 'lower'} after 30 candles. "
        + (f"It broke the setup high on candle {f['candles_to_break_high']}. "
           if f["broke_setup_high"] else "It never took out the setup high. ")
        + f"Worst drawdown along the way was {abs(f['max_drawdown_pct'])}%."
    )

    return {
        "id": wid,
        "symbol": symbol,
        "timeframe": interval,
        "asset_class": ASSET_CLASS[provider],
        "setup_candles": SETUP_CANDLES,
        "hidden_candles": HIDDEN_CANDLES,
        "question": f"Where does price close {HIDDEN_CANDLES} candles from now, "
                    "relative to the last close?",
        "answer_type": "direction_plus_confidence",
        "ground_truth": {"direction": f["direction"], "change_pct": f["change_pct"]},
        "facts": f,
        "annotations": anno,
        "source": {
            "provider": provider,
            "setup_from": str(df.index[0]),
            "decision_at": str(df.index[SETUP_CANDLES - 1]),
            "reveal_to": str(df.index[-1]),
        },
        "breakdown_brief": brief,
        "breakdown_detailed": None,   # written once per window, then cached
        "images": {"setup": f"{wid}_setup.png", "reveal": f"{wid}_reveal.png"},
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", default="binance", choices=list(PROVIDERS))
    p.add_argument("--symbol", default="BTCUSDT", help="BTCUSDT, or XAU/USD, GBP/USD")
    p.add_argument("--interval", default="1d", choices=["1h", "4h", "1d"])
    p.add_argument("--end", help="UTC date, YYYY-MM-DD")
    p.add_argument("--demo", action="store_true")
    a = p.parse_args()

    n = SETUP_CANDLES + HIDDEN_CANDLES
    if a.demo:
        rec = build(demo_klines(n), "demo_001")
    else:
        end = datetime.strptime(a.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        df = PROVIDERS[a.provider](a.symbol, a.interval, end, n)
        if len(df) < n:
            raise SystemExit(f"only got {len(df)} candles, need {n}")
        wid = f"{a.symbol.replace('/', '')}_{a.interval}_{a.end}"
        rec = build(df, wid, a.symbol, a.interval, a.provider)

    wid = rec["id"]
    with open(f"{OUT}/{wid}.json", "w") as fh:
        json.dump(rec, fh, indent=2)
    print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    main()

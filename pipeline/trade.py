"""
Runs a user's trade against the hidden candles.

Entry is the close of the decision candle. Stop and target are given as
percentage distances from entry. The simulation walks forward one candle at a
time and resolves whichever level is touched first.

One modelling decision worth knowing about: when a single candle's range
contains BOTH the stop and the target, OHLC data cannot tell you which was
touched first — you would need tick data. We assume the stop. That is the
conservative convention and it errs against the user, which is the right
direction to err in a teaching tool.

R is the unit of risk. Risking 2% to make 6% and winning is +3R. Losing is -1R.
Expectancy is the mean R across many trades, and it is the number that decides
whether an approach makes money, not the hit rate.
"""


def simulate(candles, entry, direction, stop_pct, target_pct):
    """
    candles: list of [open, high, low, close] for the hidden region
    direction: 'up' (long) or 'down' (short)
    stop_pct / target_pct: positive percentages, distance from entry
    """
    long = direction == "up"
    risk = entry * stop_pct / 100
    reward = entry * target_pct / 100

    stop = entry - risk if long else entry + risk
    target = entry + reward if long else entry - reward

    for i, (o, h, l, c) in enumerate(candles, start=1):
        hit_stop = l <= stop if long else h >= stop
        hit_target = h >= target if long else l <= target

        if hit_stop and hit_target:
            return _result("stopped", -1.0, stop, i, entry, long,
                           "Both levels were inside one candle, so we assume the "
                           "stop went first. Without tick data there is no way to know.")
        if hit_stop:
            return _result("stopped", -1.0, stop, i, entry, long)
        if hit_target:
            return _result("target", round(target_pct / stop_pct, 2), target, i, entry, long)

    exit_price = candles[-1][3]
    move = (exit_price - entry) if long else (entry - exit_price)
    return _result("open", round(move / risk, 2), exit_price, len(candles), entry, long,
                   "Neither level was reached. The trade is marked to the final close.")


def _result(outcome, r, price, candle, entry, long, note=None):
    return {
        "outcome": outcome,
        "r_multiple": r,
        "exit_price": round(price, 4),
        "exit_candle": candle,
        "entry_price": round(entry, 4),
        "direction": "long" if long else "short",
        "note": note,
    }


def verdict(res, right_direction):
    """One line summarising what happened, for the reveal panel."""
    r = res["r_multiple"]
    if res["outcome"] == "target":
        return f"Target hit on candle {res['exit_candle']}. +{r}R."
    if res["outcome"] == "stopped":
        if right_direction:
            return (f"Stopped out on candle {res['exit_candle']} for -1R — "
                    f"even though the direction was right. The stop was too tight "
                    f"for the volatility in this window.")
        return f"Stopped out on candle {res['exit_candle']}. -1R."
    sign = "+" if r >= 0 else ""
    return (f"Neither level reached. Closed at the end of the window for {sign}{r}R.")


def expectancy(results):
    """Mean R across trades. Positive means the approach makes money."""
    if not results:
        return None
    rs = [x["r_multiple"] for x in results]
    wins = [x for x in rs if x > 0]
    return {
        "trades": len(rs),
        "expectancy_r": round(sum(rs) / len(rs), 2),
        "win_rate_pct": round(100 * len(wins) / len(rs)),
        "avg_win_r": round(sum(wins) / len(wins), 2) if wins else 0,
        "total_r": round(sum(rs), 2),
    }

"""
Turns the computed facts and annotations into a readable paragraph.

Every clause here traces to a number. Nothing about motive, sentiment, or who
was buying — none of that is knowable from candles, and inventing it would
teach users to narrate randomness.
"""


def _ord(n):
    return {1: "the first candle", 2: "the second candle"}.get(n, f"candle {n}")


def paragraph(facts, anno, timeframe="1d"):
    f, a = facts, anno
    up = f["direction"] == "up"
    bars = []

    trend = a["trend_at_decision"]
    if trend != "none":
        bars.append(f"At the decision point the structure was {trend}"
                    f", with {a['swing_highs']} swing highs and {a['swing_lows']} "
                    f"swing lows behind it")
    else:
        bars.append("At the decision point there was no clean trend structure — "
                    "swings were not making consistent higher lows or lower highs")

    rsi = f["rsi_at_decision"]
    state = ("overbought territory" if rsi > 70 else
             "oversold territory" if rsi < 30 else "neutral territory")
    bars.append(f"RSI sat at {rsi}, {state}, and price was "
                f"{abs(f['close_vs_ma20_pct'])}% "
                f"{'above' if f['close_vs_ma20_pct'] > 0 else 'below'} its 20-period average")

    taken = a["liquidity_taken"]
    if taken:
        first = taken[0]
        side = "above" if first["side"] == "above" else "below"
        bars.append(f"The first thing that resolved was liquidity {side} the market: "
                    f"the level at {first['level']} was taken on {_ord(first['candles_later'])}")
        if len(taken) > 1:
            bars.append(f"{len(taken)} resting levels were cleared in total")
    else:
        rest = len(a["resting_above"]) + len(a["resting_below"])
        if rest:
            bars.append(f"None of the {rest} resting levels were reached")

    bars.append(f"Price finished {abs(f['change_pct'])}% "
                f"{'higher' if up else 'lower'}")

    excursion = f["max_gain_pct"] if up else f["max_loss_pct"]
    if abs(excursion) > abs(f["change_pct"]) * 1.5:
        bars.append(f"but it reached {abs(excursion)}% at the extreme before "
                    f"giving part of that back")

    dd = abs(f["max_drawdown_pct"])
    if dd > 3:
        bars.append(f"A long position taken at the decision candle would have been "
                    f"{dd}% underwater at the worst point")

    text = ". ".join(bars).replace(". but", ", but") + "."

    if dd > abs(f["change_pct"]) * 2 and dd > 5:
        text += (" The size of that drawdown relative to the final move is the "
                 "point worth noting: being right about direction and surviving "
                 "the path are different problems.")

    return text


def brief(facts, anno):
    """Free tier. Two sentences, outcome only."""
    f = facts
    s = (f"Price closed {abs(f['change_pct'])}% "
         f"{'higher' if f['direction'] == 'up' else 'lower'} after the hidden period.")
    taken = anno["liquidity_taken"]
    if taken:
        s += (f" {len(taken)} resting level"
              f"{'s were' if len(taken) > 1 else ' was'} taken along the way, "
              f"and the worst drawdown was {abs(f['max_drawdown_pct'])}%.")
    else:
        s += f" Worst drawdown along the way was {abs(f['max_drawdown_pct'])}%."
    return s


def key_insight(facts, anno, trade_res=None, right_direction=None):
    """
    The single most useful sentence for this window. Shown in a highlight box
    above everything else, because most people will not read the paragraph.
    """
    f = facts
    dd = abs(f["max_drawdown_pct"])
    move = abs(f["change_pct"])

    if trade_res:
        if trade_res["outcome"] == "stopped" and right_direction:
            return ("You read the direction correctly and still lost. "
                    "The stop was inside the noise of this window.")
        if trade_res["outcome"] == "target" and not right_direction:
            return ("Your target was hit even though price finished the other way. "
                    "Getting paid and being right are not the same thing.")
        if trade_res["outcome"] == "open":
            return ("Neither level was reached in 30 candles. Not every chart "
                    "resolves, and waiting has a cost.")

    if dd > move * 3 and dd > 8:
        return (f"Price finished only {move}% from entry but travelled {dd}% "
                f"against a long on the way. The path matters more than the destination.")

    taken = anno["liquidity_taken"]
    if taken and taken[0]["candles_later"] <= 3:
        side = "above" if taken[0]["side"] == "above" else "below"
        return (f"Resting liquidity {side} was taken within "
                f"{taken[0]['candles_later']} candles, then the move developed. "
                f"A sweep before the real move is the most common shape there is.")

    if f["rsi_at_decision"] > 70 and f["direction"] == "up":
        return ("RSI was overbought at the decision point and price kept going. "
                "Overbought is not a sell signal on its own.")
    if f["rsi_at_decision"] < 30 and f["direction"] == "down":
        return ("RSI was oversold at the decision point and price kept falling. "
                "Oversold is not a buy signal on its own.")

    if move < 2:
        return ("Price finished close to where it started. Plenty of windows "
                "are simply noise, and recognising that is a skill.")

    return None


def stats(facts, trade_res):
    """Compact numbers for the stat cards. Labels say what they mean."""
    f = facts
    out = [
        ("Outcome", f"{f['change_pct']:+.2f}%", "up" if f["direction"] == "up" else "down"),
        ("Best it got", f"{f['max_gain_pct']:+.2f}%", "up"),
        ("Worst it got", f"{f['max_loss_pct']:+.2f}%", "down"),
        ("Max drawdown", f"{f['max_drawdown_pct']:.2f}%", "down"),
    ]
    if trade_res:
        out.insert(1, ("Your exit", f"candle {trade_res['exit_candle']}", "flat"))
    return [{"label": a, "value": b, "tone": c} for a, b, c in out]

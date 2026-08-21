"""
Generates MANY windows in one run.

    python batch.py --symbol BTCUSDT --interval 1d --count 30
    python batch.py --provider twelvedata --symbol "XAU/USD" --interval 4h --count 20

Walks backwards from a start date, stepping one full window each time so no two
windows overlap. Skips anything that fails and keeps going.

Windows already in out/ are skipped, so you can stop and resume freely.
"""

import argparse, json, os, time
from datetime import datetime, timedelta, timezone

import generate_window as g

STEP_DAYS = {"1h": 5, "4h": 20, "1d": 120}  # 120 candles at each interval


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", default="binance", choices=list(g.PROVIDERS))
    p.add_argument("--symbol", default="BTCUSDT")
    p.add_argument("--interval", default="1d", choices=["1h", "4h", "1d"])
    p.add_argument("--count", type=int, default=20)
    p.add_argument("--start", help="Newest end date, YYYY-MM-DD. Default: 40 days ago.")
    p.add_argument("--pause", type=float, default=1.0, help="Seconds between calls")
    a = p.parse_args()

    end = (datetime.strptime(a.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
           if a.start else datetime.now(timezone.utc) - timedelta(days=40))
    step = timedelta(days=STEP_DAYS[a.interval])
    n = g.SETUP_CANDLES + g.HIDDEN_CANDLES
    os.makedirs(g.OUT, exist_ok=True)

    made = skipped = failed = 0
    for _ in range(a.count):
        date = end.strftime("%Y-%m-%d")
        wid = f"{a.symbol.replace('/', '')}_{a.interval}_{date}"
        end -= step

        if os.path.exists(f"{g.OUT}/{wid}.json"):
            skipped += 1
            continue

        try:
            df = g.PROVIDERS[a.provider](a.symbol, a.interval,
                                         datetime.strptime(date, "%Y-%m-%d")
                                         .replace(tzinfo=timezone.utc), n)
            if len(df) < n:
                print(f"  skip {date}: only {len(df)} candles")
                failed += 1
                continue
            rec = g.build(df, wid, a.symbol, a.interval, a.provider)
            with open(f"{g.OUT}/{wid}.json", "w") as fh:
                json.dump(rec, fh, indent=2)
            made += 1
            print(f"  {wid}  {rec['ground_truth']['change_pct']:+.2f}%")
        except Exception as e:
            print(f"  fail {date}: {e}")
            failed += 1

        time.sleep(a.pause)

    print(f"\n{made} made, {skipped} already existed, {failed} failed")
    print(f"Play them: python play.py")


if __name__ == "__main__":
    main()

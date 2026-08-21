# Chart quiz

Practice reading real historical price charts. The app hides the next 30
candles, you call the direction and how confident you are, then it reveals what
actually happened and scores your calibration.

Every question is built from real market data. Nothing is simulated.

## Layout

```
pipeline/    Python. Generates windows from real candles. (backend)
app/         Mobile app. (frontend)
fixtures/    Sample windows, committed. Build the app against these.
docs/        window-schema.md is the contract between the two.
out/         Generated output. Gitignored — never commit this.
```

## Running the pipeline

```bash
cd pipeline
pip install -r requirements.txt

# offline smoke test, synthetic candles
python generate_window.py --demo

# real crypto, no API key needed
python generate_window.py --symbol BTCUSDT --interval 1d --end 2026-07-15

# real gold or FX, needs a free key from twelvedata.com
export TWELVEDATA_KEY=yourkey          # Windows: set TWELVEDATA_KEY=yourkey
python generate_window.py --provider twelvedata --symbol "XAU/USD" --interval 4h --end 2026-07-15
```

Output lands in `out/`. Play it in a browser:

```bash
python play.py          # then open http://localhost:8000
```

## Constraints worth knowing

- A window needs its next 30 candles to already exist, so `--end` must be at
  least 30 candles before today.
- Setup images carry no dates, no price axis and no ticker. An experienced
  trader recognises a chart from its price level alone.
- Spot FX and metals have no real volume. The volume panel and volume-based
  facts are dropped automatically for those.
- Scores are Brier scores, so lower is better and 0.25 is what a coin flip
  gets. Always show that baseline next to a user's number.

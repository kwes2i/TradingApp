# Window schema

A **window** is one question. This file is the contract between the pipeline
and the app. If a field changes here, it changes in a commit both people see.

A real example lives at `fixtures/demo_001.json` with its two images.

## Fields

| Field | Type | Notes |
|---|---|---|
| `id` | string | Unique. Format `SYMBOL_INTERVAL_ENDDATE`. |
| `symbol` | string | `BTCUSDT`, `XAU/USD`, `GBP/USD`. |
| `timeframe` | string | `1h`, `4h`, `1d`. |
| `asset_class` | string | `crypto`, `forex_metals`. Ratings are kept separate per class and timeframe. |
| `setup_candles` | int | Candles the user sees. Currently 90. |
| `hidden_candles` | int | Candles being predicted. Currently 30. |
| `question` | string | Shown above the chart. |
| `answer_type` | string | `direction_plus_confidence`. |
| `ground_truth` | object | `direction` (`up`/`down`) and `change_pct`. **Never send to the client before the user answers.** |
| `facts` | object | Computed indicators and outcome measures. See below. |
| `annotations` | object | Swings, liquidity, sweeps. See below. |
| `source` | object | `provider`, `setup_from`, `decision_at`, `reveal_to`. Audit trail. |
| `breakdown_brief` | string | Free tier. Generated from `facts`. |
| `breakdown_detailed` | string \| null | Paid tier. Written once per window, cached. |
| `images.setup` | string | Filename. No dates, no price axis. |
| `images.reveal` | string | Filename. Dates and axis visible. |

## `facts`

All computed from the candles. No interpretation.

`change_pct`, `direction`, `max_gain_pct`, `max_loss_pct`, `max_drawdown_pct`,
`setup_high`, `setup_low`, `broke_setup_high`, `candles_to_break_high`,
`broke_setup_low`, `rsi_at_decision`, `close_vs_ma20_pct`, `vol_vs_20d_avg`
(null for spot FX and metals — no real volume), `setup_range_pct`.

## `annotations`

`swing_highs`, `swing_lows` — counts.
`resting_above`, `resting_below` — swing levels not yet traded through at the
decision candle. This is "liquidity".
`liquidity_taken` — list of `{side, level, candles_later}` for levels the hidden
region took out.
`trend_at_decision` — `up`, `down`, or `none`.

## Rules

1. The client never receives `ground_truth`, `facts` or `annotations` until the
   user has submitted an answer. Two endpoints, not one payload.
2. `images.setup` must contain no dates, no price axis, no ticker. Percent
   normalised from the first candle.
3. Adding a field is fine any time. Renaming or removing one needs a heads-up,
   because it breaks the app.

# App

Mobile frontend. Nothing here yet.

## Build against fixtures, not the pipeline

`../fixtures/` holds a real generated window and its two images. Import that
JSON directly and build every screen against it. You do not need Python
installed, and you are never blocked waiting on the backend.

The shape of that JSON is documented in `../docs/window-schema.md`.

## Two rules that affect the UI

1. **The answer arrives in a second request.** The first payload has the setup
   image and the question. `ground_truth`, `facts` and `annotations` only come
   back after the user submits. Don't design a screen that assumes it has
   everything up front.

2. **Confidence is part of the answer.** The user picks a direction *and* a
   confidence between 50 and 95%. Scoring is a Brier score:
   `(stated_probability_of_up - actual_outcome)^2`, lower is better. A coin
   flip scores 0.25 and that number should be visible next to the user's own.

## Planned screens

- Taster: two hand-picked windows, full breakdown, no account
- Signup
- Asset class picker (crypto only at launch, others "coming soon")
- Daily three: setup, answer, reveal, brief breakdown
- Subscription offer after the third reveal
- Calibration: accuracy by confidence band, per timeframe and asset class

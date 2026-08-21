"""
Interactive player for the windows made by generate_window.py.

    python play.py

Then open http://localhost:8000 in your browser.
Reads every *.json in out/ and serves them one at a time.
Your calls are logged to out/calls.json so you can check calibration later.
"""

import json, glob, os, random
from http.server import BaseHTTPRequestHandler, HTTPServer

OUT = "out"
PORT = 8000

PAGE = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Chart quiz</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, system-ui, sans-serif; max-width: 940px;
         margin: 0 auto; padding: 24px 20px 60px; line-height: 1.6; }
  h1 { font-size: 20px; font-weight: 500; margin: 0 0 4px; }
  .sub { opacity: .6; font-size: 14px; margin-bottom: 20px; }
  img { width: 100%; border: 1px solid rgba(128,128,128,.3); border-radius: 8px;
        display: block; background: #fff; }
  .row { display: flex; gap: 10px; margin: 18px 0 10px; }
  button { flex: 1; padding: 14px; font-size: 15px; font-family: inherit;
           border: 1px solid rgba(128,128,128,.4); background: transparent;
           color: inherit; border-radius: 8px; cursor: pointer; }
  button:hover { border-color: rgba(128,128,128,.8); }
  button.sel { border-color: #3d8; border-width: 2px; }
  button.primary { background: #3d8; color: #052; border-color: #3d8; font-weight: 500; }
  button:disabled { opacity: .35; cursor: default; }
  label { font-size: 14px; opacity: .75; display: block; margin-top: 16px; }
  input[type=range] { width: 100%; margin-top: 6px; }
  .conf { font-variant-numeric: tabular-nums; font-size: 15px; }
  .panel { margin-top: 22px; padding: 16px; border-radius: 8px;
           background: rgba(128,128,128,.1); font-size: 15px; }
  .verdict { font-size: 17px; font-weight: 500; margin-bottom: 8px; }
  .good { color: #2a9d5c; } .bad { color: #c4453c; }
  .facts { font-size: 13px; opacity: .7; margin-top: 12px;
           font-family: ui-monospace, monospace; white-space: pre-wrap; }
  .score { font-size: 13px; opacity: .7; margin-top: 24px;
           border-top: 1px solid rgba(128,128,128,.25); padding-top: 12px; }
  .err { color: #c4453c; font-size: 14px; margin-top: 8px; min-height: 20px; }
  .hide { display: none; }
</style></head><body>

<h1>Where does price go next?</h1>
<div class="sub" id="meta"></div>

<img id="chart" alt="Price chart with the outcome hidden">

<div id="ask">
  <div class="row">
    <button id="up" onclick="pick('up')">Higher &uarr;</button>
    <button id="down" onclick="pick('down')">Lower &darr;</button>
  </div>
  <label>How confident? <span class="conf" id="cval">70%</span></label>
  <input type="range" id="conf" min="50" max="95" value="70"
         oninput="document.getElementById('cval').textContent = this.value + '%'">
  <div class="err" id="err"></div>
  <div class="row"><button class="primary" onclick="reveal()">Reveal</button></div>
</div>

<div id="result" class="hide">
  <div class="panel">
    <div class="verdict" id="verdict"></div>
    <div id="brief"></div>
    <div class="facts" id="facts"></div>
  </div>
  <div class="row"><button class="primary" onclick="next()">Next chart</button></div>
</div>

<div class="score" id="score"></div>

<script>
let cur = null, choice = null, played = 0, brierSum = 0;

async function next() {
  choice = null;
  document.getElementById('err').textContent = '';
  document.getElementById('up').classList.remove('sel');
  document.getElementById('down').classList.remove('sel');
  document.getElementById('result').classList.add('hide');
  document.getElementById('ask').classList.remove('hide');
  const r = await fetch('/api/next');
  cur = await r.json();
  if (cur.error) { document.getElementById('meta').textContent = cur.error; return; }
  document.getElementById('chart').src = '/img/' + cur.images.setup + '?t=' + Date.now();
  document.getElementById('meta').textContent =
    'Asset and dates hidden. Y axis is percent from the first candle.';
}

function pick(d) {
  choice = d;
  document.getElementById('err').textContent = '';
  document.getElementById('up').classList.toggle('sel', d === 'up');
  document.getElementById('down').classList.toggle('sel', d === 'down');
}

function reveal() {
  if (!choice) {
    document.getElementById('err').textContent = 'Pick higher or lower first.';
    return;
  }
  const conf = +document.getElementById('conf').value / 100;
  const pUp = choice === 'up' ? conf : 1 - conf;
  const actual = cur.ground_truth.direction === 'up' ? 1 : 0;
  const brier = Math.pow(pUp - actual, 2);
  const right = choice === cur.ground_truth.direction;

  played++; brierSum += brier;

  document.getElementById('chart').src = '/img/' + cur.images.reveal + '?t=' + Date.now();
  const v = document.getElementById('verdict');
  v.textContent = right ? 'Correct' : 'Wrong';
  v.className = 'verdict ' + (right ? 'good' : 'bad');
  document.getElementById('brief').textContent = cur.breakdown_brief;

  const f = cur.facts;
  document.getElementById('facts').textContent =
    `rsi at decision      ${f.rsi_at_decision}\n` +
    `close vs 20d ma      ${f.close_vs_ma20_pct}%\n` +
    `volume vs 20d avg    ${f.vol_vs_20d_avg}x\n` +
    `best point           ${f.max_gain_pct}%\n` +
    `worst point          ${f.max_loss_pct}%\n` +
    `brier this call      ${brier.toFixed(3)}`;

  document.getElementById('ask').classList.add('hide');
  document.getElementById('result').classList.remove('hide');

  const avg = brierSum / played;
  document.getElementById('score').textContent =
    `${played} call${played > 1 ? 's' : ''}  ·  your brier ${avg.toFixed(3)}  ·  ` +
    `coin flip 0.250  ·  ${avg < 0.25 ? 'beating the coin flip' : 'not beating the coin flip'}`;

  fetch('/api/log', { method: 'POST', body: JSON.stringify({
    id: cur.id, choice, confidence: conf, actual: cur.ground_truth.direction,
    change_pct: cur.ground_truth.change_pct, brier }) });
}

next();
</script>
</body></html>"""


def windows():
    out = []
    for p in sorted(glob.glob(f"{OUT}/*.json")):
        if os.path.basename(p) == "calls.json":
            continue
        with open(p) as f:
            out.append(json.load(f))
    return out


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            return self._send(200, PAGE.encode(), "text/html; charset=utf-8")

        if self.path.startswith("/api/next"):
            w = windows()
            if not w:
                return self._send(200, json.dumps(
                    {"error": "No windows in out/. Run generate_window.py first."}).encode())
            return self._send(200, json.dumps(random.choice(w)).encode())

        if self.path.startswith("/img/"):
            name = os.path.basename(self.path.split("?")[0])
            path = os.path.join(OUT, name)
            if not os.path.isfile(path):
                return self._send(404, b"not found", "text/plain")
            with open(path, "rb") as f:
                return self._send(200, f.read(), "image/png")

        self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path == "/api/log":
            n = int(self.headers.get("Content-Length", 0))
            entry = json.loads(self.rfile.read(n))
            log_path = f"{OUT}/calls.json"
            log = json.load(open(log_path)) if os.path.exists(log_path) else []
            log.append(entry)
            json.dump(log, open(log_path, "w"), indent=2)
            return self._send(200, b'{"ok":true}')
        self._send(404, b"not found", "text/plain")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    n = len(windows())
    print(f"{n} window(s) loaded from {OUT}/")
    print(f"Open http://localhost:{PORT} — Ctrl+C to stop")
    HTTPServer(("", PORT), Handler).serve_forever()

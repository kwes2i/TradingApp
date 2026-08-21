"""
Interactive player. Set a direction, a stop and a target, then see the trade
resolved against the real candles.

    python play.py        then open http://localhost:8000

Two endpoints on purpose:
    GET  /api/next     question and setup image only. No answer data.
    POST /api/trade    grades the trade server-side, THEN returns the reveal.

The hidden candles never reach the browser before the user has committed, which
is the same rule the real app has to follow.

Trades are logged to out/calls.json.
"""

import json, glob, os, random, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import trade
import breakdown

OUT = "out"
PORT = 8000

PAGE = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Chart quiz</title>
<style>
  :root { color-scheme: dark; }
  body { font-family: -apple-system, system-ui, sans-serif; max-width: 1000px;
         margin: 0 auto; padding: 24px 20px 60px; line-height: 1.6;
         background: #0d1017; color: #d1d4dc; }
  h1 { font-size: 20px; font-weight: 500; margin: 0 0 4px; }
  .sub { color: #787b86; font-size: 14px; margin-bottom: 16px; }
  img { width: 100%; border: 1px solid #1e222d; border-radius: 8px;
        display: block; background: #131722; }
  .wrap { position: relative; }
  .line { position: absolute; left: 0; right: 0; height: 0;
          border-top: 1px dashed; pointer-events: none; transition: top .08s linear; }
  .tag { position: absolute; right: 8px; transform: translateY(-50%);
         font-size: 11px; font-family: ui-monospace, monospace; padding: 2px 7px;
         border-radius: 3px; color: #fff; pointer-events: none;
         transition: top .08s linear; white-space: nowrap; }
  #tpLine { border-color: #26a69a; } #tpTag { background: #26a69a; }
  #slLine { border-color: #ef5350; } #slTag { background: #ef5350; }
  #enLine { border-color: #787b86; } #enTag { background: #434651; }
  .zone { position: absolute; left: 0; right: 0; pointer-events: none;
          transition: top .08s linear, height .08s linear; }
  #tpZone { background: rgba(38,166,154,.10); }
  #slZone { background: rgba(239,83,80,.10); }
  .tfbar { display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }
  .tf { padding: 7px 16px; font-size: 13px; background: #1a1e29;
        border: 1px solid #2a2e39; color: #787b86; border-radius: 6px; cursor: pointer; }
  .tf.on { background: #2962ff; border-color: #2962ff; color: #fff; }
  .tf:disabled { opacity: .3; cursor: default; }
  .row { display: flex; gap: 10px; margin: 18px 0 10px; }
  button { flex: 1; padding: 14px; font-size: 15px; font-family: inherit;
           border: 1px solid #2a2e39; background: #1a1e29; color: #d1d4dc;
           border-radius: 8px; cursor: pointer; }
  button:hover { border-color: #434651; }
  #up.sel { border-color: #26a69a; background: #14342f; color: #26a69a; }
  #down.sel { border-color: #ef5350; background: #3a1e1e; color: #ef5350; }
  button.primary { background: #2962ff; color: #fff; border-color: #2962ff; font-weight: 500; }
  .levels { display: flex; gap: 20px; margin-top: 18px; align-items: flex-end; }
  .lv { flex: 1; }
  .lv label { display: block; font-size: 13px; color: #787b86; margin-bottom: 6px; }
  .lv input { width: 100%; }
  .lvval { font-variant-numeric: tabular-nums; font-size: 15px; color: #d1d4dc; }
  .atr { font-size: 12px; color: #6b7280; margin-left: 6px; }
  .rr { font-size: 14px; color: #787b86; margin-top: 12px; }
  .vol { font-size: 12px; color: #6b7280; margin-top: 6px; }
  .rr b { color: #d1d4dc; font-weight: 500; }
  .panel { margin-top: 22px; padding: 20px; border-radius: 8px;
           background: #171b26; border: 1px solid #1e222d; font-size: 15px; }
  .head { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
  .rbig { font-size: 34px; font-weight: 500; letter-spacing: -0.5px; }
  .badge { font-size: 12px; padding: 4px 10px; border-radius: 4px;
           text-transform: uppercase; letter-spacing: .04em; }
  .b-win { background: #14342f; color: #26a69a; }
  .b-loss { background: #3a1e1e; color: #ef5350; }
  .b-flat { background: #22262f; color: #a3a6ad; }
  .vline { color: #b2b5be; font-size: 15px; margin-top: 6px; }
  .good { color: #26a69a; } .bad { color: #ef5350; } .flat { color: #d1d4dc; }
  .insight { margin-top: 18px; padding: 14px 16px; border-radius: 6px;
             background: #1a2233; border-left: 3px solid #2962ff;
             color: #dfe3ea; font-size: 15px; line-height: 1.55; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
           gap: 10px; margin-top: 18px; }
  .card { background: #131722; border: 1px solid #1e222d; border-radius: 6px;
          padding: 11px 12px; }
  .card .l { font-size: 11px; color: #6b7280; text-transform: uppercase;
             letter-spacing: .05em; margin-bottom: 5px; }
  .card .v { font-size: 17px; font-weight: 500; font-variant-numeric: tabular-nums; }
  .para { margin-top: 18px; padding-top: 16px; border-top: 1px solid #1e222d;
          color: #9ca3af; font-size: 14px; line-height: 1.65; }
  .para b { color: #d1d4dc; font-weight: 500; }
  details { margin-top: 14px; }
  summary { font-size: 13px; color: #6b7280; cursor: pointer; }
  .facts { font-size: 13px; color: #787b86; margin-top: 10px;
           font-family: ui-monospace, monospace; white-space: pre-wrap; }
  .score { font-size: 13px; color: #787b86; margin-top: 24px;
           border-top: 1px solid #1e222d; padding-top: 12px; }
  .err { color: #ef5350; font-size: 14px; margin-top: 8px; min-height: 20px; }
  .hide { display: none; }
</style></head><body>

<h1>Long or short?</h1>
<div class="sub" id="meta"></div>
<div class="tfbar" id="tfbar"></div>

<div class="wrap">
  <img id="chart" alt="Price chart with the outcome hidden">
  <div class="zone" id="tpZone"></div>
  <div class="zone" id="slZone"></div>
  <div class="line" id="enLine"></div><div class="tag" id="enTag">entry</div>
  <div class="line" id="tpLine"></div><div class="tag" id="tpTag">TP</div>
  <div class="line" id="slLine"></div><div class="tag" id="slTag">SL</div>
</div>

<div id="ask">
  <div class="row">
    <button id="up" onclick="pick('up')">Long &uarr;</button>
    <button id="down" onclick="pick('down')">Short &darr;</button>
  </div>
  <div class="levels">
    <div class="lv">
      <label>Stop loss <span class="lvval" id="sv">2.0%</span>
        <span class="atr" id="satr"></span></label>
      <input type="range" id="stop" min="0.5" max="15" step="0.1" value="2" oninput="upd()">
    </div>
    <div class="lv">
      <label>Take profit <span class="lvval" id="tv">6.0%</span>
        <span class="atr" id="tatr"></span></label>
      <input type="range" id="target" min="0.5" max="30" step="0.1" value="6" oninput="upd()">
    </div>
  </div>
  <div class="rr" id="rr"></div>
  <div class="vol" id="vol"></div>
  <div class="err" id="err"></div>
  <div class="row"><button class="primary" onclick="submit()">Place trade</button></div>
</div>

<div id="result" class="hide">
  <div class="panel">
    <div class="head">
      <span class="rbig" id="rbig"></span>
      <span class="badge" id="badge"></span>
    </div>
    <div class="vline" id="brief"></div>
    <div class="insight hide" id="insight"></div>
    <div class="cards" id="cards"></div>
    <div class="para" id="para"></div>
    <details>
      <summary>Raw numbers</summary>
      <div class="facts" id="facts"></div>
    </details>
  </div>
  <div class="row"><button class="primary" onclick="next()">Next chart</button></div>
</div>

<div class="score" id="score"></div>

<script>
let cur = null, choice = null, tf = 'all', results = [];

function showLines(on) {
  for (const id of ['enLine','enTag','tpLine','tpTag','slLine','slTag','tpZone','slZone'])
    document.getElementById(id).style.display = on ? 'block' : 'none';
}

/* normalised chart units -> fraction down the image */
function yFrac(norm) {
  const g = cur.geometry;
  const inAxes = (norm - g.ymin) / (g.ymax - g.ymin);
  return g.top + (1 - inAxes) * g.height;
}

/* entry is a normalised value; a pct move off entry in PRICE terms */
function moved(pct) {
  return ((1 + cur.entry_norm / 100) * (1 + pct / 100) - 1) * 100;
}

function place(lineId, tagId, norm, label) {
  const pct = (yFrac(norm) * 100);
  const clamped = Math.max(0, Math.min(100, pct));
  document.getElementById(lineId).style.top = clamped + '%';
  const tag = document.getElementById(tagId);
  tag.style.top = clamped + '%';
  tag.textContent = label;
}

function niceStep(range) {
  if (range <= 5) return 0.05;
  if (range <= 15) return 0.1;
  if (range <= 40) return 0.25;
  return 0.5;
}

function applyLimits() {
  if (!cur || !cur.limits) return;
  const L = cur.limits;
  const sl = document.getElementById('stop'), tg = document.getElementById('target');

  const sStep = niceStep(L.stop_max - L.stop_min);
  const tStep = niceStep(L.target_max - L.target_min);

  /* widen the bounds first so assigning a value never gets clamped */
  sl.min = 0; sl.max = 1000; tg.min = 0; tg.max = 1000;
  sl.step = sStep; tg.step = tStep;
  sl.value = Math.min(L.stop_max, Math.max(L.stop_min, L.atr_pct * 1.5));
  tg.value = Math.min(L.target_max, Math.max(L.target_min, L.atr_pct * 4));
  sl.min = L.stop_min; sl.max = L.stop_max;
  tg.min = L.target_min; tg.max = L.target_max;
  document.getElementById('vol').textContent =
    'This chart moves about ' + L.atr_pct.toFixed(2) +
    '% per candle on average. Stops inside that are inside the noise.';
}

function upd() {
  const s = +document.getElementById('stop').value;
  const t = +document.getElementById('target').value;
  const atr = cur && cur.limits ? cur.limits.atr_pct : null;
  document.getElementById('sv').textContent = s.toFixed(2) + '%';
  document.getElementById('tv').textContent = t.toFixed(2) + '%';
  if (atr) {
    document.getElementById('satr').textContent = '(' + (s / atr).toFixed(1) + ' ATR)';
    document.getElementById('tatr').textContent = '(' + (t / atr).toFixed(1) + ' ATR)';
  }
  document.getElementById('rr').innerHTML =
    'Risk/reward <b>1 : ' + (t / s).toFixed(2) + '</b> — a win pays <b>' +
    (t / s).toFixed(2) + 'R</b>, a loss costs <b>1R</b>';

  if (!cur || !cur.geometry) return;
  if (!choice) { showLines(false); return; }
  showLines(true);

  const long = choice === 'up';
  const tpN = moved(long ? t : -t);
  const slN = moved(long ? -s : s);
  const enF = yFrac(cur.entry_norm) * 100;
  const tpF = Math.max(0, Math.min(100, yFrac(tpN) * 100));
  const slF = Math.max(0, Math.min(100, yFrac(slN) * 100));

  place('enLine', 'enTag', cur.entry_norm, 'entry');
  place('tpLine', 'tpTag', tpN, 'TP  +' + t.toFixed(1) + '%');
  place('slLine', 'slTag', slN, 'SL  \u2212' + s.toFixed(1) + '%');

  const tz = document.getElementById('tpZone');
  tz.style.top = Math.min(enF, tpF) + '%';
  tz.style.height = Math.abs(enF - tpF) + '%';
  const sz = document.getElementById('slZone');
  sz.style.top = Math.min(enF, slF) + '%';
  sz.style.height = Math.abs(enF - slF) + '%';
}

async function loadCounts() {
  const d = await (await fetch('/api/counts')).json();
  const bar = document.getElementById('tfbar');
  bar.innerHTML = '';
  const total = Object.values(d.counts).reduce((a, b) => a + b, 0);
  for (const [k, label] of [['all','All'],['1h','1 hour'],['4h','4 hour'],['1d','Daily']]) {
    const n = k === 'all' ? total : (d.counts[k] || 0);
    const b = document.createElement('button');
    b.className = 'tf' + (tf === k ? ' on' : '');
    b.textContent = label + ' (' + n + ')';
    b.disabled = n === 0;
    b.onclick = () => { tf = k; loadCounts(); next(); };
    bar.appendChild(b);
  }
}

async function next() {
  choice = null;
  document.getElementById('err').textContent = '';
  document.getElementById('up').classList.remove('sel');
  document.getElementById('down').classList.remove('sel');
  document.getElementById('result').classList.add('hide');
  document.getElementById('ask').classList.remove('hide');
  showLines(false);
  cur = await (await fetch('/api/next?tf=' + tf)).json();
  if (cur.error) { document.getElementById('meta').textContent = cur.error; return; }
  document.getElementById('chart').src = '/img/' + cur.setup_image + '?t=' + Date.now();
  document.getElementById('meta').textContent =
    'Asset, dates and price hidden. Entry is the last close.';
  applyLimits();
  upd();
}

function pick(d) {
  choice = d;
  document.getElementById('err').textContent = '';
  document.getElementById('up').classList.toggle('sel', d === 'up');
  document.getElementById('down').classList.toggle('sel', d === 'down');
  upd();
}

async function submit() {
  if (!choice) {
    document.getElementById('err').textContent = 'Pick long or short first.';
    return;
  }
  const body = { id: cur.id, direction: choice,
                 stop_pct: +document.getElementById('stop').value,
                 target_pct: +document.getElementById('target').value };
  const r = await (await fetch('/api/trade', { method: 'POST',
                    body: JSON.stringify(body) })).json();

  results.push(r.trade.r_multiple);

  showLines(false);
  document.getElementById('chart').src = '/img/' + r.reveal_image + '?t=' + Date.now();
  const rm = r.trade.r_multiple;
  const big = document.getElementById('rbig');
  big.textContent = (rm > 0 ? '+' : '') + rm.toFixed(2) + 'R';
  big.className = 'rbig ' + (rm > 0 ? 'good' : rm < 0 ? 'bad' : 'flat');

  const badge = document.getElementById('badge');
  const oc = r.trade.outcome;
  badge.textContent = oc === 'target' ? 'target hit'
                    : oc === 'stopped' ? 'stopped out' : 'never resolved';
  badge.className = 'badge ' + (oc === 'target' ? 'b-win'
                    : oc === 'stopped' ? 'b-loss' : 'b-flat');

  document.getElementById('brief').textContent =
    r.verdict + (r.trade.note ? ' ' + r.trade.note : '');

  const ins = document.getElementById('insight');
  if (r.key_insight) { ins.textContent = r.key_insight; ins.classList.remove('hide'); }
  else ins.classList.add('hide');

  const cards = document.getElementById('cards');
  cards.innerHTML = '';
  for (const c of r.stats) {
    const d = document.createElement('div');
    d.className = 'card';
    d.innerHTML = '<div class="l"></div><div class="v"></div>';
    d.querySelector('.l').textContent = c.label;
    const v = d.querySelector('.v');
    v.textContent = c.value;
    v.className = 'v ' + (c.tone === 'up' ? 'good' : c.tone === 'down' ? 'bad' : 'flat');
    cards.appendChild(d);
  }

  document.getElementById('para').textContent = r.breakdown_detailed || '';

  const f = r.facts;
  document.getElementById('facts').textContent =
    `entry                ${r.trade.entry_price}\n` +
    `exit                 ${(+r.trade.exit_price).toFixed(2)} on candle ${r.trade.exit_candle}\n` +
    `rsi at decision      ${f.rsi_at_decision}\n` +
    `close vs 20d ma      ${f.close_vs_ma20_pct}%\n` +
    `setup range          ${f.setup_range_pct}%\n` +
    `trend at decision    ${r.annotations.trend_at_decision}\n` +
    `levels taken         ${r.annotations.liquidity_taken.length}`;

  document.getElementById('ask').classList.add('hide');
  document.getElementById('result').classList.remove('hide');

  const n = results.length;
  const total = results.reduce((a, b) => a + b, 0);
  const wins = results.filter(x => x > 0).length;
  document.getElementById('score').textContent =
    `${n} trade${n > 1 ? 's' : ''}  ·  total ${total >= 0 ? '+' : ''}${total.toFixed(2)}R  ·  ` +
    `expectancy ${(total / n) >= 0 ? '+' : ''}${(total / n).toFixed(2)}R per trade  ·  ` +
    `win rate ${Math.round(100 * wins / n)}%`;
}

loadCounts().then(next);
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


def by_id(wid):
    for w in windows():
        if w["id"] == wid:
            return w
    return None


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

        if self.path.startswith("/api/counts"):
            c = {}
            for w in windows():
                k = w.get("timeframe", "1d")
                c[k] = c.get(k, 0) + 1
            return self._send(200, json.dumps({"counts": c}).encode())

        if self.path.startswith("/api/next"):
            tf = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query).get("tf", ["all"])[0]
            w = windows()
            if tf != "all":
                w = [x for x in w if x.get("timeframe") == tf]
            if not w:
                return self._send(200, json.dumps(
                    {"error": "No windows for that timeframe. Run batch.py first."}).encode())
            c = random.choice(w)
            # only what the user is allowed to see before committing
            return self._send(200, json.dumps({
                "id": c["id"], "question": c["question"],
                "timeframe": c["timeframe"],
                "setup_image": c["images"]["setup"],
                "entry_norm": c["entry_norm"],
                "geometry": c["setup_geometry"],
                "limits": c["limits"],
            }).encode())

        if self.path.startswith("/img/"):
            name = os.path.basename(self.path.split("?")[0])
            path = os.path.join(OUT, name)
            if not os.path.isfile(path):
                return self._send(404, b"not found", "text/plain")
            with open(path, "rb") as f:
                return self._send(200, f.read(), "image/png")

        self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/api/trade":
            return self._send(404, b"not found", "text/plain")

        n = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(n))
        w = by_id(req["id"])
        if not w:
            return self._send(404, json.dumps({"error": "unknown window"}).encode())

        res = trade.simulate(w["hidden_ohlc"], w["entry_price"], req["direction"],
                             float(req["stop_pct"]), float(req["target_pct"]))
        right = req["direction"] == w["ground_truth"]["direction"]

        log_path = f"{OUT}/calls.json"
        log = json.load(open(log_path)) if os.path.exists(log_path) else []
        log.append({"id": w["id"], "direction": req["direction"],
                    "stop_pct": req["stop_pct"], "target_pct": req["target_pct"],
                    "outcome": res["outcome"], "r_multiple": res["r_multiple"],
                    "correct_direction": right})
        json.dump(log, open(log_path, "w"), indent=2)

        return self._send(200, json.dumps({
            "trade": res,
            "verdict": trade.verdict(res, right),
            "ground_truth": w["ground_truth"],
            "facts": w["facts"],
            "annotations": w["annotations"],
            "key_insight": breakdown.key_insight(w["facts"], w["annotations"], res, right),
            "stats": breakdown.stats(w["facts"], res),
            "breakdown_detailed": w["breakdown_detailed"],
            "reveal_image": w["images"]["reveal"],
        }).encode())

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"{len(windows())} window(s) loaded from {OUT}/")
    print(f"Open http://localhost:{PORT} — Ctrl+C to stop")
    HTTPServer(("", PORT), Handler).serve_forever()

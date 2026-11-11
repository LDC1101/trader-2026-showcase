"""
Buy alert: reports via Telegram when Brent reaches the trigger and includes the
ready-made order (WKN, limit, units). No order, no access to the game account: the
player types the order into the web interface by hand (Rule 10). It is a price alert
like the one in any broker app.

Configuration in depot/buy_alert.json. If the file is missing or valid_until has
passed, nothing happens. Example (also in depot/examples/buy_alert.json):
  {"depot": "A", "wkn": "FG8V8A", "asset": -4, "name": "Brent", "direction": "call",
   "barrier": 98.67, "trigger": 104.2, "stake": 20000, "markup": 0.05,
   "valid_until": "2026-10-23", "repeat_min": 120, "max_per_day": 3,
   "note": "..."}

Where it runs: GitHub Actions, every 15 minutes on weekdays (reference workflow in
ops/github-actions/), not in the local Watch. Reason: the laptop sleeps during the
day; on 15 Oct 2026 there was not a single Watch run between 5:00 and 18:00, and the
pullback to 103.4 would have gone unnoticed. Token and chat ID are repository secrets,
the state (last report) lives in the Actions cache (state.json, key
buy-alert-state-<run>; the default token may not write repository variables,
16 Oct 2026 HTTP 403); locally in data/buy_alert_state.json.

Price: derived from the SG call prices (sg_products.implied_spot), i.e. for exactly
the contract SG quotes the product against. If SG fails: Yahoo BZ=F, with the ask
then estimated.

The alert goes quiet by itself as soon as depot/positions.md has a row for the depot
under "Open positions", so record the position after buying.

Usage:   python3 src/buy_alert.py                        # live (sends)
         python3 src/buy_alert.py --test                 # prints instead of sending
         python3 src/buy_alert.py --test --probe 104.0   # pretends Brent is at 104.0
         python3 src/buy_alert.py --test --probe-trigger
         python3 src/buy_alert.py --activation           # one-off start message
         python3 src/buy_alert.py --state-in state.json --state-out state.json   # Actions
"""
import argparse
import datetime as dt
import io
import json
import math
import os
import re
import subprocess
import sys
import urllib.request
import zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
TZ = zoneinfo.ZoneInfo("Europe/Berlin")
CONFIG = os.path.join(REPO, "depot", "buy_alert.json")
POSITIONS = os.path.join(REPO, "depot", "positions.md")
STATE_LOCAL = os.path.join(REPO, "data", "buy_alert_state.json")
FEE = 3.90
FX_FALLBACK = 0.9026   # EUR per USD point, from the SG calls on 16 Oct 2026 (estimate only)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def log(s):
    print(f"{dt.datetime.now(TZ):%Y-%m-%d %H:%M} {s}", flush=True)


def num(x, n=2):
    """English number: thousands comma, decimal point."""
    return f"{x:,.{n}f}"


def load_env():
    out = dict(os.environ)
    try:
        for line in io.open(os.path.join(REPO, ".env"), encoding="utf-8"):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                out.setdefault(k, v)
    except FileNotFoundError:
        pass
    return out


def send_telegram(text, test=False):
    if test:
        print("--- WOULD SEND ---\n" + text + "\n---")
        return True
    e = load_env()
    if not e.get("TELEGRAM_BOT_TOKEN") or not e.get("TELEGRAM_CHAT_ID"):
        log("Telegram not configured")
        return False
    r = subprocess.run(["curl", "-sS", "-m", "20", "-X", "POST",
                        f"https://api.telegram.org/bot{e['TELEGRAM_BOT_TOKEN']}/sendMessage",
                        "--data-urlencode", f"chat_id={e['TELEGRAM_CHAT_ID']}",
                        "--data-urlencode", f"text={text}"], capture_output=True, text=True)
    ok = '"ok":true' in r.stdout
    log(("sent: " if ok else "SEND FAILED: ") + text.replace("\n", " | ")[:120])
    return ok


def depot_has_position(depot):
    """True if depot/positions.md has a row with a WKN for the depot under 'Open positions'."""
    try:
        text = io.open(POSITIONS, encoding="utf-8").read()
    except FileNotFoundError:
        return False
    block = text.split("## Open positions", 1)[-1].split("## ", 1)[0]
    for line in block.splitlines():
        if not line.strip().startswith("|"):
            continue
        z = [c.strip() for c in line.strip().strip("|").split("|")]
        if not any(z) or z[0] == "Depot" or all(not c or set(c) <= set("-: ") for c in z):
            continue
        if len(z) >= 9 and re.fullmatch(r"[A-Z0-9]{6}", z[1]) and z[0].upper().endswith(depot.upper()):
            return True
    return False


def quote_sg(k):
    """Underlying from the SG calls, ask/bid/barrier of the product. Raises on failure."""
    import sg_products as sg
    calls = sg.products(k["asset"], 47, 0)
    puts = sg.products(k["asset"], 47, 1)
    s_c, fx_c, s_p, fx_p = sg.implied_spot(calls, puts)
    S = (s_c + s_p) / 2 if (s_c and s_p) else (s_c or s_p)
    if not S:
        raise RuntimeError("SG: underlying price cannot be derived")
    px = calls if k.get("direction", "call") == "call" else puts
    product = next((p for p in px if p.get("Code") == k["wkn"]), None)
    return dict(S=S, fx=fx_c or fx_p or FX_FALLBACK,
                ask=(product or {}).get("Offer") or None, bid=(product or {}).get("Bid") or None,
                barrier=(product or {}).get("BarrierTurboCertificate") or (product or {}).get("Strike") or None,
                source="SG")


def quote_yahoo():
    req = urllib.request.Request("https://query1.finance.yahoo.com/v8/finance/chart/BZ=F?range=1d&interval=15m",
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.load(r)
    return float(d["chart"]["result"][0]["meta"]["regularMarketPrice"])


def load_state(path_in=None):
    """State of the last report: file from --state-in (Actions cache), otherwise local."""
    for path in (path_in, STATE_LOCAL):
        if not path:
            continue
        try:
            return json.load(io.open(path, encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return {}


def save_state(st, path_out):
    """Writes the state; next to it a marker <path>.new, so the workflow only creates a
    new cache entry when a report was actually sent."""
    path = path_out or STATE_LOCAL
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    io.open(path, "w", encoding="utf-8").write(json.dumps(st))
    if path_out:
        io.open(path_out + ".new", "w").write("1")


def order_size(stake, limit):
    """The platform counts the fee towards the EUR 20,000 cap (rejection on 7 Sep 2026); round tens."""
    n = math.floor((min(stake, 20_000.0) - FEE) / limit)
    n = min(20_000, n // 10 * 10)
    return n, n * limit


def message(k, quote, now, estimated):
    call = k.get("direction", "call") == "call"
    S = quote["S"]
    barrier = quote.get("barrier") or k["barrier"]
    if quote.get("ask"):
        ask = quote["ask"]
    else:
        ask = round(((S - barrier) if call else (barrier - S)) * quote.get("fx", FX_FALLBACK) + 0.02, 2)
        estimated = True
    hint = ""
    if estimated:
        hint = " (estimated from Brent and barrier)" if quote.get("source") == "SG" else " (estimated, SG unreachable)"
    limit = round(ask + k.get("markup", 0.05), 2)
    n, eur = order_size(k.get("stake", 20_000), limit)
    dist = (S - barrier) / S if call else (barrier - S) / S
    # Messages use the platform's names: Depot 1 for Depot A, Depot 2 for Depot B.
    name = "Depot " + ("1" if k.get("depot", "A").upper().endswith("A") else "2")
    lines = [
        f"BUY {name}: buy alert {k.get('name', 'Brent')} {'long' if call else 'short'}",
        f"{k.get('name', 'Brent')} ${num(S)} (trigger ${num(k['trigger'])}), {now.day} {now:%b %H:%M} Berlin",
        f"WKN {k['wkn']} · limit €{num(limit)} · {num(n, 0)} units · valid for the day",
        f"Ask €{num(ask)}{hint}, "
        f"barrier {num(barrier)} = {num(dist*100, 1)}% distance, stake €{num(eur, 0)} + 3.90",
        "Check first: if the drop comes from a deal headline or news of Hormuz reopening, do not buy.",
        "Report back after buying; the position then gets recorded and the alert goes quiet.",
    ]
    if k.get("note"):
        lines.append(k["note"])
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Brent buy alert via Telegram (no order, no account access)")
    ap.add_argument("--test", action="store_true", help="print instead of sending, do not write the state")
    ap.add_argument("--probe", type=float, help="pretend Brent is at this price")
    ap.add_argument("--probe-trigger", action="store_true", help="pretend Brent is just past the trigger")
    ap.add_argument("--state-in", help="read the state from this file (GitHub Actions, from the cache)")
    ap.add_argument("--state-out", help="write the new state to this file (GitHub Actions)")
    ap.add_argument("--ignore-time", action="store_true", help="run outside 8:00-21:45 Mon-Fri as well")
    ap.add_argument("--activation", action="store_true", help="send a one-off start message (checks secrets and Telegram)")
    a = ap.parse_args()
    now = dt.datetime.now(TZ)

    try:
        k = json.load(io.open(CONFIG, encoding="utf-8"))
    except FileNotFoundError:
        log("no depot/buy_alert.json, nothing to do"); return
    if k.get("valid_until") and now.date() > dt.date.fromisoformat(k["valid_until"]):
        log(f"buy alert expired ({k['valid_until']}), nothing to do"); return
    if not a.ignore_time and not a.probe and not a.probe_trigger and not a.activation:
        if now.weekday() >= 5 or not (8 <= now.hour < 22) or (now.hour == 21 and now.minute > 45):
            log("outside 8:00-21:45 Mon-Fri Berlin, nothing to do"); return
    depot = k.get("depot", "A")
    if a.activation:
        try:
            S = quote_sg(k)["S"]
        except Exception:
            S = None
        call = k.get("direction", "call") == "call"
        valid_until = dt.date.fromisoformat(k["valid_until"])
        send_telegram(f"Buy alert active: {k.get('name', 'Brent')} {'long' if call else 'short'}, "
                      f"trigger ${num(k['trigger'])}, WKN {k['wkn']}, stake €{num(min(k.get('stake', 20_000), 20_000), 0)}. "
                      f"Checks every 15 min Mon–Fri 8:00–21:45 Berlin until {valid_until.day} {valid_until:%b} "
                      f"and then reports WKN, limit and units. {k.get('name', 'Brent')} now {'$' + num(S) if S else 'without a price'}.", a.test)
        return
    if depot_has_position(depot):
        log(f"Depot {depot} has a position per positions.md, alert resting"); return

    call = k.get("direction", "call") == "call"
    estimated = False
    try:
        quote = quote_sg(k)
    except Exception as e:
        log(f"SG unreachable ({type(e).__name__}: {e}), Yahoo as fallback")
        try:
            quote = dict(S=quote_yahoo(), fx=FX_FALLBACK, ask=None, bid=None, barrier=None, source="Yahoo")
        except Exception as e2:
            log(f"Yahoo has no price either ({type(e2).__name__}), run ends"); return
        estimated = True
    if a.probe is not None:
        quote["S"] = a.probe; quote["ask"] = None
    elif a.probe_trigger:
        quote["S"] = k["trigger"] - 0.05 if call else k["trigger"] + 0.05; quote["ask"] = None
    S = quote["S"]
    reached = S <= k["trigger"] if call else S >= k["trigger"]
    log(f"{k.get('name', 'Brent')} {S:.2f} ({quote['source']}), trigger {k['trigger']}, "
        f"ask {k['wkn']} {quote.get('ask') or '?'}, {'REACHED' if reached else 'not reached'}")
    if not reached:
        return

    st = load_state(a.state_in)
    today = now.strftime("%Y-%m-%d")
    count = st.get("count", 0) if st.get("date") == today else 0
    since = now.timestamp() - st.get("epoch", 0)
    further = (st.get("brent") is not None and st.get("date") == today
               and ((S <= st["brent"] - 0.75) if call else (S >= st["brent"] + 0.75)))
    if count >= k.get("max_per_day", 3):
        log(f"already {count} reports today, limit reached"); return
    if count and since < k.get("repeat_min", 120) * 60 and not further:
        log(f"last report {since/60:.0f} min ago, no repeat yet"); return

    text = message(k, quote, now, estimated)
    if send_telegram(text, a.test) and not a.test:
        save_state({"date": today, "epoch": now.timestamp(), "brent": S, "count": count + 1}, a.state_out)


if __name__ == "__main__":
    main()

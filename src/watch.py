"""
The Watch: looks every 15 minutes and writes only when something happened.

No account access, no orders: it observes and reports. It runs under launchd on
the player's own machine (template in ops/launchd/), needs only curl and .env,
and sends through a private Telegram bot.

Triggers, each reported once, quiet hours 22:00–8:00 Berlin time:
  1. A headline with a Hormuz/Iran word AND an action word (deal, reopening,
     blockade, attack, Kharg ...) from the feeds in situation.py
  2. Polymarket "Hormuz traffic normal by 31 Oct" moves by >= 5 points since
     the last alert
  3. Brent is >= 3 % above/below its price at the last alert, or moves
     >= 1.5 % within 60 minutes
  4. A position in depot/positions.md broke its knock-out barrier (low/high
     since the last run counts), or is less than 1 % away from it
  5. Friday from 21:30: CFTC COT, when Managed Money in Brent or gold flips
     sign or moves by more than a fifth
Scheduled reminders: Friday 21:00 close the weekly leg (Depot B), Monday renew
limit orders, weekdays 21:00 the daily report plus the regime check.

On the very first run it only stores the state and reports "Watch active".

Usage:    python3 src/watch.py           # one look, alert if needed
          python3 src/watch.py --test    # look without sending, shows what would go out
          python3 src/watch.py --status  # stored state
"""

import argparse
import datetime as dt
import io
import json
import os
import re
import shutil
import subprocess
import sys
import zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data")
sys.path.insert(0, HERE)
from situation import FEEDS, BROWSER_UA, fetch, feed_entries, quote_cnbc, load_json, write_json  # noqa: E402
import sources  # noqa: E402

STATE = os.path.join(DATA, "watch_state.json")
LOG = os.path.join(DATA, "watch.log")
TZ = zoneinfo.ZoneInfo("Europe/Berlin")


def _claude_path():
    """launchd starts with a minimal PATH; so first PATH, then the usual
    install locations. If all of them fail, the bare name stays, and the call
    logs FileNotFoundError instead of failing silently."""
    candidates = [shutil.which("claude"),
                  os.path.expanduser("~/.local/bin/claude"),
                  "/opt/homebrew/bin/claude", "/usr/local/bin/claude"]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return "claude"


CLAUDE = _claude_path()

# Gold and silver as SPOT (XAU=, XAG=), not as COMEX futures (@GC.1, @SI.1):
# the SG turbos are on XAUUSD. On 7 Sep 2026 the future was 1.1 % above spot
# (4,444 vs 4,395); against a barrier at 4,450 that would have been a false knock-out.
PRICES = {"Brent": "@LCO.1", "WTI": "@CL.1", "Gold": "XAU=", "Silver": "XAG=", "DAX": ".GDAXI"}
PLACE_RE = re.compile(r"hormuz|iran|kharg|strait of|persian gulf|gulf of oman|tehran|houthi|trump|white house", re.I)
# 17 Sep: Trump's peace signal slipped through the filter, hence peace, negotiat,
# end of the war, envoy.
ACTION_RE = re.compile(r"deal|agreement|accord|reopen|open(ing|s|ed)?\b|blockade|attack|strike|missile|"
                       r"drone|tanker|ceasefire|truce|talks|sanction|closure|mine|peace|negotiat|"
                       r"end (of )?the war|envoy", re.I)
PM_TITLE = "Strait of Hormuz traffic returns to normal by October 31?"
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def short_date(t, with_time=True):
    """'7 Sep 14:30' (or '7 Sep'), independent of the locale."""
    s = f"{t.day} {MONTHS[t.month - 1]}"
    return f"{s} {t:%H:%M}" if with_time else s


def log(s):
    os.makedirs(DATA, exist_ok=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{dt.datetime.now(TZ):%Y-%m-%d %H:%M} {s}\n")


def load_state():
    return load_json(STATE)


def save_state(st):
    write_json(STATE, st, indent=1)


def load_env():
    out = {}
    try:
        for line in io.open(os.path.join(REPO, ".env"), encoding="utf-8"):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                out[k] = v
    except FileNotFoundError:
        pass
    return out


def send_telegram(text, test=False):
    if test:
        print("--- WOULD SEND ---\n" + text + "\n---")
        return True
    e = load_env()
    if not e.get("TELEGRAM_BOT_TOKEN") or not e.get("TELEGRAM_CHAT_ID"):
        log("Telegram not configured"); return False
    r = subprocess.run(["curl", "-sS", "-m", "20", "-X", "POST",
                        f"https://api.telegram.org/bot{e['TELEGRAM_BOT_TOKEN']}/sendMessage",
                        "--data-urlencode", f"chat_id={e['TELEGRAM_CHAT_ID']}",
                        "--data-urlencode", f"text={text}"], capture_output=True, text=True)
    ok = '"ok":true' in r.stdout
    log(("sent: " if ok else "SEND FAILED: ") + text.replace("\n", " | ")[:160])
    return ok


def read_section(rel, start=None, end=None, limit=6000):
    """Part of a repo file between two markers (case-insensitive). A missing
    start marker keeps the whole text, a missing end marker everything after
    the start. A missing file gives ""."""
    try:
        t = io.open(os.path.join(REPO, rel), encoding="utf-8").read()
    except FileNotFoundError:
        return ""
    if start:
        m = re.search(re.escape(start), t, re.I)
        if m:
            t = t[m.end():]
    if end:
        m = re.search(re.escape(end), t, re.I)
        if m:
            t = t[:m.start()]
    return t.strip()[:limit]


# ---- Message to the player -------------------------------------------------

# Prefixes of the Watch's own calls to action; they always reach the player.
ACTIONS = ("KNOCK-OUT", "CLOSE WEEKLY LEG", "LIMIT ORDERS", "BRENT FAST", "NEAR BARRIER")
BUY_RE = re.compile(r"\bBUY\b")   # a morning card that actually says buy


def _depot_name(t):
    """The player reads Depot 1/2 on the game platform; internally they are A/B."""
    return re.sub(r"\bDepot ([AB])\b", lambda m: "Depot " + ("1" if m.group(1) == "A" else "2"), t)


def log_full(text):
    """The long version (headlines, council rounds, evidence tiers) stays readable in data/."""
    try:
        os.makedirs(DATA, exist_ok=True)
        with io.open(os.path.join(DATA, "watch_full.log"), "a", encoding="utf-8") as f:
            f.write(text.rstrip() + "\n\n" + "-" * 60 + "\n\n")
    except Exception as e:
        log(f"full log: {type(e).__name__}")


def for_player(header, now, assessment, alerts):
    """Short version for Telegram (the player's feedback of 7 Sep 2026): first
    what it means for the portfolios, then what to do, then one sentence why.
    No council rounds, no evidence tiers, no headline list; those are in
    data/watch_full.log. The Watch's own calls to action (knock-out, weekly
    leg, limit orders, order card) stay in."""
    fields = {}
    for z in (assessment or "").splitlines():
        m = re.match(r"^(WHAT|DEPOTS|ACTION):\s*(.*)$", z)
        if m and m.group(2).strip():
            fields[m.group(1)] = m.group(2).strip()
    lines = [f"{header} {short_date(now)}".strip()]
    if fields.get("DEPOTS"):
        lines.append(fields["DEPOTS"][:300])
    h = fields.get("ACTION", "")
    if h and h.lower().rstrip(".") != "none":
        lines.append("To do: " + h[:300])
    elif fields:
        lines.append("To do: nothing.")
    if fields.get("WHAT"):
        lines.append("Why: " + fields["WHAT"][:250])
    actions = [m for m in alerts if m.startswith(ACTIONS) or BUY_RE.search(m)]
    lines.extend(a[:400] for a in actions)
    if not fields and not actions:
        first = (alerts[0] if alerts else "").replace("HEADLINES\n", "")
        lines.append("Assessment failed (see data/watch.log). Trigger: " + first[:250])
    return _depot_name("\n\n".join(lines))


# ---- Sources ---------------------------------------------------------------

def headlines():
    out = []
    for name, url, ua in FEEDS:
        try:
            for title, date in feed_entries(fetch(url, ua, timeout=12), 40):
                if PLACE_RE.search(title) and ACTION_RE.search(title):
                    out.append((f"{name}|S{sources.tier(name)}", title))
        except Exception as e:
            log(f"Feed {name}: {type(e).__name__}")
    return out


def polymarket():
    try:
        raw = fetch("https://gamma-api.polymarket.com/public-search?q=hormuz&limit_per_type=20", BROWSER_UA)
        d = json.loads(raw)
        for ev in d.get("events") or []:
            if ev.get("title") == PM_TITLE:
                m = (ev.get("markets") or [])[0]
                op = m.get("outcomePrices")
                op = json.loads(op) if isinstance(op, str) else op
                return float(op[0]) * 100
    except Exception as e:
        log(f"Polymarket: {type(e).__name__}")
    return None


YAHOO = {"Brent": "BZ=F", "WTI": "CL=F", "Gold": "GC=F", "Silver": "SI=F", "DAX": "%5EGDAXI"}


def extremes_since(name, since_epoch):
    """Low and high of the underlying since `since_epoch`, from Yahoo 5-minute candles.

    Reason (16 Sep 2026): at 17:30 Brent broke the barrier 104.74 for a few
    minutes (low 104.06) and was back at 105.7 by the next 15-minute run; the
    Watch saw only the current price and never reported the knock-out. Returns
    (None, None) if Yahoo does not answer; then only the current price counts,
    as before."""
    sym = YAHOO.get(name)
    if not sym or not since_epoch:
        return None, None
    try:
        # With the full browser UA Yahoo answers "Too Many Requests", with the short one it does not (17 Sep 2026)
        d = json.loads(fetch(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1d&interval=5m", "Mozilla/5.0", timeout=12))
        r = d["chart"]["result"][0]
        q = r["indicators"]["quote"][0]
        lows = [l for ts, l in zip(r["timestamp"], q["low"]) if l and ts >= since_epoch - 300]
        highs = [h for ts, h in zip(r["timestamp"], q["high"]) if h and ts >= since_epoch - 300]
        return (min(lows) if lows else None, max(highs) if highs else None)
    except Exception as e:
        log(f"Yahoo extremes {name}: {type(e).__name__}")
        return None, None


EN_NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")


def parse_en_number(cell):
    """First number in a table cell, English format only ("4,390.25", "98.04").
    German format ("4.390,25", "98,04") gives None instead of a wrong value."""
    m = re.search(r"\d[\d.,]*", cell or "")
    if not m:
        return None
    token = m.group(0).rstrip(".,")
    if not EN_NUMBER.fullmatch(token):
        return None
    return float(token.replace(",", ""))


def open_positions(text=None):
    """Open positions from depot/positions.md: (depot, WKN, underlying, direction, barrier).

    A filled-in row that cannot be read is logged instead of silently skipped;
    otherwise a knock-out goes unnoticed because a column had shifted. `text`
    is for the tests."""
    out = []
    if text is None:
        try:
            text = io.open(os.path.join(REPO, "depot", "positions.md"), encoding="utf-8").read()
        except FileNotFoundError:
            return out
    block = text.split("## Open positions", 1)[-1].split("## ", 1)[0]
    for line in block.splitlines():
        if not line.strip().startswith("|"):
            continue
        z = [c.strip() for c in line.strip().strip("|").split("|")]
        if not any(z) or z[0] == "Depot" or all(not c or set(c) <= set("-: ") for c in z):
            continue  # empty template row, header, separator
        if len(z) < 9 or not z[1]:
            log(f"positions.md: row not readable (expected 9 columns, WKN in column 2): {line.strip()[:90]}")
            continue
        depot, wkn, product, underlying, barrier_cell = z[0], z[1], z[2], z[3], z[8]
        barrier = parse_en_number(barrier_cell)
        if barrier is None:
            log(f"positions.md: barrier not readable for {wkn} (English number format expected): {barrier_cell!r}")
            continue
        direction = "short" if re.search(r"put|short", product + " " + depot, re.I) else "long"
        name = next((k for k in PRICES if k.lower() in underlying.lower()), None)
        if name:
            out.append((depot, wkn, name, direction, barrier))
        else:
            log(f"positions.md: underlying {underlying!r} for {wkn} unknown, known: {', '.join(PRICES)}")
    return out


def cot():
    """Managed Money net for Brent and gold from the current COT report."""
    try:
        txt = fetch("https://www.cftc.gov/dea/newcot/f_disagg.txt", BROWSER_UA)
    except Exception as e:
        log(f"COT: {type(e).__name__}"); return None
    out = {}
    for line in txt.splitlines():
        if "BRENT LAST DAY" in line or "GOLD - COMMODITY EXCHANGE" in line:
            r = [c.strip().strip('"') for c in line.split(",")]
            try:
                name = "Brent" if "BRENT" in line else "Gold"
                out[name] = dict(date=r[2], net=int(r[10]) - int(r[11]))
            except Exception:
                pass
    return out or None


def replacement_card(depot):
    """After a knock-out, send the replacement order right away instead of
    waiting for the next 8:05 card (the player, 7 Sep 2026: act directly after
    a knock-out). morning_card.py imports from watch, so this runs it as a
    subprocess instead of importing it."""
    d = depot.strip().upper()[-1]
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "morning_card.py"), "--depot", d, "--text-only"],
                           capture_output=True, text=True, timeout=240, cwd=REPO)
        if r.returncode == 0 and r.stdout.strip():
            return f"REPLACEMENT ORDER DEPOT {d}\n" + r.stdout.strip()
        log(f"replacement order {d}: rc={r.returncode} {r.stderr.strip()[-160:]!r}")
    except Exception as e:
        log(f"replacement order {d}: {type(e).__name__} {e}")
    return f"REPLACEMENT ORDER DEPOT {d}: could not be determined; run python3 src/morning_card.py --depot {d} --text-only"


# ---- Assessment by Claude (headless) ---------------------------------------

def assess(alerts, prices, p_hormuz, brent_delta="?"):
    """Calls `claude -p` and has the alert assessed against positions and
    abort conditions. Only Read is allowed, no search: the context is passed
    in, the answer comes in seconds. No account access, no order: the result
    is text for the player."""
    pos = read_section("depot/positions.md", "## Open positions", "## Resting sell orders", 100000) or "(no file)"
    thesis = read_section("strategy/00-thesis.md", "## Abort conditions", "\n## ", 100000)
    themes = read_section("strategy/40-themes.md", "**Triggers for immediate action:**", "## 2.", 100000)
    if themes:
        thesis += "\n\nTRIGGERS FOR IMMEDIATE ACTION (40-themes.md):\n" + themes
    try:
        cot_txt = ", ".join(f"{k} Managed Money net {v['net']:+,} ({v['date']})" for k, v in (load_state().get("cot") or {}).items())
    except Exception:
        cot_txt = "?"
    dossier = read_section("strategy/70-hormuz-dossier.md", "## Summary", "## Chronology") + "\n\n" + \
        read_section("strategy/70-hormuz-dossier.md", "## What prices said", "## Actors")
    prompt = f"""You are the assessment step of the Watch for Trader 2026. You do not place orders; the player trades by hand.

MEMORY (strategy/70-hormuz-dossier.md, as of 6 Sep):
{dossier}

ALERT:
{chr(10).join(alerts)}

PRICES: {', '.join(f'{k} {v:.2f}' for k, v in prices.items())}
BRENT since the last look (15 min): {brent_delta}
POLYMARKET Hormuz normal by 31 Oct: {p_hormuz if p_hormuz is not None else '?'} %
COT: {cot_txt or '?'}

OPEN POSITIONS (empty = the standing order card applies: Depot A Brent long, Depot B Brent short):
{pos}

ABORT CONDITIONS:
{thesis}

{sources.rule_text()}

Rate the SIGNAL, evidence-based, from four building blocks:
1. Sources: how many independent sources report THE SAME EVENT (an act, not an opinion)? 1 = weak, 2 = medium, 3+ = strong.
2. Office: does an official speak to the catalyst (president, foreign minister, Oman, Fed, OPEC)? Raises one level.
3. Market: do Polymarket and Brent move in the same direction as the alert? Yes raises one level, no lowers one level.
4. Positioning: a COT extreme in the alert's direction (e.g. Brent one-sidedly long on an escalation alert) lowers one level, because the consensus is already priced in. The deduction does not apply to a supply loss or return (strait, blockade, Kharg, mines, Bab el-Mandeb): on 28 Feb and 8 Jul the funds were long as well, and Brent still rose 47–70 %.
Rhetoric without an act (threat, warning, expectation, commentary) is at most "weak", no matter who speaks. Only an act (attack, signature, lifting, transit, decision) can be "medium" or "strong".
Size for Brent, from the comparison cases in memory: incidents without a supply effect, +3 to +13 % on the day and back within 20 days = small/medium; supply loss or return (strait closed/open, blockade on/off, Kharg, mines in the corridor) = large. "Agreement reported" counts only with signature AND implementation; "close to a deal" is rhetoric. Name the nearest comparison case with its number in WHAT.
Measured in the repo: gold trends persist (with the trend 25 % survival, against it 6.6 %), oil trends are neutral over 39 years.
Instrument per strategy/20-instruments.md: turbo at high volatility (oil), warrant at low volatility (stocks, VIX below 20), warrant if the scheduled event falls after 22:00.

Answer in English, exactly five lines, no introduction, no filler words, never invent a number:
SIGNAL: <strong|medium|weak> <long|short|neutral> <underlying> (<building blocks as keywords, e.g. 2 sources, office yes, market yes, COT against>)
WHAT: <one sentence: event or rhetoric>
DEPOTS: A <effect> | B <effect>
ABORT: <no | YES: condition> (<source tier S1/S2 | only S3/S4>)
ACTION: <none | check: what | buy: instrument direction underlying, distance, then sg_products.py for the WKN | close: depot>"""
    # launchd does not know ~/.local/bin: pass the absolute path and PATH.
    environment = dict(os.environ, PATH=os.path.dirname(CLAUDE) + ":" + os.environ.get("PATH", "/usr/bin:/bin"))
    for model in ("sonnet", "opus"):
        try:
            r = subprocess.run([CLAUDE, "-p", "--model", model, "--allowedTools", "Read"],
                               input=prompt, capture_output=True, text=True, timeout=150, cwd=REPO, env=environment)
            text = r.stdout.strip()
            if r.returncode == 0 and text.startswith("SIGNAL"):
                return text
            log(f"assessment {model} unusable: rc={r.returncode} {text[:80]!r} {r.stderr[:80]!r}")
        except Exception as e:
            log(f"assessment {model}: {type(e).__name__} {e}")
    return None


def consult_or_assess(alerts, prices, p_hormuz, delta):
    """The Council (src/council.py) checks every alert with five specialist
    agents before it reaches the player (the player's instruction of 7 Sep 2026). If the Council
    fails, the simple assessment decides, and it may then only trigger 'check'."""
    try:
        import council
        text = council.deliberate(alerts, prices, p_hormuz, delta)
        if text and text.startswith("SIGNAL"):
            return text
        log("Council: no result, assessment as fallback")
    except Exception as e:
        log(f"Council: {type(e).__name__} {e}; assessment as fallback")
    result = assess(alerts, prices, p_hormuz, delta)
    if result:
        result = re.sub(r"^ACTION: *(buy|close)", r"ACTION: check (without council): \1", result, flags=re.M)
        result += "\nEVIDENCED: no (without council)"
    return result


def _action_body(line):
    """The ACTION line without its label, lower-case."""
    return re.sub(r"^action:\s*", "", (line or "").strip().lower())


def wants_action(line, include_act=True):
    """True if an ACTION line asks to buy or close (or, with include_act, to act)."""
    words = r"close|buy|act" if include_act else r"close|buy"
    return bool(re.search(r"\b(" + words + r")\b", _action_body(line)))


def wants_check(line):
    return bool(re.search(r"\bcheck\b", _action_body(line)))


def acquire_lock():
    """One run at a time: the Council can take minutes, launchd starts every 15."""
    import fcntl
    os.makedirs(DATA, exist_ok=True)
    f = io.open(os.path.join(DATA, "watch.lock"), "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except OSError:
        return None


# ---- Main run --------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="The Watch: one look at prices, headlines and positions; alerts via Telegram.")
    ap.add_argument("--test", action="store_true", help="look without sending and without saving state")
    ap.add_argument("--status", action="store_true", help="print the stored state")
    ap.add_argument("--ignore-quiet-hours", action="store_true", help="also run between 22:00 and 8:00")
    ap.add_argument("--probe", help="inject a headline to test the alert and the assessment")
    a = ap.parse_args()
    st = load_state()
    if a.status:
        print(json.dumps(st, indent=1, ensure_ascii=False)); return
    lock = acquire_lock()
    if lock is None:
        log("run skipped: the previous run (Council) is still going"); return
    now = dt.datetime.now(TZ)
    if not a.ignore_quiet_hours and not (8 <= now.hour < 22):
        log("quiet hours"); return
    first = not st and not a.probe
    alerts = []

    # Prices
    prices = {}
    for name, sym in PRICES.items():
        k = quote_cnbc(sym)
        if k:
            prices[name] = k[1]
    brent = prices.get("Brent")
    if brent:
        ref = st.get("brent_alerted")
        if ref and abs(brent / ref - 1) >= 0.03:
            alerts.append(f"BRENT {brent:.2f} $: {brent/ref-1:+.1%} since the last alert ({ref:.2f}).")
            st["brent_alerted"] = brent
        if not ref:
            st["brent_alerted"] = brent
        # Fast move (17 Sep 2026, the player: "oil is falling heavily"): >= 1.5 % within
        # 60 minutes alerts at once, even if the 3 % since the last alert are not reached.
        history = [v for v in st.get("brent_history", []) if now.timestamp() - v[0] <= 3 * 3600]
        history.append([now.timestamp(), brent])
        st["brent_history"] = history
        one_hour_ago = [v for v in history if 45 * 60 <= now.timestamp() - v[0] <= 75 * 60]
        if one_hour_ago:
            old = one_hour_ago[0][1]
            move = brent / old - 1
            last = st.get("fast_alerted", [0, 0])
            if abs(move) >= 0.015 and (now.timestamp() - last[0] >= 3600 or (move > 0) != (last[1] > 0)):
                pos_lines = []
                for depot, wkn, name, direction, barrier in open_positions():
                    if name == "Brent" and wkn not in st.get("ko_alerted", []):
                        dist = (brent - barrier) / brent if direction == "long" else (barrier - brent) / brent
                        toward = (move < 0) == (direction == "long")
                        pos_lines.append(f"{depot} {wkn} ({direction}, barrier {barrier:.2f}) still {dist:.1%} away, "
                                         f"moving {'toward the barrier' if toward else 'away from the barrier'}")
                alerts.append(f"BRENT FAST: {brent:.2f} $, {move:+.1%} in one hour (from {old:.2f}). "
                              + ("; ".join(pos_lines) + "." if pos_lines else "No Brent position open."))
                st["fast_alerted"] = [now.timestamp(), move]

    # Headlines
    seen = set(st.get("headlines", []))
    new = []
    for source, title in headlines():
        key = re.sub(r"\W+", " ", title.lower()).strip()[:120]
        if key not in seen:
            seen.add(key)
            if not first:
                new.append(f"[{source}] {title}")
    st["headlines"] = sorted(seen)[-400:]
    if a.probe:
        new.append(a.probe)
    if new:
        alerts.append("HEADLINES\n" + "\n".join("• " + n for n in new[:6]))

    # Polymarket
    p = polymarket()
    if p is not None:
        ref = st.get("pm_alerted")
        if ref is not None and abs(p - ref) >= 5:
            alerts.append(f"POLYMARKET Hormuz normal by 31 Oct: {p:.1f} % (before {ref:.1f} %).")
            st["pm_alerted"] = p
        if ref is None:
            st["pm_alerted"] = p

    # Knock-outs
    ko_alerted = set(st.get("ko_alerted", []))
    near_alerted = st.get("near_alerted", {})
    since = st.get("last_run_epoch")
    extremes = {}
    for depot, wkn, name, direction, barrier in open_positions():
        k = prices.get(name)
        if k is None or wkn in ko_alerted:
            continue
        if name not in extremes:
            extremes[name] = extremes_since(name, since)
        low, high = extremes[name]
        # Low/high since the last run counts, not just the price now (16 Sep 2026, FG6MRT)
        checked = min(k, low) if (direction == "long" and low) else (max(k, high) if (direction == "short" and high) else k)
        broken = (checked <= barrier) if direction == "long" else (checked >= barrier)
        if broken:
            alerts.append(f"KNOCK-OUT {depot} {wkn} ({name} {direction}): {'low' if direction == 'long' else 'high'} since the last run {checked:.2f}, "
                          f"barrier {barrier:.2f}, price now {k:.2f}. Per the thesis, re-enter at once; update depot/positions.md.")
            ko_alerted.add(wkn)
            alerts.append(replacement_card(depot))
            continue
        # Close to the barrier: below 1 %, alert once per hour so the player sees the slide
        distance = (k - barrier) / k if direction == "long" else (barrier - k) / k
        if distance < 0.01 and (now.timestamp() - near_alerted.get(wkn, 0)) >= 3600:
            alerts.append(f"NEAR BARRIER: {depot} {wkn} ({name} {direction}, barrier {barrier:.2f}): price {k:.2f}, "
                          f"only {distance:.1%} away. Nothing to do, a turbo is not sold before it knocks out, "
                          f"but the replacement order is ready.")
            near_alerted[wkn] = now.timestamp()
    st["ko_alerted"] = sorted(ko_alerted)
    st["near_alerted"] = near_alerted

    # COT on Fridays from 21:30, at weekends, or if never read
    if (now.weekday() == 4 and now.hour >= 21 and now.minute >= 30) or now.weekday() in (5, 6) or "cot" not in st:
        c = cot()
        if c:
            old = st.get("cot", {})
            lines = []
            for name, v in c.items():
                if name in old and old[name]["date"] != v["date"]:
                    a0, a1 = old[name]["net"], v["net"]
                    if (a0 * a1 < 0) or (a0 and abs(a1 - a0) / abs(a0) > 0.20):
                        lines.append(f"{name}: Managed Money net {a1:+,} (before {a0:+,}), as of {v['date']}")
            if lines:
                alerts.append("COT\n" + "\n".join("• " + z for z in lines))
            st["cot"] = c

    # Depot A empty (no call was available): check hourly whether SG now offers
    # a Brent call within 1.5 %. Only A, the main-prize leg.
    if now.minute < 15 and 8 <= now.hour < 22:
        live = {d.strip().upper()[-1] for d, wkn, *_ in open_positions() if wkn not in ko_alerted}
        if "A" not in live and st.get("a_card_hour") != now.strftime("%Y-%m-%d %H"):
            card = replacement_card("A")
            if BUY_RE.search(card):
                alerts.append(card)
            st["a_card_hour"] = now.strftime("%Y-%m-%d %H")

    # Fridays 21:00-21:30, once: the weekly leg (Depot B, 2 %) is closed and set up
    # again on Monday; measured in strategy/92-sideways.md (weekly pair Mon 9:00 to Fri 21:45).
    if now.weekday() == 4 and now.hour == 21 and now.minute < 30 and st.get("friday_reminded") != now.strftime("%Y-%m-%d"):
        live_b = [(wkn, name, r, b) for d, wkn, name, r, b in open_positions() if d.strip().upper()[-1] == "B" and wkn not in ko_alerted]
        if live_b:
            wkn, name, r, b = live_b[0]
            k = prices.get(name)
            alerts.append(f"CLOSE WEEKLY LEG: Depot B {wkn} ({name} {r}, barrier {b:.2f}, price {k if k else '?'}): sell now at market, "
                          f"the proceeds stay cash. The new card comes Monday 8:05 (2 % distance). Then delete row B in depot/positions.md.")
        st["friday_reminded"] = now.strftime("%Y-%m-%d")

    # Mondays, once: limit orders expire after 7 days
    if now.weekday() == 0 and st.get("limit_reminded") != now.strftime("%Y-%m-%d") and open_positions():
        alerts.append("LIMIT ORDERS: 7-day validity; renew today for every live position (67.5 x ask).")
        st["limit_reminded"] = now.strftime("%Y-%m-%d")

    # SG bid prices of open positions into the cache every hour (daily_report.with_cache),
    # so the report can still compute when SG no longer quotes in the evening.
    if now.minute < 15 and 8 <= now.hour < 21 and open_positions():
        try:
            import daily_report
            daily_report.fetch_sg_quotes(daily_report.read_positions()["positions"], now)
        except Exception as e:
            log(f"SG quote cache: {type(e).__name__} {e}")

    # Daily report (src/daily_report.py) and regime check (src/regime.py): once on weekdays
    # in the 21:00-21:14 run. SG trades until 22:00 but stops quoting through the API from
    # about 21:30 (7 Sep 2026). The daily report always goes out; the regime check is
    # appended when it has something to say (Fridays, level changes).
    if now.weekday() < 5 and now.hour == 21 and now.minute < 15 and st.get("regime_day") != now.strftime("%Y-%m-%d"):
        parts = []
        try:
            import daily_report
            report_text, _ = daily_report.build(now, write=not a.test)
            parts.append(report_text)
        except Exception as e:
            log(f"daily report: {type(e).__name__} {e}")
            parts.append(f"Daily state {short_date(now, with_time=False)}: could not be computed ({type(e).__name__}), see data/watch.log.")
        try:
            import regime
            regime_text, _ = regime.daily(now.date(), send=not a.test, brent_today=brent)
            if regime_text:
                parts.append(regime_text)
        except Exception as e:
            log(f"regime check: {type(e).__name__} {e}")
        send_telegram("\n\n".join(parts), a.test)
        st["regime_day"] = now.strftime("%Y-%m-%d")

    # Send
    st["last_run"] = now.strftime("%Y-%m-%d %H:%M")
    st["last_run_epoch"] = now.timestamp()
    if brent:
        st["brent_last_run"] = brent
    if first:
        text = (f"Watch active ({short_date(now)}). Brent {brent or '?'} $, Hormuz P {p if p is not None else '?'} %. "
                f"Alerts only on triggers.")
        send_telegram(text, a.test)
    elif alerts:
        full = f"{short_date(now)}\n" + "\n\n".join(alerts)
        before = st.get("brent_last_run")
        delta = f"{brent/before-1:+.2%} (from {before:.2f})" if (brent and before) else "no previous value"
        result = consult_or_assess(alerts, prices, p, delta)
        header = ""
        if result:
            action_line = next((z for z in result.splitlines() if z.startswith("ACTION")), "")
            act = wants_action(action_line)
            council_evidenced = "EVIDENCED: yes" in result
            if act and not (sources.may_trigger(alerts) or council_evidenced):
                # Gate (7 Sep 2026): tier-3/4 sources do not trigger an action.
                log(f"Gate: action on an S3/S4 source downgraded: {action_line[:80]!r}")
                header = "WATCH (source not yet confirmed)"
                result = re.sub(r"^ACTION: *", "ACTION: nothing yet, source unconfirmed. Under review: ", result, count=1, flags=re.M)
            elif act:
                header = "ALERT: ACT"
            elif wants_check(action_line):
                header = "WATCH"
            full += "\n\nASSESSMENT\n" + result
            try:
                sig = result.splitlines()[0].replace("SIGNAL:", "").strip()
                os.makedirs(DATA, exist_ok=True)
                with io.open(os.path.join(DATA, "signals.md"), "a", encoding="utf-8") as f:
                    f.write(f"| {now:%Y-%m-%d %H:%M} | {sig} | Brent {brent} | Hormuz P {p} | {alerts[0].splitlines()[-1][:90]} | Outcome 7d: |\n")
            except Exception as e:
                log(f"signal log: {type(e).__name__}")
        else:
            full += "\n\n(assessment failed; see data/watch.log)"
        log_full(full)
        text = for_player(header, now, result, alerts)
        send_telegram(text, a.test)
    else:
        log(f"quiet. Brent {brent} Hormuz P {p}")
    if not a.test:
        save_state(st)


if __name__ == "__main__":
    main()

# launchd: a LaunchAgent with StartInterval 900 and WorkingDirectory = repo root
# (template in ops/launchd/). Load: launchctl bootstrap gui/$(id -u) <plist>.
# Unload: launchctl bootout gui/$(id -u)/<label>.

"""
Regime check: is the market moving sideways, and are the gains good enough?

The player's request on 7 Sep 2026: track when the movement is too sideways and
the gains are too poor, with an assessment and an action.

Measures daily (called from the Watch after 21:30, once a day):
1. Brent weeks: net move and efficiency (net / sum of daily moves).
   Trigger from strategy/00-thesis.md and 92-sideways.md: two completed weeks
   in a row with efficiency < 0.25 and net < 5% -> Depot A to weekly mode
   (2% distance, close on Friday, new on Monday).
2. Depots: value from depot/positions.md (kept by the player), history in
   data/regime_state.json. The weekly result of the better depot against the
   measured benchmark of weekly mode (+12% median per week, 92-sideways.md
   section 4). From 12 Oct below EUR 300,000 -> write off the main prize (thesis).
3. Knock-outs in Depot A in a row (the log in positions.md): three -> weekly mode.

Writes one line per day to data/regime_log.md and reports via Telegram on
Fridays after the close and on every day the stage changes.
No access to the game account, no order.

    python3 src/regime.py --test          # computes, shows, does not send
    python3 src/regime.py --test --json
"""

import argparse
import datetime as dt
import io
import json
import os
import re
import sys
import zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from situation import fetch, load_json, write_json  # noqa: E402

TZ = zoneinfo.ZoneInfo("Europe/Berlin")
DATA = os.path.join(REPO, "data")
STATE = os.path.join(DATA, "regime_state.json")
LOG_FILE = os.path.join(DATA, "regime_log.md")
POSITIONS = os.path.join(REPO, "depot", "positions.md")
DAILY_STATE = os.path.join(DATA, "daily_state.json")

START = dt.date(2026, 9, 7)
END = dt.date(2026, 10, 30)
MAIN_PRIZE_CUTOFF = dt.date(2026, 10, 12)
MAIN_PRIZE_MINIMUM = 300_000
WINNING_MARK = 1_350_000
EFF_LIMIT = 0.25
NET_LIMIT = 0.05
WEEK_BENCHMARK = 0.12      # median depot week in weekly mode, 92-sideways.md section 4
KO_LIMIT = 3


# ---- Brent -----------------------------------------------------------------

UA = "Mozilla/5.0"   # the full browser User-Agent (situation.BROWSER_UA) gets HTTP 429 from Yahoo, the short one does not (7 Sep 2026)


def brent_days(range_="3mo"):
    """Daily Brent closes (Yahoo BZ=F) as a list of (date, close), oldest first."""
    raw = fetch(f"https://query1.finance.yahoo.com/v8/finance/chart/BZ=F?range={range_}&interval=1d", UA)
    if not raw.lstrip().startswith("{"):
        raise RuntimeError("Yahoo: " + raw.strip()[:40])
    d = json.loads(raw)["chart"]["result"][0]
    out = []
    for t, c in zip(d["timestamp"], d["indicators"]["quote"][0]["close"]):
        if c:
            out.append((dt.datetime.fromtimestamp(t, TZ).date(), float(c)))
    return out


def weeks(days):
    """Per ISO week: net (close to previous week's close), path (sum of |daily move|),
    eff = |net| / path. The first week without a previous week is dropped."""
    by = {}
    for d, c in days:
        by.setdefault(d.isocalendar()[:2], []).append((d, c))
    keys = sorted(by)
    out = []
    prev = None
    for k in keys:
        bs = by[k]
        if prev is not None:
            series = [prev] + [c for _, c in bs]
            path = sum(abs(series[i] / series[i - 1] - 1) for i in range(1, len(series)))
            net = series[-1] / series[0] - 1
            out.append(dict(year=k[0], week=k[1], start=bs[0][0], end=bs[-1][0], days=len(bs),
                            net=net, path=path, eff=(abs(net) / path if path else 0.0),
                            close=series[-1]))
        prev = bs[-1][1]
    return out


def window(days, n, today=None):
    """Net, path and efficiency over the last n completed trading days.
    Today counts only after the close (call after 21:30); otherwise it is dropped."""
    series = [c for d, c in days if today is None or d <= today]
    if len(series) < n + 1:
        return None
    series = series[-(n + 1):]
    path = sum(abs(series[i] / series[i - 1] - 1) for i in range(1, len(series)))
    net = series[-1] / series[0] - 1
    return dict(n=n, net=net, path=path, eff=(abs(net) / path if path else 0.0))


def sideways(days, today=None):
    """0 = there is movement, 1 = warning (last 5 days sideways), 2 = trigger (10 days sideways).
    Trigger as in 00-thesis.md / 92-sideways.md section 1: efficiency over 10 trading days
    below 0.25 with a net move below 5%."""
    f10 = window(days, 10, today)
    f5 = window(days, 5, today)
    if f10 and f10["eff"] < EFF_LIMIT and abs(f10["net"]) < NET_LIMIT:
        return 2, f10, f5
    if f5 and f5["eff"] < EFF_LIMIT and abs(f5["net"]) < NET_LIMIT / 2:
        return 1, f10, f5
    return 0, f10, f5


def plain_text(f):
    """'+7.8% in two weeks, back-and-forth ate 1% of the movement' instead of 'efficiency 0.99'."""
    if not f:
        return "too little price data"
    duration = {5: "one week", 10: "two weeks"}.get(f["n"], f"{f['n']} trading days")
    loss = max(0.0, 1 - f["eff"])
    return f"{f['net']:+.1%} in {duration}, back-and-forth ate {loss:.0%} of the movement"


# ---- Depots ----------------------------------------------------------------

def depot_status(text=None):
    """Depot value A/B, as-of date, knock-outs of Depot A in a row (log), positions A."""
    text_is_file = text is None
    if text is None:
        try:
            text = io.open(POSITIONS, encoding="utf-8").read()
        except FileNotFoundError:
            text = ""
    out = dict(A=None, B=None, date=None, ko_a_streak=0)
    m = re.search(r"Date:\s*(\d{4}-\d{2}-\d{2})", text)
    if m:
        out["date"] = dt.date.fromisoformat(m.group(1))
    # Whole euros only; the decimals are dropped. A bold value (**232,469.59**) is read too.
    m = re.search(r"\|\s*Depot value\s*\|\s*\**([\d,]+)(?:\.\d+)?[^|]*\|\s*\**([\d,]+)(?:\.\d+)?[^|]*\|", text)
    if m:
        out["A"] = float(m.group(1).replace(",", ""))
        out["B"] = float(m.group(2).replace(",", ""))
    # Knock-outs of Depot A in a row: log rows from the bottom that name "A" and a knock-out;
    # a row with a new purchase in A without a knock-out does not break the streak, a profitable sale does.
    log = text.split("## Log", 1)[-1]
    rows = [z for z in log.splitlines() if z.startswith("| 20")]
    streak = 0
    for z in reversed(rows):
        action = z.split("|")[2] if z.count("|") >= 3 else z
        a_part = re.search(r"A:([^|]*?)(?=B:|$)", action)
        a_txt = a_part.group(1) if a_part else ""
        if re.search(r"knock-?out|knocked out|breached", a_txt, re.I):
            streak += 1
        elif re.search(r"sold|closed|profit", a_txt, re.I):
            break
    out["ko_a_streak"] = streak
    # The computed daily status (daily_report.py) beats an older manual entry.
    ds = load_json(DAILY_STATE) if text_is_file else None
    if ds and ds.get("A") and ds.get("B"):
        d = dt.date.fromisoformat(ds["date"])
        if out["date"] is None or d >= out["date"]:
            out.update(A=float(ds["A"]), B=float(ds["B"]), date=d)
    return out


def extend_history(st, today, status, brent):
    h = st.setdefault("history", [])
    entry = dict(date=today.isoformat(), A=status["A"], B=status["B"],
                 as_of=status["date"].isoformat() if status["date"] else None, brent=brent)
    if h and h[-1]["date"] == entry["date"]:
        h[-1] = entry
    else:
        h.append(entry)
    st["history"] = h[-120:]
    return h


def last_friday_value(history, today):
    """Best depot on the last Friday before the current week (or the start value 100,000)."""
    monday = today - dt.timedelta(days=today.weekday())
    for e in reversed(history):
        d = dt.date.fromisoformat(e["date"])
        if d < monday and e.get("A") is not None:
            return max(e["A"], e["B"] or 0), d
    return 100_000.0, START


# ---- Assessment --------------------------------------------------------------
# Numbers in the messages use Python's default English format (131,237 and +1.2%),
# so no conversion pass is needed.

def short_date(d):
    return f"{d.day} {d:%b}"


def assess(days, status, history, today, brent=None):
    """Rule-based, no model. Returns stage, text (for the player), full (for the log)."""
    level, f10, f5 = sideways(days, today)
    week_list = weeks(days)
    done_weeks = [w for w in week_list if w["end"].weekday() == 4 or (today - w["end"]).days >= 3]
    a, b = status.get("A"), status.get("B")
    best = max(a or 0, b or 0) or None
    ref, ref_date = last_friday_value(history, today)
    week_pct = (best / ref - 1) if (best and ref) else None
    total_pct = (best / 100_000 - 1) if best else None
    missing = (WINNING_MARK / best) if best else None
    days_left = (END - today).days
    ko = status.get("ko_a_streak", 0)
    status_old = status.get("date") and (today - status["date"]).days >= 2

    reasons, stage = [], "calm"
    # 1) Sideways
    if level >= 2:
        stage = "switch"
        reasons.append(f"Brent is moving sideways: {plain_text(f10)}. With a 1% distance Depot 1 gets knocked out in a market like this before a run comes.")
    elif level == 1:
        stage = "warning"
        reasons.append(f"Brent moved sideways last week: {plain_text(f5)}. If it stays like that for a second week, Depot 1 switches to weekly mode.")
    elif f10 and (f10["eff"] < EFF_LIMIT + 0.10 or abs(f10["net"]) < NET_LIMIT + 0.02):
        reasons.append(f"Brent is moving, but only just: {plain_text(f10)}. The sideways threshold is close.")
    elif f10:
        reasons.append(f"Brent is moving: {plain_text(f10)}.")
    # 2) Knock-outs
    if ko >= KO_LIMIT:
        stage = "switch"
        reasons.append(f"Depot 1 was knocked out {ko} times in a row.")
    elif ko == 2:
        stage = "warning" if stage == "calm" else stage
        reasons.append("Depot 1 was knocked out twice in a row; a third time means weekly mode.")
    # 3) Gains
    if today >= MAIN_PRIZE_CUTOFF and best and best < MAIN_PRIZE_MINIMUM:
        stage = "main_prize_off"
        reasons.append(f"Cutoff of 12 Oct missed: best depot at {best:,.0f} EUR instead of at least 300,000.")
    elif week_pct is not None and today.weekday() >= 4 and week_pct < WEEK_BENCHMARK and level >= 1:
        stage = "warning" if stage == "calm" else stage
        reasons.append(f"The week brought {week_pct:+.1%} in the better depot; weekly mode delivers a median of +12%.")

    # Action
    if stage == "switch":
        action = ("Switch Depot 1 to weekly mode: on Monday a Brent turbo with 2% distance instead of 1%, "
                  "close on Friday at 21:45, new on Monday. Depot 2 stays as it is. "
                  "Back to 1% only after a real event (Kharg, end of the blockade, supply outage).")
    elif stage == "main_prize_off":
        action = ("Write off the main prize. Both depots on weekly scoring: 2% distance, close on Friday, new on Monday. "
                  "The goal is now the weekly prizes (EUR 2,222) and the rank.")
    elif stage == "warning":
        action = "Change nothing yet. I will report when the second condition is met."
    else:
        action = "Change nothing, the plan is running."

    head = {"calm": "Regime check", "warning": "Regime check: warning", "switch": "Regime check: weekly mode",
            "main_prize_off": "Regime check: write off the main prize"}[stage]
    lines = [f"{head} {short_date(today)}"]
    if best:
        situation = f"Better depot {best:,.0f} EUR ({total_pct:+.1%} since start"
        if week_pct is not None and ref_date != START:
            situation += f", {week_pct:+.1%} this week"
        situation += f"). The winning mark is {missing:.0f}x that, {days_left} days remain."
        lines.append(situation)
        if status_old:
            lines.append(f"Depot status is from {short_date(status['date'])}, please update positions.md.")
    else:
        lines.append("No depot value found in positions.md, please add it.")
    lines.append("To do: " + action)
    lines.append("Why: " + " ".join(reasons))
    text = lines[0] + "\n\n" + "\n\n".join(lines[1:])

    full = [text, ""]
    if f10:
        full.append(f"Window 10 days: net {f10['net']:+.1%}, path {f10['path']:.1%}, eff {f10['eff']:.2f} (trigger: eff < {EFF_LIMIT}, |net| < {NET_LIMIT:.0%})")
    if f5:
        full.append(f"Window 5 days:  net {f5['net']:+.1%}, path {f5['path']:.1%}, eff {f5['eff']:.2f}")
    full.append("Brent weeks (completed):")
    for w in done_weeks[-6:]:
        full.append(f"  W{w['week']:02d} {short_date(w['start'])} to {short_date(w['end'])}: net {w['net']:+.1%}, path {w['path']:.1%}, eff {w['eff']:.2f}")
    return dict(stage=stage, text=text, full="\n".join(full), level=level, ko=ko,
                best=best, week_pct=week_pct, brent=brent, f10=f10, f5=f5)


def write_log(today, b):
    new = not os.path.exists(LOG_FILE)
    os.makedirs(DATA, exist_ok=True)
    with io.open(LOG_FILE, "a", encoding="utf-8") as f:
        if new:
            f.write("# Regime log\n\nOne line per trading day, written by `src/regime.py`.\n\n")
            f.write("| Date | Stage | Brent | Sideways level | KO streak Depot A | Best depot | Week |\n|---|---|---|---|---|---|---|\n")
        f10 = b.get("f10") or {}
        brent = f"{b['brent']:.2f}" if b.get("brent") else "?"
        best = f"{b['best']:,.0f}" if b.get("best") else "?"
        week = f"{b['week_pct']:+.1%}" if b.get("week_pct") is not None else "?"
        f.write(f"| {today} | {b['stage']} | {brent} | {b['level']} (10 d: {f10.get('net', 0):+.1%}, eff {f10.get('eff', 0):.2f}) | {b['ko']} | {best} | {week} |\n")


def daily(today=None, send=True, brent_today=None):
    """One run per day. Returns (text, assessment); text is None when nothing is reported.
    brent_today: price from the Watch (CNBC), the fallback when Yahoo does not answer."""
    today = today or dt.datetime.now(TZ).date()
    st = load_json(STATE) or {}
    try:
        days = brent_days()
        st["brent_days"] = [(d.isoformat(), c) for d, c in days]
        st["brent_source"] = "Yahoo"
    except Exception as e:
        days = [(dt.date.fromisoformat(d), c) for d, c in st.get("brent_days", [])]
        if brent_today:
            days = [(d, c) for d, c in days if d != today] + [(today, float(brent_today))]
            st["brent_days"] = [(d.isoformat(), c) for d, c in days]
        st["brent_source"] = f"cache ({type(e).__name__})"
        if not days:
            raise RuntimeError(f"Brent history unreachable and no cache: {type(e).__name__}")
    status = depot_status()
    history = extend_history(st, today, status, days[-1][1] if days else None)
    b = assess(days, status, history, today, brent=days[-1][1] if days else None)
    report = today.weekday() == 4 or b["stage"] != st.get("stage") or (today.weekday() == 0 and b["stage"] != "calm")
    st["stage"] = b["stage"]
    st["last_run"] = today.isoformat()
    if send:
        write_json(STATE, st, indent=1)
        write_log(today, b)
    return b["text"] if report else None, b


def main():
    ap = argparse.ArgumentParser(description="Regime check: sideways market and weekly gains")
    ap.add_argument("--test", action="store_true", help="compute and show, write and send nothing")
    ap.add_argument("--json", action="store_true", help="print the full assessment as JSON")
    ap.add_argument("--date", help="YYYY-MM-DD instead of today")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.date) if a.date else None
    text, b = daily(today, send=not a.test)
    if a.json:
        print(json.dumps(b, indent=1, ensure_ascii=False, default=str))
        return
    print(b["full"])
    print("\nREPORT:", "yes" if text else "no (not a Friday, stage unchanged)")
    if not a.test and text:
        from watch import send_telegram
        send_telegram(text)


if __name__ == "__main__":
    main()

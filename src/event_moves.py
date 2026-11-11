"""
Event-move library: what Brent actually did around comparable events.

For every dated event, measured on EIA daily closes (Brent since 1987): the move
on the first trading day after it, the high and low within 5 and 20 trading days,
and the level after 20 and 40 days. This is the size scale for the Watch's
assessment: comparison cases, not a forecast.

Usage:   python3 src/event_moves.py [--write] [--extra 2026-09-08:Name ...]
         python3 src/event_moves.py --data-dir /path/to/cache
"""

import argparse
import csv
import datetime as dt
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data")
OUTPUT = os.path.join(REPO, "strategy", "71-event-moves.md")

BRENT_FILE = "eia_brent.csv"
BRENT_SOURCE = ("EIA Brent spot daily closes since 1987, columns date,close; originally fetched "
                "with curl from the EIA spot price history HTML table")

# (event date, short name, type). The move is measured from the last close
# BEFORE the date; if the event falls inside trading hours, that day's close
# is the first reaction day.
EVENTS = [
    ("1990-08-02", "Iraq invades Kuwait", "Escalation"),
    ("1991-01-17", "Desert Storm begins", "Escalation, resolution"),
    ("2001-09-11", "September 11 attacks", "Shock"),
    ("2003-03-20", "Iraq invasion", "Escalation, priced in"),
    ("2008-07-11", "All-time high $147", "Peak"),
    ("2014-06-10", "ISIS takes Mosul", "Escalation Iraq"),
    ("2019-06-13", "Tanker attacks, Gulf of Oman", "Hormuz incident"),
    ("2019-09-14", "Abqaiq attack, Saudi output halved", "Infrastructure"),
    ("2020-01-03", "Soleimani killed", "Escalation Iran"),
    ("2020-03-06", "OPEC+ split, price war, Covid", "Supply shock, demand"),
    ("2022-02-24", "Russia invades Ukraine", "Escalation, sanctions"),
    ("2022-03-08", "Brent peak $128, US import ban", "Peak"),
    ("2023-10-07", "Hamas attack on Israel", "Escalation Middle East"),
    ("2024-04-13", "Iran attacks Israel directly", "Escalation Iran"),
    ("2025-06-13", "Israel strikes Iran, Twelve-Day War", "Escalation Iran"),
    ("2025-06-24", "Israel-Iran ceasefire", "De-escalation"),
    # 2026, from the chronology in strategy/70-hormuz-dossier.md
    ("2026-02-28", "War begins, Khamenei killed, Hormuz closed", "Supply outage"),
    ("2026-03-19", "US air campaign to reopen the strait begins", "Escalation"),
    ("2026-04-12", "Islamabad talks fail, US naval blockade", "Escalation"),
    ("2026-05-06", "Trump pauses Project Freedom, 'great progress'", "De-escalation, hope"),
    ("2026-06-17", "Trump-Pezeshkian MoU, strait opens 18 Jun, blockade ends", "DEAL REPORTED"),
    ("2026-07-08", "Ceasefire breaks, Iran attacks merchant ships", "Escalation"),
    ("2026-07-14", "US reimposes blockade", "Escalation"),
    ("2026-08-19", "60-day deadline expires, no extension", "Escalation"),
    ("2026-08-26", "Iran-Oman corridor agreed, without US consent", "De-escalation, partial"),
]


def load(data_dir=DATA):
    path = os.path.join(data_dir, BRENT_FILE)
    if not os.path.exists(path):
        sys.exit(f"Missing data file {path} ({BRENT_SOURCE}).")
    with open(path) as f:
        rows = list(csv.DictReader(f))
    dates = [dt.date.fromisoformat(x["date"]) for x in rows]
    closes = np.array([float(x["close"]) for x in rows])
    return dates, closes


def measure(dates, closes, date):
    event = dt.date.fromisoformat(date)
    i0 = max(i for i, x in enumerate(dates) if x < event)   # last close before the event
    base = closes[i0]
    f = closes[i0 + 1:i0 + 41]
    if len(f) < 2:
        return None
    n = len(f)
    after = lambda k: (f[k - 1] / base - 1) if n >= k else None
    return dict(base=base, day1=f[0] / base - 1, n=n,
                high5=f[:5].max() / base - 1, low5=f[:5].min() / base - 1,
                high20=f[:20].max() / base - 1, low20=f[:20].min() / base - 1,
                high20_day=int(f[:20].argmax()) + 1,
                after20=after(20), after40=after(40))


def main():
    ap = argparse.ArgumentParser(description="Brent event-move library: comparison cases from EIA daily closes.")
    ap.add_argument("--write", action="store_true", help=f"also write the table to strategy/{os.path.basename(OUTPUT)}")
    ap.add_argument("--extra", nargs="*", default=[], help="additional events as YYYY-MM-DD:Name")
    ap.add_argument("--data-dir", default=DATA, help="directory with eia_brent.csv (default: data/ in the repo root)")
    a = ap.parse_args()
    dates, closes = load(a.data_dir)
    out = []
    P = out.append
    P("# Brent event-move library: comparison cases")
    P("")
    P("From EIA daily closes. Move measured from the last close before the event. High/Low = extreme within the window.")
    P("")
    P("| Date | Event | Type | Base $ | Day 1 | High 5d | Low 5d | High 20d (day) | Low 20d | After 20d | After 40d |")
    P("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    events = list(EVENTS) + [(z.split(":", 1)[0], z.split(":", 1)[1], "Extra") for z in a.extra]
    for date, name, kind in sorted(events):
        m = measure(dates, closes, date)
        if not m:
            P(f"| {date} | {name} | {kind} | no data | | | | | | | |"); continue
        pct = lambda v: f"{v:+.1%}" if v is not None else f"({m['n']} d)"
        P(f"| {date} | {name} | {kind} | {m['base']:.0f} | {m['day1']:+.1%} | {m['high5']:+.1%} | {m['low5']:+.1%} | "
          f"{m['high20']:+.1%} ({m['high20_day']}) | {m['low20']:+.1%} | {pct(m['after20'])} | {pct(m['after40'])} |")
    P("")
    P("Reading for the assessment: a 1% turbo survives only if the low in the window stays above -1% (long) or the high below +1% (short).")
    P("The Low 5d / High 5d columns show how often even the right direction first runs through the barrier.")
    text = "\n".join(out)
    print(text)
    if a.write:
        with open(OUTPUT, "w") as f:
            f.write(text + "\n")
        print("->", OUTPUT)


if __name__ == "__main__":
    main()

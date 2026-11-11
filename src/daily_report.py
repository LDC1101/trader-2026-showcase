"""
Daily report: where both depots stand, shortly before the close.

The player's request on 7 Sep 2026: an interim status of both depots before the
close on every trading day. Runs from the Watch on weekdays in the 21:00-21:14
run: SG trades until 22:00 but stops quoting through its interface from about
21:30 (7 Sep 2026: the first report at 21:33 valued both positions at 0). The
regime check runs right after it.

The game platform shows different figures: it apparently values positions at
the product's last exchange trade, which can be hours old for illiquid turbos
(7 Sep: put at EUR 1.59 from the morning session while SG bid 1.38). Here the
SG bid counts, i.e. what a sale would bring now.

Computes the depot value itself: cash from depot/positions.md plus units times
the product's bid from sg-zertifikate.de. The player only has to record buys
and sells. The computed status goes to data/daily_state.json; the regime check
uses it when positions.md is older. No access to the game account, no order.

Messages use the platform's names "Depot 1" and "Depot 2" (Depot A and Depot B
in the files).

    python3 src/daily_report.py --test     # shows, does not send
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
from situation import quote_cnbc, load_json, write_json  # noqa: E402

TZ = zoneinfo.ZoneInfo("Europe/Berlin")
DATA = os.path.join(REPO, "data")
POSITIONS = os.path.join(REPO, "depot", "positions.md")
DAILY_STATE = os.path.join(DATA, "daily_state.json")
QUOTE_CACHE = os.path.join(DATA, "sg_quotes.json")   # last valid bid per WKN, refreshed hourly by the Watch
START = 100_000.0
WINNING_MARK = 1_350_000
# Underlying name in positions.md -> (SG AssetId, CNBC symbol)
UNDERLYINGS = {"brent": (-4, "@LCO.1"), "wti": (-5, "@CL.1"), "gold": (415, "XAU="), "silver": (423, "XAG="),
               "dax": (389, ".GDAXI"), "nasdaq": (315, ".NDX")}
NAME = {"A": "Depot 1", "B": "Depot 2"}


def number(s):
    """'80,233.48' -> 80233.48; '€1.38 (7 Sep 9:49)' -> 1.38; '14,489' -> 14489.
    English format only: thousands comma, decimal point."""
    m = re.search(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?", s or "")
    if not m:
        return None
    return float(m.group(0).replace(",", ""))


def read_positions(text=None):
    """Cash per depot and open positions (depot, wkn, product, underlying, units, entry, barrier)."""
    if text is None:
        text = io.open(POSITIONS, encoding="utf-8").read()
    cash = {}
    m = re.search(r"\|\s*Cash\s*\|([^|]*)\|([^|]*)\|", text)
    if m:
        cash = {"A": number(m.group(1)), "B": number(m.group(2))}
    m = re.search(r"Date:\s*(\d{4}-\d{2}-\d{2})", text)
    date = dt.date.fromisoformat(m.group(1)) if m else None
    pos = []
    block = text.split("## Open positions", 1)[-1].split("## ", 1)[0]
    for line in block.splitlines():
        z = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(z) < 9 or not z[1] or z[0] == "Depot" or set(z[0]) <= set("-: "):
            continue
        pos.append(dict(depot=z[0].strip().upper()[-1], wkn=z[1], product=z[2], underlying=z[3],
                        units=number(z[4]), entry=number(z[5]), barrier=number(z[8]),
                        direction="short" if re.search(r"put|short", z[2], re.I) else "long"))
    return dict(cash=cash, date=date, positions=pos)


def underlying(name):
    k = next((k for k in UNDERLYINGS if k in name.lower()), None)
    return (k,) + UNDERLYINGS[k] if k else (None, None, None)


def fetch_sg_quotes(positions, now=None, cache=True):
    """Bid per WKN from SG (BEST 47, otherwise Classic 43).

    Outside quoting hours (seen on 7 Sep 2026 from about 21:30) SG returns bid 0. That is
    not a price but "none". The last valid price from the cache then applies, with its time.
    Valid prices go into the cache (the Watch calls this hourly)."""
    import sg_products as sg
    now = now or dt.datetime.now(TZ)
    out = {}
    held = {p["wkn"] for p in positions}
    for p in positions:
        if p["wkn"] in out:
            continue
        _, asset, _ = underlying(p["underlying"])
        if asset is None:
            continue
        cp = 1 if p["direction"] == "short" else 0  # SG API: CallPutRadio 0 = call, 1 = put
        for product_class in (47, 43):
            try:
                for r in sg.products(asset, product_class, cp):
                    if r.get("Code") in held:
                        bid = r.get("Bid") or 0.0
                        out[r["Code"]] = dict(bid=(bid if bid > 0 else None), offer=r.get("Offer") or None,
                                              barrier=r.get("BarrierTurboCertificate") or r.get("Strike"),
                                              leverage=r.get("CurrentLeverage"), hit=r.get("TodayBarrierHitDate"),
                                              time=now.strftime("%H:%M") if bid > 0 else None)
            except Exception:
                continue
            if p["wkn"] in out:
                break
    if cache:
        out = with_cache(out, held, now)
    return out


def with_cache(out, held, now):
    """Store valid prices; replace missing ones from the same day's cache (flagged)."""
    c = load_json(QUOTE_CACHE) or {}
    today = now.date().isoformat()
    for wkn, q in out.items():
        if q.get("bid"):
            c[wkn] = dict(bid=q["bid"], offer=q.get("offer"), date=today, time=q["time"])
    for wkn in held:
        q = out.get(wkn, {})
        old = c.get(wkn)
        if not q.get("bid") and old and old.get("date") == today:
            out[wkn] = dict(q, bid=old["bid"], offer=old.get("offer"), time=old["time"], from_cache=True)
    write_json(QUOTE_CACHE, c, indent=1)
    return out


def underlying_quotes(positions):
    out = {}
    for p in positions:
        k, _, sym = underlying(p["underlying"])
        if k and k not in out:
            r = quote_cnbc(sym)
            if r:
                out[k] = dict(price=r[1], day=r[2])
    return out


def compute(data, sg, base):
    """Depot values and position lines. Pure calculation, testable."""
    depots = {}
    for d in ("A", "B"):
        depots[d] = dict(cash=data["cash"].get(d), positions=[], value=None)
    for p in data["positions"]:
        q = sg.get(p["wkn"], {})
        bid = q.get("bid")
        k, _, _ = underlying(p["underlying"])
        b = base.get(k, {})
        distance = None
        if b.get("price") and p.get("barrier"):
            distance = (b["price"] / p["barrier"] - 1) if p["direction"] == "long" else (p["barrier"] / b["price"] - 1)
        value = bid * p["units"] if (bid is not None and p.get("units")) else None
        depots.setdefault(p["depot"], dict(cash=None, positions=[], value=None))["positions"].append(
            dict(p, bid=bid, value=value, distance=distance, hit=q.get("hit"),
                 quote_time=q.get("time") if q.get("from_cache") else None,
                 since_buy=(bid / p["entry"] - 1) if (bid and p.get("entry")) else None))
    for d, dep in depots.items():
        if dep["cash"] is not None and all(p["value"] is not None for p in dep["positions"]):
            dep["value"] = dep["cash"] + sum(p["value"] for p in dep["positions"])
    return depots


def num(x, n=0):
    """English number: thousands comma, decimal point."""
    return f"{x:,.{n}f}"


def pct(x, n=1):
    return f"{x*100:+.{n}f}%"


def short_name(p):
    k, _, _ = underlying(p["underlying"])
    kind = "put" if p["direction"] == "short" else "call"
    return f"{(k or p['underlying']).capitalize()} {kind} {p['wkn']}"


def render(depots, base, now, positions_date=None):
    lines = [f"Daily status {now.day} {now:%b %H:%M}"]
    hints = []
    values = {d: dep["value"] for d, dep in depots.items() if dep["value"]}
    for d in ("A", "B"):
        dep = depots.get(d)
        if not dep:
            continue
        if dep["value"] is None:
            missing = [p["wkn"] for p in dep["positions"] if p["value"] is None]
            lines.append(f"{NAME[d]}: value not computable today, SG no longer quotes {', '.join(missing) or 'the position'}. Cash €{num(dep['cash'])}." if dep["cash"] is not None
                         else f"{NAME[d]}: value not computable, cash is missing in positions.md.")
            continue
        s = f"{NAME[d]}: €{num(dep['value'])} ({pct(dep['value'] / START - 1)} since start)."
        for p in dep["positions"]:
            s += f" {short_name(p)}"
            if p["since_buy"] is not None:
                s += f" {pct(p['since_buy'], 0)} since purchase"
            if p.get("quote_time"):
                s += f" (SG price from {p['quote_time']})"
            if p["distance"] is not None:
                s += f", distance to barrier {pct(p['distance']).lstrip('+')}"
                if p["distance"] <= 0 or p.get("hit"):
                    hints.append(f"{short_name(p)} in {NAME[d]} is knocked out or touched the barrier today. The new order card comes tomorrow at 8:05; update positions.md.")
                elif p["distance"] < 0.01:
                    hints.append(f"{short_name(p)} in {NAME[d]} is less than 1% from the barrier and can be knocked out overnight. That is part of the plan, do nothing; the new card comes tomorrow at 8:05.")
            s += "."
        if not dep["positions"]:
            s += " No position, cash only."
            hints.append(f"{NAME[d]} has no position. The order card comes tomorrow at 8:05.")
        lines.append(s)
    for k, b in base.items():
        lines.append(f"{k.capitalize()} ${num(b['price'], 2)}" + (f" ({pct(b['day'])} today)." if b.get("day") else "."))
    if values:
        best = max(values.values())
        ahead = NAME[max(values, key=values.get)] if len(values) == 2 and values["A"] != values["B"] else None
        s = f"The winning mark is {WINNING_MARK / best:.0f}x the best depot."
        if ahead:
            s = f"{ahead} is ahead. " + s
        lines.append(s)
    lines.append("To do: " + (" ".join(hints) if hints else "Nothing. Both positions are running, the sell limits are in place."))
    return "\n\n".join(lines)


def build(now=None, write=True):
    now = now or dt.datetime.now(TZ)
    data = read_positions()
    sg = fetch_sg_quotes(data["positions"], now)
    base = underlying_quotes(data["positions"])
    depots = compute(data, sg, base)
    t = render(depots, base, now, data["date"])
    if write and all(depots.get(d, {}).get("value") for d in ("A", "B")):
        write_json(DAILY_STATE, dict(date=now.date().isoformat(), time=now.strftime("%H:%M"),
                                     A=depots.get("A", {}).get("value"), B=depots.get("B", {}).get("value"),
                                     underlyings=base), indent=1)
    return t, depots


def main():
    ap = argparse.ArgumentParser(description="Daily status of both depots, before the close")
    ap.add_argument("--test", action="store_true", help="show the report, do not write or send")
    a = ap.parse_args()
    t, _ = build(write=not a.test)
    print(t)
    if not a.test:
        from watch import send_telegram
        send_telegram(t)


if __name__ == "__main__":
    main()

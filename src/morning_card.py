"""
Morning card: the day's buy order as a Telegram message, with live prices.

Runs on weekdays at 8:05 and 9:05 (launchd, see ops/launchd/). Checks which
depot has no live position (depot/positions.md, knock-outs from the Watch),
pulls the products for it from SG, computes units and limit, and writes:
WKN, units, ask, stake, barrier, distance, limit sell, holding period. The
player buys by hand. No access to the game account, no order.

Rules from the Monday plan: Depot A Brent BEST call, distance 0.7-2% (since
17 Sep, 1.5% before), otherwise a gold BEST put as the escalation leg. Depot B
Brent BEST put 0.8-2.2%. After a knock-out, rotate to gold, opposite to the
other depot. Stake min(20% of depot, EUR 20,000), at most 20,000 units. Limit
sell at 67.5 times the ask (the winning mark), 7 days.

Usage:    python3 src/morning_card.py --test     # shows, does not send
          python3 src/morning_card.py
          python3 src/morning_card.py --depot B --text-only   # used by the Watch
"""

import argparse
import datetime as dt
import io
import math
import os
import re
import sys
import zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from sg_products import products, spots_by_contract  # noqa: E402
from watch import send_telegram, log, open_positions, load_state, polymarket  # noqa: E402
from situation import load_json, write_json  # noqa: E402

TZ = zoneinfo.ZoneInfo("Europe/Berlin")
DATA = os.path.join(REPO, "data")
STATE = os.path.join(DATA, "morning_state.json")
POSITIONS = os.path.join(REPO, "depot", "positions.md")
BET = os.path.join(REPO, "depot", "bet.json")
KO_STATE_KEY = "ko_alerted"   # knock-outs the Watch has already reported (data/watch_state.json)
WIN_MULTIPLE = 1_350_000 / 20_000
MIN_ASK = 0.60        # below this ask the 20,000-unit cap binds too hard
FEE = 3.90
BRENT, GOLD = -4, 415
BEST = 47


def _amount(cell):
    """'120,368.01 (8 Sep 11:26)' -> 120368.01; '83,628.50' -> 83628.5; '' -> None."""
    m = re.search(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", cell or "")
    return float(m.group(0).replace(",", "")) if m else None


def depot_values(text=None, live=None):
    """Depot value A/B for the 20% cap.

    After a knock-out, positions.md often still shows the old depot value with the dead
    position in it (8 Sep 2026: the card sized EUR 19,996 against 101,237 while 16,725 was
    allowed). If a depot has no live position, its cash balance counts. If nothing is there:
    100,000."""
    if text is None:
        try:
            text = io.open(POSITIONS, encoding="utf-8").read()
        except FileNotFoundError:
            text = ""
    if live is None:
        live = live_positions()
    values = {}
    for name in ("Depot value", "Cash"):
        m = re.search(r"\|\s*" + name + r"\s*\|([^|]*)\|([^|]*)\|", text)
        values[name] = (_amount(m.group(1)), _amount(m.group(2))) if m else (None, None)
    out = []
    for i, d in enumerate(("A", "B")):
        value, cash = values["Depot value"][i], values["Cash"][i]
        if not live.get(d) and cash:
            out.append(cash)
        else:
            out.append(value or cash or 100_000.0)
    return tuple(out)


def live_positions():
    ko = set(load_state().get(KO_STATE_KEY, []))
    live = {}
    for depot, wkn, underlying, direction, barrier in open_positions():
        if wkn not in ko:
            live.setdefault(depot.strip().upper()[-1], []).append((wkn, underlying, direction))
    return live


def candidate(asset, callput, lo, hi, target):
    px = products(asset, BEST, callput)
    calls = px if callput == 0 else products(asset, BEST, 0)
    puts = px if callput == 1 else products(asset, BEST, 1)
    # Price per contract: SG lists several futures months at once (sg_products.spots_by_contract)
    spots = spots_by_contract(calls, puts)
    if not spots:
        return None, None
    best, seen = None, set()
    for p in px:
        if p.get("Code") in seen:
            continue
        seen.add(p.get("Code"))
        c = spots.get(p.get("AssetName"))
        bar = p.get("BarrierTurboCertificate") or p.get("Strike") or 0
        ask = p.get("Offer") or 0
        if not c or bar <= 0 or ask < MIN_ASK:
            continue
        S = c["S"]
        dist = (S - bar) / S if callput == 0 else (bar - S) / S
        if lo <= dist <= hi:
            score = abs(dist - target)
            if best is None or score < best[0]:
                best = (score, dist, p, ask, bar, S)
    if best is None:
        return next(iter(spots.values()))["S"], None   # price of the largest contract, for the message
    return best[5], best[:5]


def order_size(depot_value, ask):
    # The platform counts the fee towards the 20% volume (rejection on 7 Sep 2026 at EUR 19,998).
    max_eur = min(0.20 * depot_value, 20_000.0) - FEE
    n = min(20_000, math.floor(max_eur / ask))
    return n, n * ask


def num(x, n=2):
    """English number: thousands comma, decimal point."""
    return f"{x:,.{n}f}"


def order_line(name, depot_value, S, k, direction_txt, reason=""):
    if not k:
        return f"DEPOT {name}: {reason or 'no product in the target range'}. Do not buy, retry at 9:05."
    _, dist, p, ask, bar = k
    n, eur = order_size(depot_value, ask)
    limit = ask * WIN_MULTIPLE
    is_put = "Put" in direction_txt
    # 67.5x on the product means the underlying has to travel 67.5 times the distance
    # to the barrier. At a 1.2% distance that is -81% (put) or +81% (call). A put can
    # only do that if the underlying does not reach 0 first.
    target_S = bar - WIN_MULTIPLE * (bar - S) if is_put else bar + WIN_MULTIPLE * (S - bar)
    move = (target_S / S - 1) * 100
    if is_put and target_S <= 0:
        exit_txt = (f"No sell limit: 67.5× would mean the underlying below 0 "
                    f"(put maximum {bar / max(bar - S, 1e-9):.0f}×). Hold until knock-out or 30 Oct.")
    else:
        exit_txt = (f"Then: limit sell €{num(limit)} (67.5× = underlying {num(target_S)}, "
                    f"{move:+.0f}%), 7 days. Hold until knock-out or 30 Oct.")
    t = (f"DEPOT {name}: BUY {p['AssetName']} {direction_txt}\n"
         f"WKN {p['Code']} · {num(n, 0)} units at €{num(ask)} = €{num(eur, 0)}\n"
         f"Barrier {num(bar)} ({dist*100:.2f}% to {num(S)}) · leverage {p.get('CurrentLeverage') or 0:.0f}"
         f"{' · quanto' if p.get('IsQuanto') else ''}\n"
         f"{exit_txt}")
    if reason:
        t += f"\n({reason})"
    return t


def day_bet(today):
    """The player's day bet for Depot A (since 19 Sep 2026): depot/bet.json with
    {"date": "2026-09-21", "asset": 214, "name": "AMD", "direction": "call",
     "distance": [0.025, 0.045], "target": 0.03}. Applies only on the given day and only
    if Depot A has no position. Replaces the Brent call on that day. A missing file
    means no day bet."""
    w = load_json(BET)
    if w and w.get("date") == today and w.get("asset"):
        return w
    return None


def day_bet_line(name, depot_value, S, k, w):
    if not k:
        lo, hi = w.get("distance", [0.025, 0.045])
        return (f"DEPOT {name}: day bet {w.get('name')}: no {w.get('direction', 'call').upper()} "
                f"with {lo*100:.1f}–{hi*100:.1f}% distance. Do not buy, retry at 9:05.")
    _, dist, p, ask, bar = k
    n, eur = order_size(depot_value, ask)
    return (f"DEPOT {name}: DAY BET {p['AssetName']} {'LONG (call)' if w.get('direction', 'call') == 'call' else 'SHORT (put)'}\n"
            f"WKN {p['Code']} · {num(n, 0)} units at €{num(ask)} = €{num(eur, 0)} · limit €{num(ask + 0.02)}\n"
            f"Barrier {num(bar)} ({dist*100:.2f}% to {num(S)}) · leverage {p.get('CurrentLeverage') or 0:.0f}\n"
            f"No sell limit. Sell at market by 21:45 at the latest, US trading 15:30–22:00. "
            f"The spread is wider before 15:30; buying at 15:30 saves it but misses the opening gap.")


def main():
    ap = argparse.ArgumentParser(description="Morning order card for Depot A and Depot B")
    ap.add_argument("--test", action="store_true", help="show the card, do not send")
    ap.add_argument("--all", action="store_true", help="both depots, even if positions are live")
    ap.add_argument("--depot", action="append", choices=["A", "B"],
                    help="force the card for this depot (the Watch after a knock-out)")
    ap.add_argument("--text-only", action="store_true",
                    help="card to stdout, do not send, do not touch the state")
    a = ap.parse_args()
    now = dt.datetime.now(TZ)
    # launchd fires on the machine's local clock, which need not be Berlin time; the card
    # belongs to the Berlin market open. Runs outside 8-10 Berlin are misfires, skip them.
    if not a.test and not a.text_only and not (8 <= now.hour < 10):
        log(f"morning card: {now:%H:%M} Berlin is outside 8-10, nothing to do"); return
    st = load_json(STATE)
    today = now.strftime("%Y-%m-%d")
    forced = set(a.depot or [])
    if st.get("date") == today and st.get("done") and not a.test and not forced:
        log("morning card: already done today"); return
    va, vb = depot_values()
    live = live_positions()
    needed = {"A": "A" not in live or a.all or "A" in forced,
              "B": "B" not in live or a.all or "B" in forced}
    if forced:
        needed = {d: d in forced for d in needed}
    if not any(needed.values()):
        log("morning card: both depots have live positions, nothing to buy")
        if not a.test:
            write_json(STATE, dict(date=today, done=True))
        return
    parts = []
    done = True

    w = day_bet(today)
    if needed["A"] and w:
        lo, hi = w.get("distance", [0.025, 0.045])
        S, k = candidate(int(w["asset"]), 0 if w.get("direction", "call") == "call" else 1, lo, hi, w.get("target", 0.03))
        parts.append(day_bet_line("A", va, S, k, w))
        if not k:
            done = False
    elif needed["A"]:
        S, k = candidate(BRENT, 0, 0.007, 0.020, 0.010)   # up to 2% since 17 Sep (after knock-out of FG6MRT; tightest call was at 1.9%)
        if k:
            parts.append(order_line("A", va, S, k, "LONG (Call)"))
        else:
            # No substitute. Depot A is the main-prize leg; an instrument without a path
            # to the winning mark (gold put) is a placeholder there, and on 7 Sep 2026 it
            # had to be sold an hour later because SG listed new calls by 9:30.
            # Leave it empty, check hourly (the Watch).
            parts.append(f"DEPOT A: no Brent call ≤2% (Brent {num(S) if S else '?'}). Do NOT buy, no substitute. "
                         f"SG usually lists new ones by 9:30; the Watch checks hourly and sends the card.")
            done = False
    if needed["B"]:
        S, k = candidate(BRENT, 1, 0.017, 0.023, 0.020)   # weekly leg: 2% (strategy/92-sideways.md)
        parts.append(order_line("B", vb, S, k, "SHORT (Put)"))

    p_h = polymarket()
    head = f"ORDER CARD {now.day} {now:%b %H:%M} · Hormuz P {p_h if p_h is not None else '?'}%"
    if now.weekday() == 0 and today == "2026-09-07":
        head += "\nNote: before the first order, fill in the profile with name and address (otherwise the prize claim is lost). US exchanges are closed today."
    foot = ("Buy as a limit 2 cents above the ask, not at market. 5-minute holding period, then the sell limit "
            "(if given). Afterwards record it in depot/positions.md.")
    text = head + "\n\n" + "\n\n".join(parts) + "\n\n" + foot
    if a.text_only:
        print(text); return
    send_telegram(text, a.test)
    if not a.test:
        write_json(STATE, dict(date=today, done=done))


if __name__ == "__main__":
    main()

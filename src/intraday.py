"""
Intraday measurement on 15-minute bars (Yahoo, 60 days, data/intraday_15m.json).

Three questions (the player, 7 Sep 2026: "we cannot settle for sideways"):
 1. Regime: how large are the daily ranges compared with the net move?
 2. Trading more often under the game rules (EUR 20,000 per buy, EUR 3.90 per
    order, turbo spread, knock-out, 8:00-22:00 Stuttgart): does a mechanical
    rule without a directional forecast help? A grid, not a best value.
 3. Another asset: which series had the largest runs and the best trend
    efficiency in 60 days, i.e. the best chance that a 1% turbo survives and runs?

    python3 src/intraday.py                 # everything
    python3 src/intraday.py --asset BZ=F
"""
import argparse
import datetime as dt
import json
import os
import statistics as st
import sys
import zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data")
BARS_FILE = "intraday_15m.json"
BARS_SOURCE = ("Yahoo Finance 15-minute bars for BZ=F, CL=F, GC=F, SI=F, NG=F, HG=F, ^GDAXI, ^NDX, ^GSPC, "
               "28 Jun to 4 Sep 2026, JSON {symbol: [[unix_time, open, high, low, close], ...]}; "
               "originally downloaded in the browser")

TZ = zoneinfo.ZoneInfo("Europe/Berlin")
STAKE = 20_000.0
FEE = 3.90
SPREAD = 0.03          # turbo bid/ask, round trip (measured 7 Sep: 2.7-3.4%)
PREMIUM = 0.0017       # premium over intrinsic value, as a share of the underlying (FG6GK5: EUR 0.15 at USD 97)
H_START, H_END = 8, 22   # Stuttgart trading hours


def load(data_dir=DATA):
    path = os.path.join(data_dir, BARS_FILE)
    if not os.path.exists(path):
        sys.exit(f"Missing data file {path} ({BARS_SOURCE}).")
    with open(path) as f:
        raw = f.read()
    d = json.loads(raw)
    if isinstance(d, str):
        d = json.loads(d)
    out = {}
    for s, rows in d.items():
        if isinstance(rows, str):
            continue
        out[s] = [(dt.datetime.fromtimestamp(t, TZ), o, h, l, c) for t, o, h, l, c in rows]
    return out


def by_day(bars):
    by = {}
    for b in bars:
        by.setdefault(b[0].date(), []).append(b)
    return by


def regime(bars):
    by = by_day(bars)
    ranges, net = [], []
    for d, bs in by.items():
        if len(bs) < 20:
            continue
        hi = max(b[2] for b in bs); lo = min(b[3] for b in bs)
        ranges.append((hi - lo) / bs[0][1]); net.append(abs(bs[-1][4] / bs[0][1] - 1))
    ds = sorted(by)
    closes = [by[d][-1][4] for d in ds if len(by[d]) >= 20]
    eff = []
    for i in range(10, len(closes)):
        path = sum(abs(closes[j] / closes[j - 1] - 1) for j in range(i - 9, i + 1))
        eff.append(abs(closes[i] / closes[i - 10] - 1) / path if path else 0)
    run5 = max(abs(closes[i] / closes[i - 5] - 1) for i in range(5, len(closes)))
    run20 = max(abs(closes[i] / closes[i - 20] - 1) for i in range(20, len(closes)))
    return dict(days=len(ranges), range_med=st.median(ranges), net_med=st.median(net),
                eff_med=st.median(eff) if eff else 0, run5=run5, run20=run20,
                total=closes[-1] / closes[0] - 1)


def turbo_value(S, K, call):
    intrinsic = (S - K) if call else (K - S)
    return max(intrinsic, 0.0) + PREMIUM * S


def simulate(bars, kind, x, d, t, L=16, H=24, directions=("call", "put")):
    """One rule, one portfolio: at most one position, stake 20,000, buy only
    8:00-22:00, exit at target t, on knock-out, after H bars or at 22:00.
    kind = 'reversion' (buy a call after a drop of x from the L-bar high, a put after a rise of x from the low)
    kind = 'breakout'  (buy a call after a rise of x within 4 bars, a put after a drop of x)"""
    trades = []
    pos = None
    buys_per_day = {}
    for i in range(L, len(bars)):
        ts, o, h, l, c = bars[i]
        if pos:
            call = pos["call"]; K = pos["K"]
            ko = (l <= K) if call else (h >= K)
            if ko:
                trades.append(dict(t0=pos["t0"], t1=ts, r=-1.0, reason="KO", call=call)); pos = None; continue
            target = c >= pos["S0"] * (1 + t) if call else c <= pos["S0"] * (1 - t)
            timeout = (i - pos["i"]) >= H or ts.hour >= H_END - 1 and ts.minute >= 45
            if target or timeout:
                w1 = turbo_value(c, K, call) * (1 - SPREAD / 2)
                r = w1 / pos["w0"] - 1
                trades.append(dict(t0=pos["t0"], t1=ts, r=r, reason="TARGET" if target else "TIME", call=call)); pos = None
            continue
        if not (H_START <= ts.hour < H_END - 1):
            continue
        day = ts.date()
        if buys_per_day.get(day, 0) >= 20:
            continue
        window = bars[i - L:i]
        sig = None
        if kind == "reversion":
            hi = max(b[2] for b in window); lo = min(b[3] for b in window)
            if "call" in directions and c <= hi * (1 - x):
                sig = True
            elif "put" in directions and c >= lo * (1 + x):
                sig = False
        else:
            c4 = bars[i - 4][4]
            if "call" in directions and c >= c4 * (1 + x):
                sig = True
            elif "put" in directions and c <= c4 * (1 - x):
                sig = False
        if sig is None:
            continue
        K = c * (1 - d) if sig else c * (1 + d)
        w0 = turbo_value(c, K, sig) * (1 + SPREAD / 2)
        pos = dict(call=sig, K=K, S0=c, w0=w0, i=i, t0=ts)
        buys_per_day[day] = buys_per_day.get(day, 0) + 1
    return trades


def evaluate(trades, bars):
    if not trades:
        return dict(n=0)
    pl = [STAKE * tr["r"] - 2 * FEE for tr in trades]
    weeks = {}
    for tr, p in zip(trades, pl):
        weeks.setdefault(tr["t1"].isocalendar()[1], 0.0)
        weeks[tr["t1"].isocalendar()[1]] += p
    w = list(weeks.values())
    return dict(n=len(trades), hit_rate=sum(1 for tr in trades if tr["r"] > 0) / len(trades),
                ko=sum(1 for tr in trades if tr["reason"] == "KO") / len(trades),
                r_med=st.median(tr["r"] for tr in trades), r_mean=st.mean(tr["r"] for tr in trades),
                pl=sum(pl), best_week=max(w), worst_week=min(w), weeks_up=sum(1 for v in w if v > 0), weeks=len(w))


def hold(bars, d, max_days=5):
    """Comparison: buy a turbo at distance d and hold it. Random entries (every
    bar 8:00-22:00): P(knock-out within max_days trading days), median of the
    best multiple before the knock-out."""
    ko, best, n = 0, [], 0
    for call in (True, False):
        for i in range(0, len(bars) - 96 * max_days, 8):
            ts, o, h, l, c = bars[i]
            if not (H_START <= ts.hour < H_END - 1):
                continue
            K = c * (1 - d) if call else c * (1 + d)
            w0 = turbo_value(c, K, call) * (1 + SPREAD / 2)
            n += 1; bm = 0.0; dead = False
            for b in bars[i + 1:i + 1 + 56 * max_days]:   # ~56 bars per trading day (14 h)
                if (b[3] <= K) if call else (b[2] >= K):
                    dead = True; break
                bm = max(bm, turbo_value(b[4], K, call) * (1 - SPREAD / 2) / w0)
            ko += dead; best.append(bm)
    return dict(n=n, p_ko=ko / n, best_med=st.median(best), best_90=sorted(best)[int(0.9 * len(best))])


def main():
    ap = argparse.ArgumentParser(description="Intraday measurement on 15-minute bars (regime, hold vs. zigzag, mechanical rules).")
    ap.add_argument("--asset", default=None, help="Yahoo symbol for sections 2 and 3, e.g. BZ=F (default: all in section 2, BZ=F in section 3)")
    ap.add_argument("--data-dir", default=DATA, help=f"directory with {BARS_FILE} (default: data/ in the repo root)")
    a = ap.parse_args()
    data = load(a.data_dir)
    if a.asset and a.asset not in data:
        sys.exit(f"Unknown asset {a.asset}; available: {', '.join(data)}.")
    print("# Intraday measurement, 15-minute bars, 60 days to 4 Sep 2026 (Yahoo)\n")
    print("## 1. Regime\n")
    print(f"{'Asset':8} {'Days':>4} {'Range/day':>10} {'Net/day':>9} {'Eff 10d':>11} {'Run 5d':>8} {'Run 20d':>9} {'60d':>7}")
    for s, bars in data.items():
        r = regime(bars)
        print(f"{s:8} {r['days']:4d} {r['range_med']*100:9.2f}% {r['net_med']*100:8.2f}% {r['eff_med']:11.2f} {r['run5']*100:7.1f}% {r['run20']*100:8.1f}% {r['total']*100:+6.1f}%")
    print("\nRange/day = median high-low; Net/day = median |close-open|; Eff 10d = |10-day move| / sum of the daily moves (1 = pure trend, 0 = zigzag); Run = largest move over 5 or 20 trading days.\n")

    print("## 2. Holding versus zigzag: turbo at distance d, random entry, 5 trading days\n")
    print(f"{'Asset':8} {'d':>5} {'P(KO 5d)':>9} {'best multiple, median':>22} {'90% q':>6}")
    for s, bars in data.items():
        if a.asset and s != a.asset:
            continue
        for d in (0.01, 0.02, 0.03):
            r = hold(bars, d)
            print(f"{s:8} {d*100:4.0f}% {r['p_ko']*100:8.0f}% {r['best_med']:22.2f} {r['best_90']:6.2f}")

    print("\n## 3. Mechanical intraday rules, Brent, stake 20,000 per buy, spread 3%, EUR 7.80 per round trip\n")
    bars = data.get(a.asset or "BZ=F")
    print(f"{'Rule':10} {'x':>5} {'d':>5} {'t':>5} {'n':>4} {'Hits':>7} {'KO':>5} {'r med':>7} {'r mean':>7} {'P/L 60d':>10} {'best wk':>9} {'worst wk':>9} {'W+/W':>6}")
    for kind in ("reversion", "breakout"):
        for x in (0.01, 0.02):
            for d in (0.01, 0.015):
                for t in (0.01, 0.02):
                    tr = simulate(bars, kind, x, d, t)
                    r = evaluate(tr, bars)
                    if r["n"] == 0:
                        print(f"{kind:10} {x*100:4.0f}% {d*100:4.1f}% {t*100:4.0f}%    0"); continue
                    print(f"{kind:10} {x*100:4.0f}% {d*100:4.1f}% {t*100:4.0f}% {r['n']:4d} {r['hit_rate']*100:6.0f}% {r['ko']*100:4.0f}% {r['r_med']*100:+6.0f}% {r['r_mean']*100:+6.0f}% {r['pl']:10,.0f} {r['best_week']:9,.0f} {r['worst_week']:9,.0f} {r['weeks_up']:2d}/{r['weeks']:<2d}")
    print("\nx = trigger (drop from the 4h high or rise within 1h), d = distance to the barrier, t = target gain in the underlying. Exit at target, on knock-out, after 6 h or at 21:45. In-sample, one regime phase, no optimisation beyond the grid.")


if __name__ == "__main__":
    main()

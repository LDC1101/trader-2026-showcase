"""
Candidate ranking: which underlying carries the EUR 20,000 bet?

The question is not "what goes up" but: on which underlying has a turbo
position with a 1-2% distance to the barrier, held for 40 trading days and
taken in both directions (two portfolios, only the better one counts), most
often reached 64x in the past, and how often did it survive at all?

Method: no GBM, the real daily paths. For every start day of the last three
years the strategy is played through: entry at the close, knock-out as soon as
the daily low (long) or daily high (short) touches the barrier, otherwise a
payout after H days of (move + distance) / distance. This is a backtest on
overlapping windows, not a forecast. It measures how trend and noise of the
underlying have related to each other, the quantity that put gold (1.1% daily
volatility, +51% in eight weeks) ahead of oil in 2025.

Limitations:
- Daily low/high instead of ticks. The low is the day's minimum, so no touch
  is missed, but the BEST window (only 9:00-17:30 counts) is not modelled.
  Futures trade almost around the clock.
- ~700 overlapping windows from three years are strongly autocorrelated.
  The percentages are orders of magnitude, not probabilities.
- Cross-check: the gold window of autumn 2025 must show up as a top value.
  If it does not, the calculator is wrong, not the world.

Usage:   python3 src/candidates.py
         python3 src/candidates.py --horizon 20 --write
         python3 src/candidates.py --conditional --data-dir /path/to/cache
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
TARGET = 1_350_000 / 20_000          # 67.5x: the 2025 winning mark from EUR 20,000
DISTANCES = (0.010, 0.015, 0.020, 0.030)

# (display name, file, note). Order = order in the detail section.
CANDIDATES = [
    ("Brent",       "brent.csv",   "Future, Yahoo BZ=F"),
    ("WTI",         "wti.csv",     "Future, Yahoo CL=F"),
    ("Gold",        "gold.csv",    "Future, Yahoo GC=F"),
    ("Silver",      "silver.csv",  "Future, Yahoo SI=F"),
    ("Copper",      "copper.csv",  "Future, Yahoo HG=F"),
    ("Natural gas", "natgas.csv",  "Future, Yahoo NG=F"),
    ("S&P 500",     "spx.csv",     "Index"),
    ("Nasdaq 100",  "ndx.csv",     "Index"),
    ("DAX",         "dax.csv",     "Index"),
    ("VIX",         "vix.csv",     "Index, not directly tradable"),
    ("TLT",         "tlt.csv",     "US long-bond ETF (rates)"),
    ("NVDA",        "nvda.csv",    "Stock"),
    ("SOXX",        "soxx.csv",    "Semiconductor ETF"),
    ("CEG",         "ceg.csv",     "Stock, nuclear power"),
    ("GEV",         "gev.csv",     "Stock, grid/turbines"),
    ("OKLO",        "oklo.csv",    "Stock, SMR, very volatile"),
    ("SMR",         "smr.csv",     "Stock, NuScale, very volatile"),
    ("URA",         "ura.csv",     "Uranium ETF"),
]

# How the price CSVs were originally obtained (used in the missing-data message).
PRICE_SOURCE = ("daily OHLC CSVs with columns date,open,high,low,close covering three years, originally "
                "downloaded from Yahoo Finance in the browser because curl got HTTP 429; stocks and ETFs "
                "cross-checked against the Nasdaq API")


def missing_data_message(data_dir):
    files = ", ".join(f for _, f, _ in CANDIDATES)
    return f"No price data in {data_dir}: expected {files} ({PRICE_SOURCE})."


def load(filename, data_dir=None):
    path = os.path.join(data_dir or DATA, filename)
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    d = np.array([x["date"] for x in rows])
    o = np.array([float(x["open"]) for x in rows])
    h = np.array([float(x["high"]) for x in rows])
    l = np.array([float(x["low"]) for x in rows])
    c = np.array([float(x["close"]) for x in rows])
    ok = (c > 0) & (l > 0) & (h > 0)
    return d[ok], o[ok], h[ok], l[ok], c[ok]


def backtest(h, l, c, distance, H):
    """For every start day i: long and short with the barrier at `distance`,
    held for H days. Returns the multiple per direction (0 = knocked out) and
    the knock-out day (H+1 = survived)."""
    n = len(c) - H
    m_long = np.zeros(n); m_short = np.zeros(n)
    ko_long = np.full(n, H + 1); ko_short = np.full(n, H + 1)
    for i in range(n):
        s0 = c[i]
        window_l = l[i + 1:i + H + 1]
        window_h = h[i + 1:i + H + 1]
        end = c[i + H] / s0 - 1.0
        hit = np.nonzero(window_l <= s0 * (1 - distance))[0]
        if hit.size:
            ko_long[i] = hit[0] + 1
        else:
            m_long[i] = (end + distance) / distance
        hit = np.nonzero(window_h >= s0 * (1 + distance))[0]
        if hit.size:
            ko_short[i] = hit[0] + 1
        else:
            m_short[i] = (-end + distance) / distance
    return m_long, m_short, ko_long, ko_short


def conditional(h, l, c, H, distance, threshold=1.0):
    """Only start days on which the underlying already shows a 20-day trend
    (|return / (sigma*sqrt(20))| > threshold). Compares a position WITH the
    trend and AGAINST the trend; as a reference, start days without a trend
    (|trend/noise| < 0.3) with the better of the two portfolios. Measures
    whether moves in this underlying persist or reverse, the question behind
    a 'running catalyst'."""
    ml, ms, kl, ks = backtest(h, l, c, distance, H)
    n = len(ml)
    r = np.diff(np.log(c))
    with_trend, against, no_trend = [], [], []
    for i in range(21, n):
        s20 = r[i - 20:i].std()
        if s20 <= 0:
            continue
        tr = (c[i] / c[i - 20] - 1) / (s20 * np.sqrt(20))
        if abs(tr) > threshold:
            with_trend.append(ml[i] if tr > 0 else ms[i])
            against.append(ms[i] if tr > 0 else ml[i])
        elif abs(tr) < 0.3:
            no_trend.append(max(ml[i], ms[i]))

    def stat(x):
        x = np.array(x)
        if x.size == 0:
            return dict(n=0, surv=0, p3=0, p10=0, med=0)
        return dict(n=x.size, surv=(x > 0).mean(), p3=(x >= 3).mean(), p10=(x >= 10).mean(),
                    med=np.median(x[x > 0]) if (x > 0).any() else 0.0)
    return stat(with_trend), stat(against), stat(no_trend)


def metrics(d, o, h, l, c, H):
    r = np.diff(np.log(c))
    sig20 = r[-20:].std(); sig60 = r[-60:].std(); sig_all = r.std()
    ret20 = c[-1] / c[-21] - 1
    ret60 = c[-1] / c[-61] - 1
    # Trend/noise: mean absolute H-day move relative to sigma*sqrt(H).
    # Pure chance (GBM) gives ~0.80. Above that, moves persist.
    moves = np.abs(np.log(c[H:] / c[:-H]))
    trend_noise = moves.mean() / (sig_all * np.sqrt(H))
    today = dict(close=c[-1], sig20=sig20, sig60=sig60, ret20=ret20, ret60=ret60,
                 tr=trend_noise, cur_tr=(ret20 / (sig20 * np.sqrt(20))) if sig20 > 0 else 0.0,
                 high20=h[-20:].max(), low20=l[-20:].min(), date=d[-1])
    results = {}
    for a in DISTANCES:
        ml, ms, kl, ks = backtest(h, l, c, a, H)
        better = np.maximum(ml, ms)
        surv_either = ((ml > 0) | (ms > 0)).mean()
        results[a] = dict(
            p_surv=surv_either,
            p_surv_long=(ml > 0).mean(), p_surv_short=(ms > 0).mean(),
            p64=(better >= TARGET).mean(), p10=(better >= 10).mean(), p3=(better >= 3).mean(),
            med=np.median(better[better > 0]) if (better > 0).any() else 0.0,
            best=better.max(), best_i=int(better.argmax()),
            ko_median=np.median(np.minimum(kl, ks)),
        )
    return today, results


def main():
    ap = argparse.ArgumentParser(description="Candidate ranking: which underlying carries the EUR 20,000 bet?")
    ap.add_argument("--horizon", type=int, default=40, help="trading days, default 40 = game length")
    ap.add_argument("--write", action="store_true",
                    help="also write the result to <data-dir>/candidates_<date>_H<horizon>.md")
    ap.add_argument("--conditional", action="store_true",
                    help="additionally: entry into an existing trend, with vs. against")
    ap.add_argument("--data-dir", default=DATA, help="directory with the price CSVs (default: data/ in the repo root)")
    args = ap.parse_args()
    H = args.horizon
    rows = []
    out = []
    P = out.append
    P(f"# Candidate ranking, {dt.date.today().isoformat()}, horizon {H} trading days")
    P("")
    P(f"Target: {TARGET:.1f}x (EUR 1.35M from EUR 20,000). Both directions held, the better portfolio counts.")
    P("Backtest over every start day of the last three years, knock-out on the daily low/high.")
    P("")
    missing = 0
    for name, filename, note in CANDIDATES:
        try:
            d, o, h, l, c = load(filename, args.data_dir)
        except FileNotFoundError:
            missing += 1
            P(f"- {name}: no data ({filename})"); continue
        if len(c) < H + 60:
            P(f"- {name}: too little data ({len(c)} days)"); continue
        today, res = metrics(d, o, h, l, c, H)
        rows.append((name, note, today, res, d))
    if missing == len(CANDIDATES):
        sys.exit(missing_data_message(args.data_dir))

    # ---- Ranking ---------------------------------------------------------
    rows.sort(key=lambda z: (z[3][0.010]["p64"], z[3][0.015]["p64"], z[3][0.010]["p10"]), reverse=True)
    P("## Ranking by P(>=67.5x) at 1.0% distance")
    P("")
    P("| # | Underlying | sigma_d 20d | Trend/noise | P(survives 1%) | P(>=67x 1%) | P(>=10x 1%) | P(>=67x 1.5%) | P(>=10x 2%) | best window 1% |")
    P("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k, (name, note, td, res, d) in enumerate(rows, 1):
        e1, e15, e2 = res[0.010], res[0.015], res[0.020]
        P(f"| {k} | {name} | {td['sig20']:.2%} | {td['tr']:.2f} | {e1['p_surv']:.1%} | {e1['p64']:.2%} | {e1['p10']:.1%} | {e15['p64']:.2%} | {e2['p10']:.1%} | {e1['best']:.0f}x from {d[e1['best_i']]} |")
    P("")
    P("Trend/noise: mean absolute 40-day move divided by sigma*sqrt(40). Pure chance = 0.80.")
    P("")

    # ---- State today -----------------------------------------------------
    P("## State on the last trading day")
    P("")
    P("| Underlying | Close | 20d return | 60d return | current trend/noise (20d) | distance to 20d high | distance to 20d low |")
    P("|---|---:|---:|---:|---:|---:|---:|")
    for name, note, td, res, d in rows:
        P(f"| {name} | {td['close']:.2f} | {td['ret20']:+.1%} | {td['ret60']:+.1%} | {td['cur_tr']:+.2f} | {td['close']/td['high20']-1:+.1%} | {td['close']/td['low20']-1:+.1%} |")
    P("")

    # ---- Detail per distance ---------------------------------------------
    P("## Detail: survival and multiple by distance")
    P("")
    for name, note, td, res, d in rows:
        P(f"### {name}: {note}, data through {td['date']}")
        P("")
        P("| Distance | Leverage | P(one side survives) | P(long) | P(short) | Median knock-out day | Median multiple (survivors) | P(>=3x) | P(>=10x) | P(>=67x) | Max |")
        P("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for a in DISTANCES:
            e = res[a]
            P(f"| {a:.1%} | {1/a:.0f} | {e['p_surv']:.1%} | {e['p_surv_long']:.1%} | {e['p_surv_short']:.1%} | {e['ko_median']:.0f} | {e['med']:.1f}x | {e['p3']:.1%} | {e['p10']:.1%} | {e['p64']:.2%} | {e['best']:.0f}x ({d[e['best_i']]}) |")
        P("")

    # ---- Conditional: entry into a running trend -------------------------
    if args.conditional:
        P("## Conditional: entry into an existing 20-day trend (|trend/noise| > 1)")
        P("")
        P("Question: does the move persist (WITH) or reverse (AGAINST)? NONE = start days without a trend, better side.")
        P("")
        files = dict((k, v) for k, v, _ in CANDIDATES)
        for a in (0.010, 0.020):
            P(f"### Distance {a:.1%}")
            P("")
            P("| Underlying | n trend days | WITH: survives | WITH: >=3x | WITH: >=10x | WITH: median | AGAINST: survives | AGAINST: >=3x | AGAINST: >=10x | NONE: survives | NONE: >=10x |")
            P("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
            for name, note, td, res, d in rows:
                dd, o, h, l, c = load(files[name], args.data_dir)
                w, g, n_ = conditional(h, l, c, H, a)
                P(f"| {name} | {w['n']} | {w['surv']:.1%} | {w['p3']:.1%} | {w['p10']:.1%} | {w['med']:.1f}x | {g['surv']:.1%} | {g['p3']:.1%} | {g['p10']:.1%} | {n_['surv']:.1%} | {n_['p10']:.1%} |")
            P("")

    # ---- Cross-check gold 2025 -------------------------------------------
    gold = next((z for z in rows if z[0] == "Gold"), None)
    if gold:
        name, note, td, res, d = gold
        e = res[0.010]
        P("## Cross-check: gold, autumn 2025")
        P("")
        P(f"Best 1% window: {e['best']:.0f}x from {d[e['best_i']]}. The 2025 winner held a BEST turbo on gold with a gain of about 5,000% (~51x).")
        P("If the best window falls in autumn 2025 and is of this order of magnitude, the calculator measures the right thing.")
        P("")

    text = "\n".join(out)
    print(text)
    if args.write:
        path = os.path.join(args.data_dir, f"candidates_{dt.date.today().isoformat()}_H{H}.md")
        with open(path, "w") as f:
            f.write(text + "\n")
        print(f"\n-> written: {path}")


if __name__ == "__main__":
    main()

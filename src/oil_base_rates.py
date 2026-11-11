"""
Oil base rates from the EIA spot series (Brent since 1987, WTI since 1986).

Two questions, neither of them a directional forecast:

1. How often does oil move +66% in 40 trading days (what a 1% long turbo needs
   for the winning mark) or -25% (the Strait of Hormuz reopens)?
2. Does a running 20-day trend persist or reverse? On three years of Yahoo
   data with daily lows it looked as if oil reverses reliably
   (candidates.py --conditional: 1.7% survival with the trend, 14% against it).
   Over 39 years the difference is gone. The three-year pattern is a regime
   artifact of 2024-2026, not a property of oil.

Closing prices only: survival is overstated (no daily low), but the ratios
between the groups hold.

Usage:   python3 src/oil_base_rates.py [--data-dir DIR]
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
H = 40
DISTANCE = 0.01

SERIES = ("brent", "wti")
LABELS = {"brent": "Brent spot daily closes since 1987", "wti": "WTI spot daily closes since 1986"}
SOURCE = ("EIA {label}, columns date,close; originally fetched with curl "
          "from the EIA spot price history HTML table")


def path_for(name, data_dir):
    return os.path.join(data_dir, f"eia_{name}.csv")


def require(data_dir):
    for name in SERIES:
        path = path_for(name, data_dir)
        if not os.path.exists(path):
            sys.exit(f"Missing data file {path} ({SOURCE.format(label=LABELS[name])}).")


def load(name, data_dir=DATA):
    with open(path_for(name, data_dir)) as f:
        rows = list(csv.DictReader(f))
    return [x["date"] for x in rows], np.array([float(x["close"]) for x in rows])


def episodes(dates, moves, threshold, above=True):
    idx = np.nonzero(moves >= threshold)[0] if above else np.nonzero(moves <= threshold)[0]
    out = []
    for i in idx:
        if not out or (dt.date.fromisoformat(dates[i]) - dt.date.fromisoformat(out[-1])).days > 60:
            out.append(dates[i])
    return out


def base_rates(name, data_dir=DATA):
    d, c = load(name, data_dir)
    mv = c[H:] / c[:-H] - 1
    print(f"--- {name.upper()} {d[0]}..{d[-1]}, {len(mv)} windows of {H} days")
    for th in (0.10, 0.17, 0.25, 0.35, 0.56, 0.66):
        print(f"   P(+{th:.0%}) {(mv >= th).mean():6.2%}   P(-{th:.0%}) {(mv <= -th).mean():6.2%}")
    print("   windows >= +40%:", ", ".join(episodes(d, mv, 0.40)))
    print("   windows <= -35%:", ", ".join(episodes(d, mv, -0.35, False)))
    print(f"   last 40 days: {c[-1]/c[-41]-1:+.1%}, last 20: {c[-1]/c[-21]-1:+.1%}")


def trend_persistence(name, data_dir=DATA, threshold=1.0):
    d, c = load(name, data_dir)
    lr = np.diff(np.log(c))

    def long_(i):
        s0 = c[i]; w = c[i + 1:i + H + 1]
        return 0.0 if (w <= s0 * (1 - DISTANCE)).any() else (c[i + H] / s0 - 1 + DISTANCE) / DISTANCE

    def short(i):
        s0 = c[i]; w = c[i + 1:i + H + 1]
        return 0.0 if (w >= s0 * (1 + DISTANCE)).any() else (1 - c[i + H] / s0 + DISTANCE) / DISTANCE

    with_trend, against, no_trend, up_long, up_short = [], [], [], [], []
    for i in range(21, len(c) - H):
        s20 = lr[i - 20:i].std()
        if s20 <= 0:
            continue
        tr = (c[i] / c[i - 20] - 1) / (s20 * np.sqrt(20))
        if abs(tr) > threshold:
            with_trend.append(long_(i) if tr > 0 else short(i))
            against.append(short(i) if tr > 0 else long_(i))
            if tr > 0:
                up_long.append(long_(i)); up_short.append(short(i))
        elif abs(tr) < 0.3:
            no_trend.append(max(long_(i), short(i)))
    print(f"--- {name.upper()}: entry when |20-day trend/noise| > {threshold}")
    for label, x in (("with trend", with_trend), ("against trend", against),
                     ("no trend, better side", no_trend),
                     ("after uptrend: long", up_long), ("after uptrend: short", up_short)):
        x = np.array(x)
        print(f"   {label:28s} n={x.size:5d}  survives {(x > 0).mean():6.1%}  >=3x {(x >= 3).mean():6.1%}"
              f"  >=10x {(x >= 10).mean():6.1%}  max {x.max():.0f}x")


def main():
    ap = argparse.ArgumentParser(description="Oil base rates from the EIA spot series (closing prices only).")
    ap.add_argument("--data-dir", default=DATA,
                    help="directory with eia_brent.csv and eia_wti.csv (default: data/ in the repo root)")
    a = ap.parse_args()
    require(a.data_dir)
    print("=" * 76)
    print("Oil base rates, EIA spot, closing prices only")
    print("=" * 76)
    for n in SERIES:
        base_rates(n, a.data_dir)
    print()
    for n in SERIES:
        trend_persistence(n, a.data_dir)
    print("""
  Reading: over 40 years the question "with or against the trend" is a draw
  for oil. The large multiples (>100x) came from long positions after
  uptrends that were already running: 1990, 2022, 2026. For the winning mark
  Brent needs +66% in 40 days; that happened in 0.8% of the windows, -66%
  practically never. The short side is therefore an instrument for a good
  rank and the weekly prize, not for the main prize.
""")


if __name__ == "__main__":
    main()

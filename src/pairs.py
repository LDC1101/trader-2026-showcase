"""
Portfolio pairs: which combination of two positions (one underlying and one
direction each, EUR 20,000, 1% barrier, held for 40 days) has most often
brought at least ONE side to 10x or to the winning mark?

For the main prize only the better of the two portfolios counts. The thesis in
strategy/00-thesis.md puts both portfolios on the same theme in opposite
directions. This script measures that against every other pairing (same
direction, opposite directions, two themes) on the same daily paths as
candidates.py.

Usage:   python3 src/pairs.py [--distance 0.01] [--horizon 40] [--top 15]
"""

import argparse
import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candidates import CANDIDATES, DATA, TARGET, backtest, load, missing_data_message  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Portfolio pairs: which two positions most often bring one side to 10x or the winning mark?")
    ap.add_argument("--distance", type=float, default=0.01, help="distance to the barrier (default 0.01 = 1%%)")
    ap.add_argument("--horizon", type=int, default=40, help="trading days held (default 40)")
    ap.add_argument("--top", type=int, default=15, help="rows per top list (default 15)")
    ap.add_argument("--data-dir", default=DATA, help="directory with the price CSVs (default: data/ in the repo root)")
    args = ap.parse_args()
    H, a = args.horizon, args.distance

    legs = {}   # (name, direction) -> {date: multiple}
    for name, filename, _ in CANDIDATES:
        try:
            d, o, h, l, c = load(filename, args.data_dir)
        except FileNotFoundError:
            continue
        ml, ms, _, _ = backtest(h, l, c, a, H)
        legs[(name, "long")] = dict(zip(d[:len(ml)], ml))
        legs[(name, "short")] = dict(zip(d[:len(ms)], ms))
    if not legs:
        sys.exit(missing_data_message(args.data_dir))

    rows = []
    for (b1, b2) in itertools.combinations(legs.keys(), 2):
        common = sorted(set(legs[b1]) & set(legs[b2]))
        if len(common) < 300:
            continue
        x = np.array([max(legs[b1][t], legs[b2][t]) for t in common])
        rows.append((b1, b2, len(common), (x > 0).mean(), (x >= 3).mean(), (x >= 10).mean(), (x >= TARGET).mean(), np.median(x[x > 0]) if (x > 0).any() else 0))

    header = ("| Depot A | Depot B | n | one side alive | >=3x | >=10x | >=67x | median (alive) |\n"
              "|---|---|---:|---:|---:|---:|---:|---:|")

    def show(title, key, n):
        print(f"\n## {title}  (distance {a:.1%}, {H} days)\n")
        print(header)
        for b1, b2, m, s, p3, p10, p67, med in sorted(rows, key=key, reverse=True)[:n]:
            print(f"| {b1[0]} {b1[1]} | {b2[0]} {b2[1]} | {m} | {s:.1%} | {p3:.1%} | {p10:.1%} | {p67:.2%} | {med:.1f}x |")

    show("Top by P(>=10x)", lambda z: (z[5], z[6]), args.top)
    show("Top by P(>=67x, winning mark)", lambda z: (z[6], z[5]), args.top)

    print("\n## Reference pairs\n")
    print(header)
    ref = [(("Brent", "long"), ("Brent", "short")), (("Gold", "long"), ("Gold", "short")),
           (("Silver", "long"), ("Silver", "short")), (("WTI", "long"), ("WTI", "short")),
           (("Brent", "long"), ("Gold", "long")), (("Brent", "short"), ("Gold", "long")),
           (("Brent", "long"), ("Silver", "long")), (("Brent", "short"), ("Silver", "long")),
           (("Brent", "long"), ("Gold", "short")), (("Gold", "long"), ("Silver", "long")),
           (("NVDA", "long"), ("NVDA", "short")), (("DAX", "long"), ("DAX", "short"))]
    for r1, r2 in ref:
        for z in rows:
            if {z[0], z[1]} == {r1, r2}:
                b1, b2, m, s, p3, p10, p67, med = z
                print(f"| {b1[0]} {b1[1]} | {b2[0]} {b2[1]} | {m} | {s:.1%} | {p3:.1%} | {p10:.1%} | {p67:.2%} | {med:.1f}x |")


if __name__ == "__main__":
    main()

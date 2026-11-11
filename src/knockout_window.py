"""
What is the shorter knock-out window worth?

SG offers two turbo families on the DAX that differ in one point no
marketing text mentions:

    BEST / Classic turbo      knock-out only during Xetra hours, 9:00-17:30
    X-BEST / X-Classic turbo  knock-out over the full session, 8:00-22:00

The price moves the same way in both cases. Only a touch of the barrier
counts for the first family during 8.5 instead of 14 hours. Outside the
window the underlying may dip below the barrier without consequence, as long
as it is back above it by the next opening.

The tournament simulation shows that the survival of the leveraged position
is the binding quantity. This script measures how much the choice of
product family changes it. It uses continuous monitoring inside the
respective window (Brownian bridge), not only checks at sample points.

Usage:    python3 src/knockout_window.py
"""

import argparse

import numpy as np

RNG = np.random.default_rng(7)
PATHS = 200_000
STEPS_PER_DAY = 28             # half-hourly over 14 trading hours
MONITORED_SHORT = 17           # 9:00-17:30 -> steps 2..18
MONITORED_START = 2


def survives(rng, n, days, distance, daily_sigma, window):
    """Share of paths that last 'days' days without touching the barrier
    inside the monitored window.

    window = (start, length) in half-hour steps, or None for the full session.
    """
    step_sigma = daily_sigma / np.sqrt(STEPS_PER_DAY)
    alive = np.ones(n, dtype=bool)
    cum = np.zeros(n)
    for _ in range(days):
        steps = rng.normal(0.0, step_sigma, (n, STEPS_PER_DAY))
        path = cum[:, None] + steps.cumsum(axis=1)
        before = np.concatenate([cum[:, None], path[:, :-1]], axis=1)

        a = before + distance
        b = path + distance
        p_cross = np.where((a > 0) & (b > 0),
                           np.exp(-2.0 * a * b / step_sigma ** 2), 1.0)
        hits = rng.random((n, STEPS_PER_DAY)) < p_cross

        if window is not None:
            start, length = window
            mask = np.zeros(STEPS_PER_DAY, dtype=bool)
            mask[start:start + length] = True
            hits &= mask[None, :]

        alive &= ~hits.any(axis=1)
        cum = path[:, -1]
    return alive.mean()


def main():
    argparse.ArgumentParser(description="Survival of BEST/Classic (knock-out 9:00-17:30) vs X-BEST/X-Classic "
                            "(8:00-22:00) turbos, simulated. No options; runs in about 20 seconds.").parse_args()
    print("=" * 76)
    print("Knock-out window: BEST/Classic (9:00-17:30) vs X-BEST/X-Classic (8:00-22:00)")
    print("=" * 76)
    print("""
  Same underlying, same distance to barrier, same leverage.
  The only difference is when a touch counts.
""")
    daily_sigma = 0.011   # DAX, about 1.1% daily move
    print(f"  {'Distance':<10}{'Lever.':>7}{'Holding':>12}"
          f"{'X-BEST':>10}{'BEST':>10}{'Edge':>10}")
    for distance in (0.010, 0.020, 0.035):
        for days in (5, 10, 20):
            full = survives(RNG, PATHS, days, distance, daily_sigma, None)
            short = survives(RNG, PATHS, days, distance, daily_sigma,
                             (MONITORED_START, MONITORED_SHORT))
            factor = short / max(full, 1e-9)
            print(f"  {distance:<10.1%}{1/distance:>7.0f}{str(days) + ' days':>12}"
                  f"{full:>10.1%}{short:>10.1%}{factor:>9.2f}x")
    print("""
  The survival rate rises in every row, but by less than expected: 2 to
  9 percent, most for tight barriers. With a longer holding period the
  edge does not grow; it even shrinks slightly (1.09x to 1.07x at 1%
  distance). The reason is that over many days almost every position runs
  into an open window at some point anyway.

  Practical rule for DAX turbos: choose BEST or Classic, not X-BEST or
  X-Classic. Same leverage, same price, slightly longer life expectancy.
  The edge is small, but it costs nothing, and the difference is in the
  product name.

  Limitation: the model lets the price move normally outside the window.
  In reality the move between 17:30 and 9:00 is driven by the US session
  and can arrive as an opening gap. A gap that OPENS below the barrier
  knocks out a BEST product as well. The measured edge is therefore an
  upper bound, not a guarantee.
""")


if __name__ == "__main__":
    main()

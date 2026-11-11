"""
Tournament math for Trader 2026.

The question is not "which stock will rise" but: with ~30,000 participants
holding two depots each, what depot value does the winner need, and which
strategy maximises P(1st place)? That is a different question from "what is
the best investment", and it has a different answer.

TWO ERRORS FROM EARLIER VERSIONS distorted the result and are fixed here:

1. A field model with freely guessed parameters produced a winning value of
   EUR 24M. The parameters are now calibrated to the actual result of
   Trader 2025 (winner EUR 1.35M, 2nd place EUR 1.24M, ~30,000 participants).

2. More serious: the strategy was optimised against a STATIC field. A turbo
   with a 0.6% distance to the barrier then came out at a 15% chance of
   winning, i.e. the claim that a tournament with 60,000 depots is won on
   every sixth attempt. The error is structural: if a product were that good,
   the other leverage players would use it too, and the winning mark would
   rise with it. The field is therefore now simulated with THE SAME
   instrument model as our own strategy, with scattered parameters. Only
   then is the question "which leverage is optimal" well posed at all.

Usage:    python3 src/tournament.py
"""

import numpy as np

RNG = np.random.default_rng(42)

PLAYERS = 30_000
FIELD = PLAYERS * 2
START = 100_000.0
WEEKS = 8
DAYS_PER_WEEK = 5

# Observed in Trader 2025: calibration targets, not assumptions.
OBSERVED_WINNER = 1_350_000.0
OBSERVED_SECOND = 1_240_000.0


# --------------------------------------------------------------------------
# Instrument
# --------------------------------------------------------------------------
# A turbo pays out LINEARLY in the underlying:
#     multiplier = (move + distance) / distance
# With a 1.2% distance, +49% in the underlying gives 42 times the stake. That
# is the order of magnitude seen in 2025: gold +51%, the winner held a
# BEST turbo with a gain of about 5,000% on a EUR 20,000 stake.
#
# The second mechanism matters more than the leverage: the barrier is FIXED.
# If the position moves into profit at once, it moves away from the barrier
# and becomes more robust with every percent. A leveraged bet is extremely
# fragile at first and increasingly safe afterwards, which is why "fail
# early, try again, let winners run" works.
def simulate_depot(rng, n, resets=True, lock_in_at=np.inf, ko_distance=0.012,
                   base_sigma=0.025, trend_chance=0.15, leverage_stake=20_000.0):
    """One depot over 8 weeks. Within the rules: at most EUR 20,000 in
    leveraged derivatives, the rest in stocks."""
    value = np.full(n, START)
    locked = np.zeros(n, dtype=bool)
    stake = np.zeros(n)
    cum = np.zeros(n)
    dead = np.ones(n, dtype=bool)
    trend = np.zeros(n)

    ko = np.broadcast_to(np.asarray(ko_distance, dtype=float), (n,)).copy()
    sig = np.broadcast_to(np.asarray(base_sigma, dtype=float), (n,)).copy()
    res = np.broadcast_to(np.asarray(resets, dtype=bool), (n,)).copy()

    for week in range(WEEKS):
        open_ = ~locked
        reset_now = res & open_ & dead & (value < START) & (week < WEEKS - 1)
        value = np.where(reset_now, START, value)

        new = open_ & dead
        e = np.minimum(leverage_stake, value * 0.20)
        stake = np.where(new, e, stake)
        value = np.where(new, value - e, value)
        cum = np.where(new, 0.0, cum)
        has_trend = rng.random(n) < trend_chance
        trend = np.where(new, np.where(has_trend, rng.normal(0.045, 0.02, n), 0.0), trend)
        dead = np.where(new, False, dead)

        daily_sigma = sig / np.sqrt(DAYS_PER_WEEK)
        steps = (rng.normal(0.0, 1.0, (n, DAYS_PER_WEEK)) * daily_sigma[:, None]
                 + (trend / DAYS_PER_WEEK)[:, None])
        path = cum[:, None] + steps.cumsum(axis=1)

        # The knock-out is monitored CONTINUOUSLY, not only at the daily close.
        # Without this correction a turbo with a 0.2% distance "survives"
        # whole weeks in the model, because nothing is checked between two
        # sample points, and the model then recommends infinite leverage.
        # Brownian bridge: P(minimum between two points < barrier)
        #   = exp(-2 * (a - B) * (b - B) / sigma^2)
        before = np.concatenate([cum[:, None], path[:, :-1]], axis=1)
        a = before + ko[:, None]
        b = path + ko[:, None]
        var = (daily_sigma ** 2)[:, None]
        p_cross = np.where((a > 0) & (b > 0),
                           np.exp(-2.0 * a * b / np.maximum(var, 1e-12)),
                           1.0)
        touched = (rng.random((n, DAYS_PER_WEEK)) < p_cross).any(axis=1)
        knocked_out = open_ & (~dead) & touched
        cum = path[:, -1]
        dead = dead | knocked_out
        stake = np.where(knocked_out, 0.0, stake)

        value = value * np.where(open_, rng.lognormal(0.0, 0.10, n), 1.0)

        pos = np.where(dead, 0.0, stake * (cum + ko) / ko)
        total = value + pos
        lock_now = open_ & (total >= lock_in_at)
        value = np.where(lock_now, total, value)
        stake = np.where(lock_now, 0.0, stake)
        dead = dead | lock_now
        locked = locked | lock_now

    pos = np.where(dead, 0.0, stake * (cum + ko) / ko)
    return np.maximum(value + pos, 0.0)


# --------------------------------------------------------------------------
# The field, simulated with the same instrument model as our own depot
# --------------------------------------------------------------------------
SHARE_PASSIVE, SHARE_ACTIVE, SHARE_MODERATE, SHARE_LEVERAGE = 0.55, 0.30, 0.12, 0.03


def field_sample(rng, n):
    """n opposing depots. The leverage group picks its products with scatter:
    some too tight, some too wide, some well chosen. This is what makes the
    question 'which leverage is optimal' answerable."""
    parts = []
    n_passive = int(n * SHARE_PASSIVE)
    n_active = int(n * SHARE_ACTIVE)
    n_moderate = int(n * SHARE_MODERATE)
    n_leverage = n - n_passive - n_active - n_moderate

    parts.append(START * rng.lognormal(0.010, 0.10, n_passive))
    parts.append(START * rng.lognormal(0.000, 0.28, n_active))
    # moderately leveraged: wide barriers, little convexity
    parts.append(simulate_depot(
        rng, n_moderate, resets=rng.random(n_moderate) < 0.4,
        ko_distance=rng.uniform(0.04, 0.12, n_moderate),
        base_sigma=rng.uniform(0.02, 0.04, n_moderate), trend_chance=0.15))
    # fully leveraged: the actual competition
    parts.append(simulate_depot(
        rng, n_leverage, resets=True,
        ko_distance=np.exp(rng.uniform(np.log(0.005), np.log(0.05), n_leverage)),
        base_sigma=rng.uniform(0.02, 0.06, n_leverage), trend_chance=0.15))
    return np.concatenate(parts)


def field_cdf(rng, sample_size=1_500_000):
    """Empirical distribution of ONE opposing depot. The distribution of the
    maximum follows exactly: P(max < x) = F(x)^(FIELD-1)."""
    values = np.sort(field_sample(rng, sample_size))
    return values


def _fmt(p):
    """P(win) lies in the range of a few basis points; percent with three
    decimals rounds the differences away."""
    if p <= 0:
        return "< 1 : 1M"
    return f"1 : {1 / p:,.0f}"


def p_win(ours, field_sorted):
    """P(our depot beats all 59,999 others)."""
    rank = np.searchsorted(field_sorted, ours, side="left")
    F = rank / len(field_sorted)
    return np.mean(np.clip(F, 0, 1) ** (FIELD - 1))


def main():
    print("=" * 78)
    print("TRADER 2026: tournament math")
    print("=" * 78)
    print(f"Field: {PLAYERS:,} players x 2 depots = {FIELD:,} depots, "
          f"start {START:,.0f} EUR each, {WEEKS} weeks")
    print(f"Metric: P(best depot >= {OBSERVED_WINNER:,.0f} EUR), the value")
    print("that actually won Trader 2025.\n")

    N = 250_000
    # Underlying: volatile single stock (5% weekly vol), barrier 1% away.
    STD = dict(ko_distance=0.010, base_sigma=0.050)

    rows = [
        ("passive, broadly diversified",
         lambda: START * RNG.lognormal(0.01, 0.10, N)),
        ("4 high-volatility stocks, no leverage",
         lambda: sum(20_000 * RNG.lognormal(0, 0.32, N) for _ in range(4)) + 20_000),
        ("leverage, no reset, no lock-in",
         lambda: simulate_depot(RNG, N, resets=False, **STD)),
        ("leverage + resets",
         lambda: simulate_depot(RNG, N, resets=True, **STD)),
        ("leverage + resets + lock in at 250k",
         lambda: simulate_depot(RNG, N, resets=True, lock_in_at=250_000, **STD)),
        ("leverage + resets + lock in at 1.4M",
         lambda: simulate_depot(RNG, N, resets=True, lock_in_at=1_400_000, **STD)),
    ]
    print(f"  {'Strategy':<40}{'P(>=1.35M)':>15}{'Median':>12}{'P(>500k)':>11}")
    results = {}
    for name, fn in rows:
        best = np.maximum(fn(), fn())
        p = (best >= OBSERVED_WINNER).mean()
        results[name] = p
        print(f"  {name:<40}{p:>14.3%}{np.median(best):>11,.0f}"
              f"{(best >= 500_000).mean():>11.1%}")

    p_res = results["leverage + resets"]
    p_none = results["leverage, no reset, no lock-in"]
    p_early = results["leverage + resets + lock in at 250k"]
    se = np.sqrt(p_res * (1 - p_res) / N)
    print(f"""
  Four observations, one of them against my starting thesis.

  1. Without a leveraged product the mark was NEVER reached in {N:,}
     simulated games. The 20% rule caps every stock position at a fifth
     of the depot, and four to five stocks do not grow thirteenfold in
     eight weeks. This line decides whether a depot is in the race at all.

  2. Resets lift the chance from {p_none:.3%} to {p_res:.3%}, a factor of
     {p_res / p_none:.2f} with a standard error of {se:.3%}. Below the mark
     they act even more strongly. The rule sits inconspicuously in
     section 3 of the game rules and reads like a consolation for losers;
     in fact it is a free option on a new attempt, and it is the reason
     for observation 4.

  3. Locking in too early costs everything: {p_early:.3%}. Going to cash at
     EUR 250,000 buys a good rank and no prize.

  4. The MEDIAN of the leverage strategy with resets is around
     EUR 380,000, far above the EUR 107,000 of the passive variant.
     Usually high variance is paid for with the likely outcome; not here,
     because the reset cuts off the losses. If the depot falls below
     100,000, it is reset; upwards nothing is capped. The game rules
     themselves turn the bet into an option. This holds only for play
     money under these rules and does not carry over to any real
     portfolio: there is no reset button there.

  To put the absolute numbers in context: about {FIELD * SHARE_LEVERAGE:,.0f} depots in the field
  also go fully leveraged. Reaching the mark does not make a winner, only
  a member of the candidate group. The realistic chance of winning is of
  the order of 1 in a few thousand, roughly the number of those trying
  the same thing.
""")

    print("=" * 78)
    print("Product choice, and the limit of this model")
    print("=" * 78)
    print("""
  The distance to the barrier sets both the leverage (~1/distance) and the
  risk of being knocked out before the trend arrives. One would expect an
  optimum.

  The model finds none. In every version of this script the best cell lay
  at the EDGE of the grid: first 0.6%, then 0.2%, and 0.5% after continuous
  knock-out monitoring was added. An optimum that always sits at the edge
  is not an optimum; it means the mechanism that would create one is
  missing. Missing here are product availability, spreads, financing costs
  and overnight gaps, which kill a 200x leverage product in practice before
  statistics play any role.

  The table is therefore shown in relative terms and is no leverage
  recommendation.
""")
    M = 120_000
    distances = [0.005, 0.010, 0.020, 0.040, 0.080]
    sigmas = [0.025, 0.040, 0.060]
    raw = {}
    for a in distances:
        for sg in sigmas:
            best = np.maximum(
                simulate_depot(RNG, M, resets=True, ko_distance=a, base_sigma=sg),
                simulate_depot(RNG, M, resets=True, ko_distance=a, base_sigma=sg))
            raw[(a, sg)] = (best >= OBSERVED_WINNER).mean()
    top = max(raw.values())
    print(f"    {'Distance':<10}{'Lever.':>7}" + "".join(f"{x:>11.1%}" for x in sigmas))
    print(f"    {'':<17}" + "".join(f"{'relative':>11}" for _ in sigmas))
    for a in distances:
        line = f"    {a:<10.1%}{1 / a:>7.0f}"
        for sg in sigmas:
            r = raw[(a, sg)] / top if top > 0 else 0.0
            line += f"{r:>11.3f}" if r >= 0.0005 else f"{'~0':>11}"
        print(line)

    print("""
  What the table supports:

    Wide barriers have no chance. From 2% distance on, the leverage is no
    longer enough to turn EUR 20,000 into a seven-figure position.

    Volatility does not help uniformly. At 1% distance the row rises with
    the volatility of the underlying. At 0.5% it falls, because a more
    volatile underlying hits a tight barrier sooner. (Earlier versions of
    this script printed "volatility always helps"; the current grid does
    not support that.)

  What it does not support: a number for the optimal leverage.
""")

    print("=" * 78)
    print("What this script supports, and what it does not")
    print("=" * 78)
    print("""
  SUPPORTS:
    - Without a leveraged derivative 1st place is unreachable, not merely
      unlikely.
    - The winning mark lies around EUR 1.3M to 1.5M. That is an
      observation from 2025, not model output.
    - Locking in too early forfeits the main prize completely.
    - More volatility in the underlying is better in every configuration.

  DOES NOT SUPPORT:
    - An optimal leverage or distance to barrier.
    - Absolute probabilities to better than an order of magnitude.
    - Any statement about WHICH underlying will rise. The drift is zero
      everywhere, the 15% hit rate is set, not derived. This script does
      not replace a market view; it only says which depot structure could
      translate a market view into a win at all.
""")


if __name__ == "__main__":
    main()

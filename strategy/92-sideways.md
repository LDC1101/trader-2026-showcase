# Sideways regime: measurement and Plan B, 7 Sep 2026

Prompt (the player): "What if easing and crisis alternate week by week and oil goes
sideways? We cannot settle for that; if necessary, higher frequency or a different asset.
Why do I see this risk and you don't?"

The objection is valid. The number was in the thesis (knock-out on day 1 at the median, one
side surviving 40 days in 15% of cases), but it had been accepted as a cost, not treated as
a regime with its own plan. Below is the measurement on 15-minute bars over the last 60
days (`src/intraday.py`, data `data/intraday_15m.json`, Yahoo via the browser, 28 Jun to
4 Sep 2026).

## 1. What the regime looks like

| Asset | Range/day (median) | Net/day | Efficiency 10d | Largest run 5d | 20d | 60d |
|---|---|---|---|---|---|---|
| Brent | 3.75% | 1.77% | 0.23 | 18.5% | 27.3% | +30.7% |
| WTI | 4.00% | 1.51% | 0.28 | 17.1% | 24.2% | +29.9% |
| Gold | 2.11% | 1.13% | 0.32 | 8.2% | 17.1% | +11.1% |
| Silver | 3.67% | 1.84% | 0.21 | 12.8% | 19.7% | +13.6% |
| Natural gas | 3.25% | 1.29% | 0.37 | 10.9% | 18.0% | −6.2% |
| DAX | 0.85% | 0.34% | 0.23 | 4.8% | 6.5% | +4.5% |
| Nasdaq-100 | 1.34% | 0.54% | 0.21 | 8.3% | 10.1% | +0.3% |

Efficiency = net move over 10 days divided by the sum of the daily moves: 1 would be a pure
trend, 0 pure zigzag. Brent is at 0.23: three quarters of the movement cancels out. Even so,
Brent has the largest runs. Brent weekly closes: 72 → 76 → 88 → 97 → 90 → 84 → 89 → 94 → 88
→ 96. The "sideways" market is a weekly rhythm of ±5 to 12%.

No other asset is better: gold survives more often but runs only half as far. At 1–2%
distance the DAX and the indices do not move enough to win a prize.

## 2. Holding through zigzag (random entry, 5 trading days)

| Asset | Distance | P(knock-out within 5d) | Best multiple, median | 90% quantile |
|---|---|---|---|---|
| Brent | 1% | 80% | 1.6× | 8.4× |
| Brent | 2% | 67% | 1.8× | 5.4× |
| Brent | 3% | 57% | 1.8× | 4.2× |
| Gold | 1% | 69% | 1.7× | 4.2× |
| Gold | 2% | 41% | 1.7× | 2.9× |
| DAX | 2% | 33% | 1.5× | 2.8× |

## 3. Higher frequency: measured, not viable

Mechanical intraday rules on Brent, €20,000 per buy, 3% turbo spread, €7.80 per round trip,
buys 8:00–22:00, exit at the target, at knock-out, after 6 h or at 21:45, at most 20 buys a
day:

- **First result +€1.07M in 60 days.** That was a model error: entry and exit at the close
  of the 15-minute bar that hit the target, which captures the bar's entire overshoot,
  something nobody gets in reality.
- **With entry on the next bar and exit at the target price (limit):** −€72,000, 3 of 10
  weeks positive, 47% knock-outs. With a 5% spread −€142,000, with double the premium
  −€283,000. First half −€92,000, second half +€40,000. Calls only +€116,000 (Brent rose
  30% over the period), puts only −€330,000. Other assets: WTI +€34,000, silver +€159,000,
  gold −€136,000, natural gas −€97,000, DAX −€106,000.
- **Breakout rules:** −€77,000 to +€140,000, no pattern.

Finding: after costs and knock-outs no rule without knowledge of direction has a measurable
edge. What looks like a return is either the trend of the period (calls only) or a
measurement error. Two further reasons lie outside the numbers: trading by hand every 15
minutes for 14 hours a day is not feasible, and a 15-minute signal generator that a human
merely follows is what Rule 10 means by "automated trading system", with exclusion on
reasonable suspicion.

## 4. What works in a weekly rhythm: the weekly pair

Every Monday at 9:00 a call **and** a put on Brent, held until Friday or knock-out; the
better leg counts (in the game: two depots, opposite sides):

| Distance | Weeks | Both legs dead | Better leg on Friday, median | Maximum | ≥3× | Depot week, median | Best depot week |
|---|---|---|---|---|---|---|---|
| 1% | 10 | 8 | 0× | 6.6× | 2 | −20% | +112% |
| **2%** | 10 | 5 | **1.6×** | 6.3× | **5** | **+12%** | **+106%** |
| 3% | 10 | 4 | 1.9× | 4.6× | 2 | +18% | +72% |

Week by week at 2%: week 28 call 3.4×, week 29 call 6.3×, week 33 call 3.7×, week 34 call
4.0×, week 35 put 3.2×; in five weeks both legs died. Gold at 2%: both dead in 2 of 10
weeks, but a maximum of 4.0× and a median of +9%.

This is the mechanism for the weekly prize (percentage weekly gain) and for the rank: at 2%
distance the better leg tripled in every second week. At 1% the pair dies in eight weeks
out of ten; 1% is the distance for the main prize and for nothing else.

## 5. Plan B: the rule

Two legs, two jobs, already set up this way as of today:

| | Depot A | Depot B |
|---|---|---|
| Job | main prize | weekly prize and rank |
| Distance | 1–1.5% | **2%** (1.8–2.2) |
| Holding period | until knock-out or 2026-10-30 | until knock-out or Friday 21:45, then cash, new position on Monday |
| Sell order | 67.5× | none; closed by hand on Friday because a new position is set up on Monday |

**Triggers for switching Depot A to weekly mode** (2%, close on Friday):
- three knock-outs in a row in Depot A, or
- Brent efficiency over 10 trading days below 0.25 together with a net move below 5% (the
  same quantity as "Efficiency 10d" in section 1; `src/regime.py` measures it daily from
  the Watch, with a warning level after a single sideways week, and sends Telegram on
  Fridays and whenever the level changes), or
- from 12 Oct, a depot below €300,000 (existing rule).

Back to 1% only on a real-world event confirmed by the Council (Kharg, end of the blockade,
supply outage).

**Gains too small:** alongside this, `regime.py` tracks the weekly result of the better
depot against the weekly-mode benchmark (+12% median, section 4) and against the €300,000
mark for 12 Oct. On Fridays the balance arrives via Telegram: depot value, the week, how far
the winning mark still is, and what to do. `python3 src/regime.py --test` shows the state at
any time without sending.

**A different asset:** only if volatility in oil collapses (strait permanently open); then
gold, the rotation target from the Monday order card (`31-week-one-plan.md`): at 2% distance both legs dead in 2 of
10 weeks, maximum 4×.

**What Plan B is not:** no intraday trading, no signals at 15-minute intervals, no
directional forecast. The weekly pair is two-sided; the market decides which leg runs.

Limits of the measurement: 60 days, one regime, overlapping weeks; turbo model with a
constant premium and a 3% spread; knock-out checked on every bar, including at night
(conservative).

## 6. The leader on 8 Sep: gold turbos at 0.25% distance, measured

The rank-1 player stood at €167,108 (+67%) on 8 Sep at 11:27 after 7 trades in 1.5 days:
gold BEST calls 0.2–0.3% from the barrier (leverage 200–450), bought in the morning, sold
at market after one to two hours. 7 Sep: €0.83 → €3.83 (4.6×, gold +0.8% in the morning),
€0.85 → €1.76 (2.1×), €1.71 → €2.42 (1.4×). 8 Sep: bought at €1.61, €1.54 an hour later.
All long, all gold.

The same rule on the 15-minute bars from 29 Jun to 4 Sep (buy every 30 minutes between 8:00
and 10:30, hold 2 hours, exit at 3×, at knock-out or on time; €20,000 per buy, 3% spread):

| Distance | Direction | Knock-out | 3× reached | Return per trade (median) | € per trade | Weeks positive |
|---|---|---|---|---|---|---|
| 0.25% | call | 40% | 1% | −18% | −3,449 | 3/10 |
| 0.25% | put | 40% | 3% | −10% | −2,984 | 3/10 |
| 0.50% | call | 11% | 1% | −6% | −911 | 4/10 |
| 1.00% | call | 2% | 0% | −5% | −748 | 4/10 |

Between 8:00 and 11:00 gold gains 0.8% from the open on 7 of 49 mornings (14%); on 21
mornings (43%) it falls 0.25% and knocks out. 7 Sep was one of the seven. Without knowledge
of direction the method loses after spread and fees in every variant; with knowledge of
direction it would not need a 0.25% barrier. With about 30,000 participants, someone using
this method who caught two good mornings is bound to be at the top after two days. The
ranking that counts is the one on 30 Oct.

Consequence for us: no change. Depot A holds the Brent call (2× on 8 Sep, 3% distance);
Depot B follows Plan B (2%, weekly leg). The rank after two days is not a signal.

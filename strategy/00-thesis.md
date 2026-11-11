# The thesis, the numbers, the abort conditions

*Written 5–6 Sep, before the game, and amended 7 and 8 Sep. Depot B was moved to cash on 15 Sep, and from 17 Sep the player wrote off the main prize and ran Depot A as day bets that took every gain; see season/README.md.*

## The target

The overall winner is whoever holds the highest absolute depot value on 30 Oct. With about
30,000 participants and two depots each, that is the maximum of roughly 60,000 depots.

Trader 2025 sets the scale: the winner finished at €1.35M, second place at about €1.24M. That is
13.5 times the starting capital in eight weeks, and it is the yardstick for every decision. A
strategy that plausibly returns +40% is irrelevant for the main prize, however good it would be
as an investment.

The whole logic follows from this. The goal is not the best expected return but the highest
probability of producing an extreme outcome. These are different optimisation problems with
different solutions.

## The bet

€20,000, the absolute cap the rules allow for leveraged derivatives, goes into **one** product on
an underlying with a running or dated catalyst. Hold it. After a knock-out, re-enter immediately;
reset the depot when its value is below €100,000. Go to cash only above the winning mark.

Both depots take **opposite directions** on the same theme, because only the better one counts
for the main prize.

## Why there is no alternative

`python3 src/tournament.py`, calibrated on Trader 2025 (winner €1.35M, second €1.24M), simulates
250,000 game rounds per strategy:

| Strategy | P(≥1.35M) | Median | P(>500k) |
|---|---:|---:|---:|
| passive, broadly diversified | **0.000%** | 106,668 | 0.0% |
| 4 high-volatility stocks, no leverage | **0.000%** | 110,817 | 0.0% |
| leverage, no reset, no securing | 1.919% | 206,517 | 22.4% |
| leverage + resets | **2.774%** | 382,598 | 37.1% |
| leverage + resets + securing from 250k | 0.000% | 299,375 | 1.3% |
| leverage + resets + securing from 1.4M | 2.736% | 381,390 | 37.0% |

The first two rows reach the mark **not once** in 250,000 simulated rounds. This is arithmetic,
not probability: the 20% rule caps every stock position at a fifth of the depot, and five stocks
do not become a 13-fold gain in eight weeks.

The median of the leveraged strategy with resets is €382,598, far above the passive variant.
Normally high variance is paid for with a worse likely outcome. Here it is not, because the reset
cuts off losses while the upside stays open: the game rules turn the bet into an option. This
does not hold for a real account, which has no reset.

## Measured behaviour rules

**Taking profits costs a factor of 93.**

| Behaviour | P(≥1.35M) | Median | P(>500k) |
|---|---:|---:|---:|
| hold winners, after a knock-out re-enter only on Monday | **2.703%** | 381,756 | 36.9% |
| hold winners, after a knock-out re-enter immediately | 2.380% | **403,340** | **38.4%** |
| take profit at 10× | 0.089% | 354,490 | 26.5% |
| take profit at 3× | **0.029%** | 331,447 | 20.0% |

The cause: after a sale, only €20,000 is allowed again. Gains then add up instead of compounding.
Reaching €1.35M by rolling would take **16 successful five-fold gains in 40 trading days**.

The only frequency rule that matters follows from this: **high frequency on the loss side, zero
frequency on the profit side.**

**Opposite depots:** P(>500k) rises from 40% to 56%, the median from 80,000 to 571,000. With both
depots in the same direction they die together or win together, and the second hit is worthless
because only the maximum counts.

**Base in cash:** the volatility of the remaining €80,000 does not matter (2.728% with cash against
2.852% with high-volatility stocks, standard error about 0.03%). Cash keeps the leverage ratio
stable and saves order fees.

## Depot roles in the first plan (5 Sep)

The pre-game plan gave the depots different jobs. Two depots are two tickets only if they hold
**different underlyings or directions**; the same turbo on the same underlying twice is one ticket
with double the stake.

- **Depot A: main prize.** Target €1.3M. €20,000 in one leveraged derivative, the rest in stocks
  or cash. Reset and re-enter after a knock-out when the depot is below €100,000. A running
  position is held, not added to; the €20,000 cap prevents adding anyway, and taking profits
  destroys the convexity everything depends on.
- **Depot B: weekly ranking.** Eight weekly prizes of €2,222 each go to the highest percentage gain
  of the week, and a reset depot starts that calculation at €100,000. Because leverage is capped
  at `min(20%, €20,000)`, a depot of exactly €100,000 is optimal for percentage returns (see
  10-rules.md). So: reset on Monday if the depot is above or clearly below the start value, play
  maximally aggressive for one week, evaluate on Friday. Eight independent attempts at a weekly
  prize are far more likely to pay than one shot at the main prize.

Once Depot A is clearly above €500,000 it changes role: it becomes the main-prize candidate and
must not be reset. Depot B then carries the weekly game alone.

The thesis above replaced this split with opposite legs on one theme in both depots; the 8 Sep
amendment at the end of this file replaced that again.

## The securing rule

The 2025 main prize was decided by the exit, not the entry. The winner sold their gold call before
the final week; the others at the top held and lost in the correction.

- **Below €500,000:** do not secure. Nothing is won at that level, and securing removes the only
  chance. In the simulation P(main prize) falls from 2.77% to 0.00% when securing at 250,000.
- **Above the winning mark and in the lead:** secure. All cash, do not touch the depot for the rest
  of the game. Cash counts in full.
- **Above €500,000 but not in the lead:** keep playing. Second place pays nothing.

The decision depends on rank, not on the absolute value. The leaderboard updates overnight and is
therefore a day old, which matters when securing in the final week. Decide by **Thursday 29 Oct**
at the latest: the last game day is Friday 30 Oct, and reacting only then leaves no trading day in
reserve.

| Situation on 29 Oct | Action |
|---|---|
| below €500,000 | do not secure, keep playing; there is nothing to lose at this level |
| above €1M and in the lead | all cash, do not touch again |
| above €500,000, not in the lead | keep playing; second place pays nothing |

The last row of the tournament table shows that securing above the mark costs almost nothing
(2.736% against 2.774%). From 6 Sep the rule was placed as an order at entry: a 7-day limit sell
at 67.5 times the ask (see 31-week-one-plan.md).

## Abort conditions

Fixed in advance so that nothing is decided anew in the moment of the move.

| Condition | Consequence |
|---|---|
| A Hormuz agreement is reported | close the long depot immediately, let the short run |
| Depot < €100,000 and no position alive | reset, new position immediately |
| Three knock-outs in a row with the same instrument type | switch from turbo to warrant |
| Below €300,000 after week 5 (from 12 Oct) | write off the main prize, both depots on the weekly ranking |
| Depot above the winning mark AND in the lead | all cash, do not touch again |
| Oil volatility collapses (strait permanently open) | change theme, see `40-themes.md` |
| VIX above 25 | convexity is expensive: avoid warrants, prefer turbos |
| Sideways regime: three knock-outs in a row in Depot A, or Brent efficiency over 10 trading days < 0.25 with a net move < 5%. Measured daily after 21:30 by `src/regime.py`, called from the Watch, log `data/regime_log.md` | Depot A to weekly mode: 2% distance, close on Friday, re-enter on Monday. Measured in `92-sideways.md`: the better leg reaches ≥3× in 5 of 10 weeks |

### Which source may trigger an abort condition

The first row of the table is literally a headline, and therefore the one place where a false
report costs money. Closing Depot A on a rumour gives up the position for nothing.

So the two steps are separated:

- **Noticing** may come from any source, including X and Reddit. Maritime news flow (UKMTO
  advisories, tanker trackers, Lloyd's List, gCaptain) regularly runs hours ahead of the RSS feeds
  in `src/situation.py`. For an underlying that gaps 17–25% at the open while the barrier sits
  1–2% away, that lead decides between closing and being knocked out.
- **Triggering** requires a primary source: a UKMTO advisory, a wire report (Reuters, Bloomberg,
  AP), a government statement, or a status change on straits.live. A post on X is a reason to
  look, never the basis for an order.

This applies in both directions: a reported escalation also closes the short depot only against
a confirmed source.

**Precedent of 17 Jun 2026** (`70-hormuz-dossier.md`): the MoU, with the strait opening the next
day, moved Brent −0.2% on the day and −6% over five days. The −45% before it happened during the
hope phase from 6 May. "Reported" therefore means signed *and* implemented, and the early
indicator is the Polymarket probability, not the headline.

## Routine (playbook, 5 Sep)

The player places every order by hand.

**Once, before the first order**

1. Complete the profile: full name and address. Without it the prize claim is forfeited
   irrevocably, and the choice cannot be undone later.
2. Check whether the leaders' depots are visible.
3. Run `python3 src/tournament.py` once and read the table. It is the reasoning for everything
   that follows.

**Before every order**

```bash
python3 src/sizing.py <depot value> --ask <ask> [--leveraged] \
        [--already <total leveraged>] [--already-position <this security>]
```

**Mondays**

- Check the previous week's ranking.
- Depot B: reset if it is above €100,000 (otherwise the €20,000 cap depresses the achievable
  percentage return) or clearly below.
- Depot A: reset only if it is below €100,000 and no position is running.

**Daily**

- A leveraged position in profit: do nothing. No adding, no partial profits.
- A position knocked out: the playbook said to wait for the next entry point rather than re-enter
  the same day out of frustration. The tournament run above then measured that immediate re-entry
  raises the median and P(>500k), and the thesis adopted it.
- Note the rank in the log of `depot/positions.md`.

## What can go wrong

- **Overnight gaps.** Trading ends at 22:00 and US earnings mostly arrive later. A turbo can run
  through its barrier overnight with no chance to react. Before events reported after the close,
  a warrant without a knock-out is the more honest instrument.
- **Securing too early.** Costs the main prize completely (see above).
- **Securing too late.** Documented several times in 2025.
- **Both depots on the same bet.** Halves the number of tickets for nothing.
- **Adding to a running winner.** The €20,000 cap prevents it, but the reflex to take profits and
  re-enter destroys the convexity and turns a possible 50-fold gain into a 3-fold one.
- **Incomplete profile.** Without full name and address before the first order, the prize claim is
  forfeited irrevocably.

## What this thesis does not claim

It does not say where the oil price is going. It says that the price will move a lot, that the
triggers are known, and that both sides are covered because only the better depot counts.

The realistic chance of winning is **about 1 in a few thousand**, roughly the number of depots
trying the same thing. Everything in this file moves the chance from practically zero to that
order of magnitude, and against 60,000 depots no more is available. That is the maximum, not the
goal.

The weekly ranking is where systematic play pays off: eight independent attempts, scored in
percent, with a reset that restores the optimal starting base every week.

## Amendment 8 Sep 2026: Depot B bets directionally (the player's decision)

Plan B (`92-sideways.md`, section 5) had Depot B as the counter-leg to Depot A. When Depot B was
proposed as Brent call plus Brent put plus gold call, the player rejected it on 8 Sep: "That works
against itself. We have to make a bet, max risk = max return or loss. I want us to bet; that is why
you analyse the media so closely. I don't want to take a safe route."

Depot B now puts every leg in one direction, set by the Council and the news situation, with the
full leverage budget (20% of the depot or €20,000 for all leveraged products together). Close on
Friday, reset on Monday if below €100,000. No pair inside one depot, no hedge leg. Depot A (the
main-prize leg, Brent call) is not affected.

Measured 29 Jun–4 Sep (buy Monday, sell Friday, 2% distance): oil call + gold call +€146,000, oil
put + gold call −€131,000, in a regime in which Brent rose 30%. The direction is the bet; if it is
wrong, it costs one week.

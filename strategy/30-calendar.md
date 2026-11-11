# Calendar 7 Sep–30 Oct 2026

*Written 5 Sep. The week-by-week plan at the end assumes two active depots; Depot B was moved to cash on 15 Sep. See season/README.md.*

54 calendar days, about 40 trading days, 8 game weeks. Trading daily 8:00–22:00 (Stuttgart/EUWAX).

Scheduled events are the only way to get volatility without having to claim a direction: a fixed
date guarantees a move and says nothing about where it goes.

## Game weeks

| Week | Period | Scoring |
|---|---|---|
| 1 | Mon 2026-09-07 to Sun 2026-09-13 | night Sun→Mon |
| 2 | Mon 2026-09-14 to Sun 2026-09-20 | |
| 3 | Mon 2026-09-21 to Sun 2026-09-27 | |
| 4 | Mon 2026-09-28 to Sun 2026-10-04 | |
| 5 | Mon 2026-10-05 to Sun 2026-10-11 | |
| 6 | Mon 2026-10-12 to Sun 2026-10-18 | |
| 7 | Mon 2026-10-19 to Sun 2026-10-25 | |
| 8 | Mon 2026-10-26 to **Fri 2026-10-30, end of game** | depot value on 30 Oct decides |

The eighth calendar week would run to 1 Nov, but the game ends on Friday 30 Oct. The value on that
day counts for the main prize.

## Fixed dates

| Date | Week | Event | Significance |
|---|---|---|---|
| **Mon 2026-09-07** | 1 | **US markets closed (Labor Day)** | game starts; oil and Europe trade, US stocks do not move; wider spreads on US products |
| **Thu 2026-09-10** | 1 | Oracle and Adobe earnings | after the US close, from 22:00; reaction as a price gap on Friday morning |
| **Fri 2026-09-11** | 1 | **US consumer prices (CPI)** | **14:30, during trading.** According to Morgan Stanley the decisive factor for the Fed meeting |
| **Wed 2026-09-16** | 2 | **FOMC decision + projections (dot plot)** | 20:00 CEST, during trading. A meeting with projections moves more than one without. Rate hike ~63% priced in |
| Fri 2026-09-18 | 2 | major expiry day | futures and options expire; higher volume, often jerky moves |
| Tue 2026-10-13 | 6 | Q3 earnings season starts (US banks) | start of the phase with the highest single-stock volatility |
| Fri 2026-10-16 | 6 | October expiry | |
| Sun 2026-10-25 | 7 | clock change CEST → CET | US trading hours shift relative to Stuttgart |
| **Wed 2026-10-28** | 8 | **FOMC decision** | 19:00 CET, **two days before the end of the game** |
| **Thu 2026-10-29** | 8 | last full trading day before the end | **latest date for the securing decision** |
| **Fri 2026-10-30** | 8 | **last game day** | the depot value decides the main prize |
| Tue 2026-11-03 | after | US midterm elections | after the end of the game; positioning for them happens inside the game window |

The large US technology companies usually report in the last week of October, which is game week 8.
Their exact dates shift every year; check them before week 7.

## Running catalysts without a fixed date

**Strait of Hormuz:** closed since day 188. Any report on the US/Iran/Oman negotiations can move the
oil price by double digits, on any day. It is the main catalyst of the game window and the only one
that cannot be scheduled. Status: `python3 src/situation.py`.

## What follows

**Weeks 1, 2 and 6–8 carry the dates.** Weeks 3–5 are light on events; that is the time for trend
positions, the weekly ranking and the oil position, not for event bets.

**The final week is the most interesting and the most dangerous.** The FOMC on 28 Oct and the
mega-cap earnings fall into the last five trading days. Whoever leads then has more to lose than to
gain; whoever trails finds the last opportunity there.

**US earnings arrive after 22:00**, when Stuttgart is closed. The reaction is a price gap the next
morning that nothing can be positioned against. Before such dates a warrant without a knock-out
barrier is the more robust instrument than a turbo.

The market situation at the start (jobs report of 4 Sep, ~63% priced for a rate hike, VIX at 14.53)
is in `31-week-one-plan.md` and `40-themes.md`.

## To verify before the game starts

These points could not be confirmed reliably and need checking before the first order:

- ECB meeting dates inside the game window
- the exact earnings dates of the underlyings SG issues turbos on
- dates of regulatory approval decisions (biotech), if such underlyings come into question
- whether the game shows the leaders' depots publicly. If so, the gap to the lead can be read off
  directly, and the securing decision in `00-thesis.md` becomes observable instead of estimated.

## Week by week (playbook, 5 Sep)

**Week 1 (7–13 Sep): set up.** Fill Depot A and Depot B with different underlyings, never the same
bet twice; that halves the number of tickets for nothing. Keep the first positions deliberately
small while the interface and the products' behaviour are unfamiliar.

**Week 2 (14–20 Sep): FOMC and expiry.** Two dates: the rate decision with projections on Wednesday
16 Sep at 20:00 and the major expiry on Friday 18 Sep, both inside trading hours. For positions held
through the rate decision the warrant is the more robust instrument, because it has no barrier the
spike can break.

**Weeks 3–5 (21 Sep–11 Oct): few events.** Little can be planned. Depot B works the weekly ranking:
reset on Monday, €20,000 into a leveraged product on the most volatile available underlying,
evaluate on Friday. Depot A looks for a running trend, the constellation that produced the
million-euro hit in 2025.

**Weeks 6–7 (12–25 Oct): earnings season.** US banks report from 13 Oct, then the season runs broad.
This is the highest single-stock volatility of the whole game window, with dates known in advance.
The numbers arrive after Stuttgart closes and the move happens as a gap the next day, so: warrants,
not tight-barrier turbos.

At the end of week 7, assess the standing honestly. Below €500,000 the main prize is practically out
of reach; then only the weekly ranking counts, and there is no reason to become cautious.

**Week 8 (26–30 Oct): endgame.**

| Day | Task |
|---|---|
| Mon 2026-10-26 | check the leaderboard, determine the gap to the lead |
| Tue 2026-10-27 | last entries, if ground still has to be made up |
| Wed 2026-10-28 | FOMC 19:00 CET, the last major event |
| **Thu 2026-10-29** | **securing decision** (see `00-thesis.md`) |
| Fri 2026-10-30 | last game day; whoever has secured only watches |

The leaderboard updates overnight, so Thursday's decision rests on Wednesday evening's standings.

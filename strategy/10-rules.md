# The game rules as an optimisation problem

This file reads the rules for the structure they give the game, not for what they allow. Section
numbers refer to SG's rules; the paraphrase is in `11-rules-reference.md`.

## 1. The caps and what they force

| Rule | Cap | Consequence |
|---|---|---|
| per security, **in total** | 20% of depot value, cumulative over all purchases | at least five positions |
| all leveraged products together | 20% of depot value | leverage ratio capped |
| **absolute** | **€20,000, regardless of depot value** | **the binding cap** |
| units | 20,000 per leveraged derivative | binds below a price of about €1 |

All apply **at the time of purchase** and on the **ask**. A position that later grows above 20% is
compliant. That is the only mechanism by which €20,000 can become a million, and with it the core
of any winning strategy: buy once, let it run, do not add.

## 2. The €20,000 cap does not scale

The effective limit is `min(20% of the depot, €20,000)`. From a depot value of €100,000 the absolute
cap binds, and its relative weight shrinks with every euro of growth.

| Depot value | max. leveraged | as % of depot | weekly return at 5× |
|---:|---:|---:|---:|
| 100,000 | 20,000 | 20.0% | 80% |
| 250,000 | 20,000 | 8.0% | 32% |
| 500,000 | 20,000 | 4.0% | 16% |
| 1,000,000 | 20,000 | 2.0% | 8% |

**For the main prize:** the big jump has to come from *one held* position. Adding €20,000 bets one
after another grows additively and never reaches the winning mark.

**For the weekly ranking:** a depot of exactly €100,000 is optimal, because 20% and €20,000 coincide
there. Above it the achievable percentage return falls. A reset restores it.

## 3. The reset is a free option

Section 3 words it as a consolation: if the game does not develop as the player had hoped, each
depot can be reset once per week. Two depots over eight weeks give up to 16 restarts.

`src/tournament.py` measures what this does to the payoff distribution: P(≥€1.35M) rises from 1.92%
to 2.77% (factor 1.45), and the median from 107,000 to 383,000. Normally high variance is paid for
with the likely outcome. Here it is not, because the reset cuts off losses while nothing caps the
upside: the rules turn the bet into an option.

The 2025 winner reset three times.

A reset is irrevocable and deletes all of the depot's game data. It makes sense while the depot is
below €100,000 and is wrong from the moment it is above.

## 4. Cash counts in full, so securing is free

Section 9 scores "the current values of the individual positions plus the cash balance". No
interest, no haircut. Selling into cash freezes the value until the last game day, at a cost of
€3.90.

The 2025 main prize was decided here: the winner sold their gold call before the final week, the
others at the top held and gave back gains in the correction.

The timing has a hard edge: in the simulation, securing at €250,000 lowers P(main prize)
from 2.77% to **0.00%**. Securing is right, but only above the winning mark.

## 5. Order types: the exit belongs to the entry

Section 5 allows limit, stop-loss, stop-loss-limit, stop-buy and stop-buy-limit orders, valid for
1 day or **7 calendar days**. Sell orders can be placed right after the purchase and become active
after the 5-minute holding period.

This fixes the exit without anyone watching. It is a feature of the platform, not an automated
system. Renew weekly. It does not help against a price gap through the knock-out barrier.

## 6. What else binds

- **5-minute holding period** after every purchase. Sell orders can be placed at once but activate
  only afterwards. No scalping.
- **20 buy orders per depot per day**, sales unlimited.
- **Trading 8:00–22:00**, Stuttgart/EUWAX. The US open at 15:30 falls inside; reports after the US
  close (22:00 and later) do not. They show up as a price gap the next day, cannot be traded, and
  knock out turbos before anyone can react.
- **Only SG derivatives** listed on EUWAX. Reverse convertibles and anything that accrues interest
  are excluded.
- **Costs:** €10.00 per stock order, €3.90 per derivative order. At €20,000 per trade that is 0.02%,
  not a relevant quantity in this game.
- **Complete the profile before the first order.** Without full name and address the prize claim is
  forfeited irrevocably.

## 7. Rule 10: the boundary

Prohibited are manipulative behaviour, multiple user names and "unauthorised aids (e.g. automated
trading systems)". Also named explicitly: shrinking the depot volume to lift a single position's
share above the 20% limit.

Research, price analysis, screeners, calculators and the platform's own order types are not
affected; every participant uses them. The difference lies in **who triggers the order**. Nothing
in this repo may ever be connected to the depot.

What that means in practice:

- No second user name. It leads to immediate exclusion, and both depots drop out of the ranking.
- No script connected to the depot. Rule 10, exclusion without a hearing; suspicion is enough.
- No series of trades that shrinks the depot volume to lift a position above 20%.
- No position that was not computed with `src/sizing.py` first. Non-compliant orders are reduced,
  and only at execution.

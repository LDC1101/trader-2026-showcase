# Off-the-shelf AI models and social signals: assessment

Written before the game. The task was to search GitHub and HuggingFace for ready-made
prediction models and to mine Reddit, X and forums for hints. Both are done
(`src/scan_repos.py`, `src/scan_social.py`). This document records what came out and why
almost none of it goes into the strategy.

## What the search found

50 distinct repos across five search queries. The largest:

| Repo | Stars | Type |
|---|---:|---|
| tensortrade-org/tensortrade | 7,101 | framework for reinforcement-learning trading |
| grananqvist/Awesome-Quant-Machine-Learning | 4,014 | link collection |
| edtechre/pybroker | 3,532 | backtesting library |
| cbailes/awesome-deep-trading | 2,036 | link collection |
| PacktPublishing/Hands-On-ML-for-Trading | 1,922 | book companion code |
| Yvictor/TradingGym | 1,915 | simulation environment |

**Among the largest hits there is not a single working prediction model.** They are
frameworks, link collections, simulation environments and book companion code: tools for
building and testing, not models with demonstrated predictive power.

On HuggingFace the yield was thinner still. The most downloaded hits are language models
fine-tuned on trading jargon, with 300 to 500 downloads. For comparison, models taken
seriously on that platform have six- to eight-digit download counts. Nobody uses what is
there.

## Why this contributes nothing within the game period

To show a 53% hit rate against a coin flip with statistical confidence (5% significance,
80% power) takes **2,178 trades**:

| Claimed hit rate | Trades needed to show it |
|---|---:|
| 51% | 19,600 |
| 52% | 4,900 |
| 53% | 2,178 |
| 55% | 784 |
| 60% | 196 |

The game lasts eight weeks and leaves room for one to three dozen held positions. On a
sample that small, a real edge of three percentage points cannot be told apart from luck,
even if it exists. A model would have to be right about 60% of the time for its edge to
show at all within eight weeks. Such models are not public.

## The three errors these repos fail on

They are the same three errors that the sister repo `ML-training-area` measures in lessons
5, 7 and 9:

**Leakage.** The model sees information from the future during training. In lesson 9 the
training loss without a causal mask falls from 1.55 to 0.03, and the model then produces
nothing but line breaks: 100% of 301 generated characters. By its loss it is the best model
in the file. A backtest with leakage always looks good, and the cruder the error, the better
the curve looks.

**Overfitting to the validation set.** In lesson 5, early stopping on the best validation
score picked a model that was **worse** on the ten times larger test set than the
supposedly overfitted one. The cause was the noise level of the validation set. Optimising a
trading strategy over a thousand parameter combinations selects the luckiest measurement,
not the best strategy.

**No baseline.** In lesson 7 an untrained baseline produced an apparent 4.9% advantage for
transfer learning. With a fair compute budget it almost completely disappeared. A trading
model that is not compared against buy-and-hold and against random entries says nothing.

A repo that does not even mention walk-forward tests, transaction costs and a baseline makes
no statement about making money, whatever its star count. `src/scan_repos.py --deep` checks
the READMEs for these terms. A mention is the lowest possible bar: it proves only that the
term appears, not that the work was done correctly.

## What is still usable

`pybroker` and comparable libraries are solid as a **toolbox**: fetching and preparing
price data, computing volatility, a backtest scaffold. They are of no use as an oracle and
of real use as infrastructure.

## Social signals: Reddit, X, forums

Access is largely closed. Anonymous queries return:

| Source | Status |
|---|---|
| reddit.com JSON | HTTP 403, OAuth only since 2023 |
| Pushshift | HTTP 403 |
| StockTwits API | HTTP 403 |
| X / Twitter | paid access required |
| GitHub API | open |
| HuggingFace API | open |

`src/scan_social.py` supports Reddit through a free OAuth read-only access; without
credentials it stops with setup instructions instead of silently returning empty lists.

**How to use the signal.** Not for direction. Social attention has a documented but weak and
quickly decaying predictive power for short-term returns, and the trade is crowded. What it
does reliably indicate is **elevated volatility**, the one property that helps in every
configuration according to `src/tournament.py`.

The scanner therefore produces a candidate list for movement, not a buy list. Mention counts
can be manipulated and are manipulated; in forums where positions are posted publicly, that
is part of the business model.

## On copying the best players

If the game discloses the leaders' depots, the obvious idea is to replicate their
positions. For the main prize that does not work: holding the same positions as the leader
ends with the same result as the leader, minus the lead the leader already has. Copying
cannot close the gap.

What insight into other depots does provide is different and more useful: it makes the
**distance to the lead** measurable. That distance is the quantity the securing decision
depends on ("The securing rule" in `00-thesis.md`), the only decision in the whole game where information about the other players actually changes the outcome.

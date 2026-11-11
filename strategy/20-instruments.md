# Instruments and product selection

*Written 5–6 Sep for positions held toward the winning mark. The day bets from 17 Sep used wider barriers: 2.5–5.3% on AMD, about 5% on Brent, 9.6–11.7% on the Tesla and Seagate earnings bets; see season/README.md.*

## The decision rule

| Situation | Instrument | Why |
|---|---|---|
| underlying with **high** implied volatility (oil at present) | **turbo** | pays linearly in the underlying and contains **no volatility premium** |
| underlying with **low** implied volatility (stocks, VIX 14.5) | **warrant** | convexity is cheap right now |
| event falls **after** 22:00 Stuttgart time | **warrant** | no barrier that a price gap can break |
| running trend, event during trading hours | **turbo** | more leverage per euro |
| sideways market | **none of these** | factor certificates lose through the daily reset |

Buying an oil **warrant** now means paying the war panic as volatility premium. Buying a stock
**turbo** means giving away the cheapest convexity in a year.

## Product families

From the pre-game strategy (5 Sep):

| Product | When | Why |
|---|---|---|
| **warrant (plain)** | before dated events | no knock-out barrier: price noise before the date cannot kill the position |
| **turbo / BEST turbo** | for running trends | linear leverage, cheaper than warrants, but can be knocked out at any time |
| **factor certificate** | only in a clear, calm trend | constant leverage without knock-out, but loses in sideways phases through the daily reset |
| **inline warrant** | when nothing happens | pays in sideways markets, unsuitable for this tournament |

For an event with a fixed date (earnings, a rate decision) the warrant is the right vehicle: it
survives the days until then. For a trend that is already running the turbo is better, because it
delivers the same leverage more cheaply, and because its barrier is fixed, it becomes more robust
with every percent of gain.

## BEST instead of X-BEST: a free advantage

On the DAX, SG offers two turbo families that differ in one point no marketing text mentions:

- **BEST / Classic**: knock-out only during Xetra hours, **9:00–17:30**
- **X-BEST / X-Classic**: knock-out over the full session, **8:00–22:00**

Same leverage, same price, 5.5 fewer hours of knock-out risk per day.
`python3 src/knockout_window.py` puts a number on it:

| Distance to barrier | Holding period | X-BEST survives | BEST survives |
|---|---|---:|---:|
| 1.0% | 10 days | 22.6% | 24.7% |
| 2.0% | 10 days | 43.4% | 45.4% |
| 3.5% | 10 days | 68.4% | 70.2% |

2 to 9 percent higher survival. That is smaller than the mechanism suggests, because over many
days almost every position eventually runs into an open window. It costs nothing, though. **Always
choose BEST or Classic.**

Limit: a price gap that opens *below* the barrier knocks out a BEST product too, so the advantage is
an upper bound.

## Distance to barrier

The model in `src/tournament.py` gives **no** number for this on its own: in every version the
optimum sat at the edge of the grid, which means the model lacks the mechanisms that would create
an interior optimum (product availability, spreads, financing costs, overnight gaps).

Only the direction holds up:

- **beyond about 4% distance** the leverage is no longer enough to turn €20,000 into a seven-figure
  position
- **very tight barriers** die of noise before the move arrives
- **more volatility in the underlying helps in every constellation** (the current grid in
  `src/tournament.py` does not support this: at 0.5% distance more volatility lowers the chance,
  because the tight barrier is hit sooner)

**Correction of 5 Sep 2026.** This section used to say "two to three daily volatilities of
distance, for oil 8–12%" (the pre-game strategy said one to two weekly volatilities). That was
wrong by a wide margin: computed against the winning mark, that distance has **zero** chance at the
main prize and at a good rank.

The reason is arithmetic. For €1.35M, €20,000 has to grow 64-fold. A turbo pays linearly:
multiplier = (move + distance) / distance. At 10% distance even Brent at $150 (+56%) would give only
6.6×.

| Distance | Leverage | P(winning mark) | P(good rank) | Knock-out |
|---|---|---|---|---|
| **1.0%** | 100 | **1.17%** | 4.3% | 94.9% |
| 2.0% | 50 | 0.01% | **5.0%** | 90.1% |
| 4.0% | 25 | 0.00% | 1.2% | 81.4% |
| 8–12% | 8–11 | 0.00% | 0.00% | 54–63% |

**The right choice is the tightest barrier, 1–2%, with a knock-out rate of about 90–95%.** The
knock-out is the normal case; resets and immediate re-entry are the answer to it, not a wider
distance.

**The quantity to look for is not volatility but the ratio of trend to noise.** The 2025 win came
from a tight turbo on **gold**, which moves about 1.1% a day and trended for weeks; there a 1%
barrier survives 20 trading days with a probability of 16%. At oil's 4% it is 4.4%. High volatility
helps the move and at the same time kills the tight barrier the multiplier needs.

The earlier simulation hid this because it varied the distance in absolute terms instead of
relative to daily volatility.

## Product selection in practice

**Correction of 5 Sep 2026:** this said "there is no SG API". Wrong. The website is a single-page
app, but its table comes from
`https://www.sg-zertifikate.de/EmcWebApi/api/ProductSearch/Search`, and that endpoint answers
`curl`. `src/sg_products.py` reads it: BEST (class 47) and Classic (43), underlying by `AssetId`
(Brent −4, gold 415, silver 423, DAX 389, NVIDIA 320), call/put, with WKN, barrier, leverage, bid
and ask. The API does not return the underlying's price; the script derives it from the product
prices.

Select by these criteria (by script or by hand in the product finder):

1. issuer Société Générale, listed on EUWAX
2. underlying as set in `40-themes.md`
3. type **BEST turbo** or **Classic**, never X-BEST/X-Classic
4. knock-out barrier **1–2% away**, leverage 50–100 (see "Distance to barrier"). **Not wider**, not
   even on calmer underlyings.
5. an ask that keeps €20,000 under 20,000 units, so **above €1.00**
6. tight spread and reasonable volume

Then compute the units:

```bash
python3 src/sizing.py <depot value> --ask <ask> --leveraged
```

## Right after the purchase

The exit is set at entry, not decided later:

- **limit sell** at the target price, valid 7 days
- **stop-loss** where it makes sense; it does not protect against a price gap through the barrier
- renew both weekly (7 calendar days validity)

Both are the game platform's own order types and explicitly allowed.

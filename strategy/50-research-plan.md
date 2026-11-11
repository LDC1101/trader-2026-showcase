# Research plan before the game: 5–6 Sep 2026

Goal: by Monday 7 Sep, 8:00, an order card with two concrete products per depot, on opposite
sides, and the reasoning for the chosen underlying. After that the system continues as a daily
routine. The results are in `60-research-2026-09-05.md`.

## 0. Ground rules

- Research, computation, product comparison: yes. The game platform: no, not even read-only. The
  player reads any data about the field of participants themselves.
- No forecast of direction. The result is a ranking by move size, trend-to-noise ratio and catalyst
  density in the window 7 Sep–30 Oct.
- The target quantity is not volatility. Gold in 2025: 1.1% daily range, trending for weeks, a 1%
  barrier survives 20 trading days with 16%. Oil at 4%: 4.4%. What is wanted is trend per unit of
  noise, with a catalyst.

## 1. Sources

| Source | Access | Expectation |
|---|---|---|
| prediction markets (Polymarket, Kalshi, Metaculus) | browser | high: market-implied probabilities for Hormuz, the Fed, an Iran agreement |
| CFTC Commitments of Traders | local, weekly | positioning of large traders in crude and gold |
| UKMTO `/recent-incidents` | browser | primary source for the abort condition |
| EIA, OPEC monthly report | local | inventories, production |
| gCaptain, Reuters, Bloomberg | RSS, WebSearch | news flow |
| openinsider (MCP) | direct | insider purchases in AI-energy names |
| Stooq, Yahoo | local | price history for section 3 |
| X | browser, login, secondary account | early warning, never a reason to decide |
| Reddit, wallstreet-online, ariva | browser | low; purpose: share of leverage players in the field |
| GitHub | WebSearch | repos on commodity volatility and turbo pricing |

Any source that does not deliver is logged as "does not deliver".

## 2. Candidates

Brent, WTI, gold, silver, natural gas, uranium, DAX, S&P 500, VIX-related products, AI energy (CEG,
OKLO, SMR, GEV), semiconductors. Plus anything with a political date inside the window: Hormuz, the
Fed on 16 Sep and 28 Oct, OPEC, the US midterms on 3 Nov, sanctions.

Per candidate: the catalyst (date or running), the move size from comparable cases, and SG product
availability.

## 3. Computation: `src/candidates.py`

Reuses `src/knockout_window.py` (Brownian bridge) and `src/tournament.py` (multiplier). Per
candidate:

| Quantity | How |
|---|---|
| σ_d | realised daily volatility, 20 and 60 days |
| trend/noise | 20-day return / (σ_d·√20), rolling |
| P(survival) | 20 trading days at 1.0 / 1.5 / 2.0% distance |
| multiplier | (move + distance) / distance |
| P(≥64×) | the number that matters for the main prize |

Cross-check: gold in 2025 must come out near the top, otherwise the model is wrong.

## 4. Products

Only for the two or three best underlyings: SG product finder in the browser, WKN, ask, barrier,
distance, leverage, spread, BEST instead of X-BEST, ask above €1.00. Units from `src/sizing.py`.

## 5. Result

The Monday order card: two products per depot, on opposite sides. If the computation points to an
underlying other than Brent, both variants go on the card with numbers, and the player decides.

## Schedule

Saturday evening: 1 and 2. Sunday early: 3. Sunday afternoon: 4 and 5. On Sunday at 18:12 the
weekly-review routine runs and reads the new state.

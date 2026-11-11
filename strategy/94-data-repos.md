# What can be borrowed from existing repos

Written before the game. The search looked for ready-made code on politician and insider
trading, SEC data and backtests. The results are usable, though not in the way their
headlines suggest. The deciding filter is the **reporting deadline**, not code quality.

## The reporting deadline

| Source | Deadline | Usable for us? |
|---|---|---|
| **SEC Form 4** (corporate insiders) | **2 business days** | **Yes**: fast enough to matter within the game period |
| Congressional PTR (STOCK Act) | **45 days** | No, not as a timing signal |
| 13F (fund holdings) | 45 days after quarter end | No |

Congressional trading is the most popular of these signals and the least useful for an
eight-week game. Evidence from the research: Pelosi's most recently published trade was
dated **28 July 2026**, and the tracker platforms had been updated on **1 September**. What
becomes visible today is five weeks old. In a game that lasts eight weeks, a signal with a
five-week delay is no signal.

Form 4 is the opposite case: corporate insiders have to report within two business days.
That is fast enough to mean something within the game period.

## The repos, sorted by usefulness for us

**1. `dgunning/edgartools`: the only one I would integrate**
Python library for SEC EDGAR: Forms 3/4/5, 13F, XBRL financial data, a clean typed API,
MIT licence. It covers exactly Form 4, the only filing that arrives fast enough. Actively
maintained.

**2. `johnisanerd/Apify-Congressional-Trading-Data-Scraper`**
Congressional transactions (House and Senate) as structured JSON, 54,000+ transactions since
2012. Cleanly built. Because of the 45-day deadline it cannot serve as a timing signal, but
it shows **which stocks are in political focus**, i.e. it works as a candidate list for
volatility, not as a buy signal.

**3. `kadoa-org/congress-trading-monitor`**
Merges the House Clerk, Senate eFD and the Office of Government Ethics into one dataset. The
cleanest aggregation of the three sources.

**4. `semerriam/congress-stock-trades`**
Free JSON endpoints (Senate/House Stock Watcher). The quickest to try for a one-off look.

**5. `anderseline/SenateTrades`**
Scans the SEC EDGAR insider list several times an hour and sends notifications. The pattern
is worth more than the code: short polling intervals on the fast source, not on the slow
one.

**6. `edtechre/pybroker`**
Backtesting library, 3,532 stars, active. Solid as a tool. Of no use for this game, because
we trade one to three dozen positions rather than testing a strategy over years.

**7. `vibeyclaw/awesome-sec-filings`**
Curated list on SEC data. A good starting point, no code.

## What I would actually build from this, and what not

**Build:** a small Form 4 fetch based on `edgartools` that reports, for a handful of
watched stocks, when executives or directors have bought in the last few days. Insider
purchases (not sales) ahead of a scheduled event are a weak but real signal, and the
two-business-day deadline makes them visible in time.

**Do not build:** a congressional tracker. Five weeks of delay, and the effect is long
priced in before the filing appears. The effort would go into a signal that structurally
arrives too late for our time horizon.

**Do not build:** a prediction model from the repos in `93-ai-trading-models.md`. The
reasoning is there: an edge of three percentage points needs 2,178 trades to be
demonstrated, and we have room for one to three dozen.

## Scope

All the sources named here are mandatory disclosures: SEC filings, STOCK Act disclosures,
13F reports. Analysing them is legal and common practice; that is what the disclosure
obligations exist for. Obtaining non-public information is something else and does not
happen here.

For the game itself this is irrelevant anyway, since it is played with play money. It
matters for the data sources, and they are all public.

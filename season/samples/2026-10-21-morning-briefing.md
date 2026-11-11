# Morning briefing, Wednesday 21 Oct 2026 (week 7, trading day 33)

> **Editor's note:** the cloud routine wrote the first part before the market opened. The addendum
> below comes from an interactive session with the player at 08:40. At 09:04 the player bought a
> Tesla BEST call, **FG8GV8**, 5,680 units at €3.45 (barrier $342.67, Tesla ~$379, distance 9.6 %),
> which is not one of the listed candidates; it was sold on 26 Oct at €4.64 for +€6,751.40 net (see
> `depot/positions.md`). The FG8V8A buy limit at €4.85 that the briefing treats as standing was a
> recommendation in the log of 16 Oct; the addendum notes that Depot A had no order.

**Run:** cloud routine (morning briefing), Wed 21 Oct, early. **Delivery:** repo commit. Telegram is
not reachable from the cloud (checked again today: no `.env`, `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`
not set; the egress proxy blocks `curl`/POST). `straits.live` via `WebFetch` again returned
`ENOTFOUND` (egress block); the situation was cross-checked through WebSearch (S2/S4). This briefing
is written to be complete when read in the repo.

**Data basis.** `depot/positions.md` is from Fri 16 Oct, 11:10, today **5 days old, past the three-day
limit**. According to the log, the days between Friday and Wednesday were trading days with no live
position (both portfolios pure cash) and no order due, so the state is unchanged in practice but **not
freshly confirmed; the player should confirm `positions.md` when convenient.** Last recorded state:
Depot A **€225,718.19** (+125.7 % since the start, pure cash), Depot B **€81,846.60** (pure cash).
**No price and no portfolio value invented.**

---

## Portfolio assessment first

**Nothing to hold, nothing to close, no forced purchase: both portfolios are pure cash (last recorded
state).** The expected pullback towards your buy level (~104) **failed to come for the second day in a
row**. The opposite happened: Brent rose intraday yesterday to a new five-month high of **$111.99**,
settled at **$108.79** and is back at **~$110** this morning. The drivers are still the attacks: IRGC
mine hits on two more tankers in Hormuz, Houthi strikes on Saudi oil infrastructure (Yanbu, Shaybah,
the Riyadh and Abha airports).

**For re-entry, patience remains right. Your alert at 104 is set correctly but stays far away.** Brent
at ~110 is at the top of the range; buying here would be buying into the high, against the repeated
lesson that the gains came from purchases at the **bottom** of the range (101.5 on 5 Oct, 104.3 on
12 Oct). Leave the buy limit **FG8V8A ~€4.85** (fills only at Brent ~104) and the buy alert (trigger
104.2, **valid only until Fri 23 Oct**, GitHub Actions) in place. **Note:** the buy alert expires on
Friday and at Brent 110 is far from its trigger; decide by then whether to extend or adjust it. **I do
not place any order; the decision stays yours.**

**If you still want to go long now:** a Brent call **warrant** without a barrier, not a turbo, because
of the deal-gap risk (Iran's conditional reopening offer stands) and the three-knock-out rule
(triggered since 17 Sep). A VIX of ~16–18 makes convexity cheap. Maximum **€19,996** (the absolute
€20,000 cap binds). **Chance of winning: yes** (the Brent call is the main-prize leg). **No direction
forecast:** the bet is on the size of the move, not its direction.

**Depot B stays pure cash** (your decision of 15 Sep). Reset only if you play B again.

---

## Prices (Wed 21 Oct early / settle Tue 20 Oct)

| Instrument | Level | Change | Source/tier |
|---|---:|---|---|
| **Brent (front)** | **~$110** (Wed 21 Oct early; 109.64 at 00:22 GMT, then ~110.10–110.40) | Tue 20 Oct settle **$108.79** (−$0.76, −0.69 %); intraday **$111.99** = five-month high. Wed early +1.4 %, back above 110 | hdfcsky/Reuters summary/Business Recorder 20–21 Oct, S2/S4 |
| **WTI (front)** | **~$99–99.2** (Wed early, Dec contract) | Nov contract expired Tue at **$101.79**; front rolled to Dec (lower) | hdfcsky/Reuters summary 20–21 Oct, S2/S4 |
| **S&P 500** | **7,712.57** (close Tue 20 Oct) | **+0.28 %**; Dow +1 % (~+500 pts) | Yahoo Finance/FRED 20 Oct, S2 |
| **VIX** | **~16.3–18.8** (Tue 20 Oct, sources disagree) | well below 20/25; an exact Cboe close could not be pinned down from the cloud | Yahoo/TradingEconomics 20 Oct, S2/S4 |
| **DAX** | **not freshly confirmed** for Tue 20 Oct | last confirmed close Fri 16 Oct **25,622.61** (+0.95 %) | TradingEconomics 16 Oct, S2 |

Brent/WTI are early and settle values cross-checked across several sources (Brent scatters between
108.79 settle, 109.64, 110.10 and 110.40 depending on the time). The WTI front value looks lower because
the Nov contract expired and Dec trades lower; this is not a direction signal. The VIX close is
inconsistent (16.27 / 17.31 / 18.76) and **is not set as a single value here**; the range stays below 25.
DAX for Tuesday not confirmed, the last reliable close is Friday. **No invented price.**

## Strait of Hormuz

**Closed. No deal. The attacks continue, and the pullback from the high does not come.**

- **No implemented agreement.** Iran's reopening offer remains conditional (the US would have to lift
  the blockade and the oil sanctions). Iran set "red lines" for talks with the US: lift sanctions, end
  threats, "not one gram" of uranium leaves the country. Tehran reports **no reply** from Saudi Arabia
  or the Houthis to its peace offer; Iran–Pakistan mediation talks are under way (the reason for
  Tuesday's small pullback from the 111.99 high). **No agreed opening date.** (Fox/Reuters
  summary/discoveryalert 20–21 Oct, S2/S4.)
- **Escalation.** The IRGC reports two more tankers on fire after mine hits (southern strait, confirmed
  by no maritime authority). **At least 18 ships attacked in two weeks** (Kpler). The Houthis claim
  strikes on Aramco Yanbu, the Shaybah oil field and the Riyadh and Abha airports (not confirmed by
  Saudi Arabia or Reuters). Analysts: the risk now extends beyond Hormuz (Red Sea, other loading
  points). (Korean business press/oilprice/Business Recorder 20–21 Oct, S2/S4.)
- **Early indicator cold (last reading).** Polymarket last priced a Hormuz normalisation by 31 Oct at
  ~3 %. Not retrievable live from the cloud; check before use. (S4 reading.)

**Net:** the physical bottleneck (escalating attacks, throughput below half) holds Brent at its
five-month high; Tuesday's small pullback was driven by diplomacy (Iran–Pakistan) and was recovered
overnight. **Abort condition 1 (Hormuz deal) NOT triggered:** a conditional Iranian offer is not an
opening confirmed by a primary source.

## News by topic

- **Oil.** Brent at its five-month high (Tue settle 108.79, intraday 111.99; Wed early ~110, +1.4 %),
  WTI Dec ~$99. Drivers: IRGC mine hits and Houthi strikes on Saudi oil infrastructure; short pullback
  on Tuesday from the Iran–Pakistan mediation, recovered overnight. **No direction forecast.**
  (hdfcsky/Korean business press/Business Recorder 20–21 Oct, S2/S4.)
- **Fed / rates.** No Fed date and no CPI this week. The hot September CPI (14 Oct) keeps a hike risk
  alive; the next decision is **Wed 28 Oct** (week 8, two days before the game ends). (S4.)
- **Equities.** S&P 500 Tuesday +0.28 % to 7,712.57, Dow +1 %, a recovery after the previous week's
  loss; VIX ~16–18. Q3 earnings season: **Tesla and Meta report today after the US close**, the
  week's biggest single-stock events; they move single stocks, not oil directly. (Yahoo/CNBC 20 Oct,
  S2.)
- **US shutdown.** Still in effect (since 1 Oct); government EIA inventory data postponed, supply
  signals from private figures to be read with caution. (S2/S4.)

## Events today (Wed 21 Oct) and this week

| Day | Event | Meaning |
|---|---|---|
| **Wed 2026-10-21** | **Tesla and Meta** (after the US close) | biggest single-stock events of the week; not an oil driver, no event that moves the open (non-)position |
| **Fri 2026-10-23** | buy alert `buy_alert.json` expires | decide by then whether to extend or adjust; untriggered at Brent 110 |
| **Sun 2026-10-25** | **clocks change, CEST to CET** | US session times shift in Berlin time |
| any time | Hormuz status, tanker attacks, US and Russia sanctions decisions | dominant oil driver, no fixed date |

No Fed date, no CPI this week. **Next fixed catalyst relevant to oil and the portfolios: FOMC
Wed 28 Oct** (week 8, two days before the game ends).

## Check against the abort conditions (`strategy/00-thesis.md`)

| Condition | State today (2026-10-21) |
|---|---|
| Hormuz agreement **reported and implemented** → close long | **NOT triggered.** Strait closed, no deal, Iran's offer conditional, attacks escalating. (No long position open.) |
| Portfolio < €100,000 and no position alive → reset | **Depot B: €81,847 cash, no position → reset technically due** (deliberately idle since 15 Sep). Depot A: €225,718 > €100,000. |
| Three knock-outs in a row, same instrument type → turbo to warrant | **triggered** (since 17 Sep). At the high with deal-gap risk, the warrant without a barrier remains the more robust instrument for re-entry. |
| **After week 5 (from 12 Oct) below €300,000** → write off the main prize | **formally triggered:** best portfolio €225,718 < €300,000. **The player's standing path B decision** (Depot A keeps going for the main prize) overrides the rule; not re-argued. |
| Above the winning mark AND in the lead → go to cash | n/a: best portfolio €225.7k, factor ~6 to €1.35M. |
| Oil volatility collapses (strait permanently open) → change theme | **not triggered.** Strait closed, Brent at a five-month high, attacks escalating: the opposite of a volatility collapse. |
| VIX above 25 → avoid warrants | **not triggered** (~16–18). Still favours a warrant for re-entry. |
| Sideways regime (Brent efficiency < 0.25 with net move < 5 % over 10 trading days) | **not triggered / superseded.** Brent at a five-month high, 10-day net move clearly > 5 %; the sideways tactic no longer applies. Only recomputable cleanly on the player's machine (`regime.py`). |

**Decisive:** abort condition 1 **not** triggered, the oil thesis holds. Both portfolios pure cash
(last recorded state), nothing to close. Unchanged from yesterday: the pullback towards 104 does not
come, Brent is at the high.

## TODAY

- **Nothing to close:** no open position in either portfolio (last recorded state).
- **No forced purchase. Do not buy into the high.** Brent ~$110 is at the top of the range, at the
  five-month high. The last two gains came from purchases at the **bottom** of the range (101.5 /
  104.3). **Leave** the buy limit **FG8V8A** 4,120 units at **€4.85** (7 days, fills at Brent ~104)
  and the buy alert (trigger 104.2, **valid until Fri 23 Oct**, GitHub Actions) **in place**: they
  wait for exactly the pullback that has been missing for two days.
- **The buy alert expires Fri 23 Oct.** Decide by then whether to extend or adjust it
  (`depot/buy_alert.json`, `valid_until`). At Brent 110 it is untriggered and far from its trigger.
- **If the player wants to go long now:** a Brent call **warrant** without a barrier, not a turbo
  (deal-gap risk plus the three-knock-out rule). First read `strategy/11-rules-reference.md`
  section 5, then `python3 src/sizing.py 225718 --ask <ask price> --leveraged`. Maximum ~€19,996 (the
  absolute €20,000 cap binds). **Chance of winning: yes. No direction forecast.**
- **On a deal or opening headline:** cancel the buy limit rather than let it fill. Only a primary
  source (UKMTO, Reuters/Bloomberg/AP, a government, a `straits.live` status change) triggers abort
  condition 1; a conditional Iranian offer does not.
- **Depot B:** pure cash (decision of 15 Sep). Reset only on reactivation (first reset to €100,000,
  then a directional oil-long weekly bet).
- **`positions.md` is 5 days old** (past the limit); confirm when convenient that both portfolios are
  still pure cash.
- Next fixed catalyst: FOMC **Wed 28 Oct**. No dated event until then.

---

### Short version (Telegram format; not sendable from the cloud, so committed to the repo)

> **Both portfolios pure cash: nothing to hold, no forced purchase today.** The pullback towards 104
> fails to come for the second day: Brent rose yesterday to a new five-month high ($111.99), settled at
> 108.79 and is back at ~110 this morning. The drivers are still the attacks (two more tanker mine hits
> in Hormuz, Houthi strikes on Saudi oil facilities). No Hormuz deal: strait closed, Iran's offer
> conditional. Do not buy into the high; your buy limit (FG8V8A ~€4.85) and buy alert (trigger Brent
> 104) keep waiting for the pullback. **The buy alert expires Fri 23 Oct; decide by then whether to
> extend it.** Depot A €225,718 (+125.7 %), Depot B unchanged at €81,847 cash. If you go long now: a
> Brent call warrant without a barrier, not a turbo, at most €20,000. `positions.md` is 5 days old;
> confirm when convenient. Next fixed event: FOMC Wed 28 Oct.

---

### Sources

- **Brent/WTI 21 Oct:** Tue 20 Oct settle Brent $108.79 (−$0.76, −0.69 %), intraday $111.99
  (five-month high); Wed early ~$109.64 (00:22 GMT), then ~$110.10–110.40 (+1.4 %). The WTI Nov
  contract expired Tuesday at $101.79, the front rolled to Dec (~$99). (hdfcsky "Crude Oil Rises 1.4%
  to $110", 21 Oct; Reuters summary/Business Recorder "oil rises on Middle East supply worries",
  21 Oct; Korean business press "Two More Tankers Hit by Mines… Brent Hits 5-Month High", 20 Oct,
  S2/S4.)
- **Equities/VIX:** S&P 500 Tue 20 Oct 7,712.57 (+0.28 %), Dow +1 % (~+500 pts). VIX inconsistent
  (16.27 / 17.31 / 18.76), range below 25, no single value set. DAX not confirmed for Tuesday, Fri
  16 Oct 25,622.61. (Yahoo Finance/FRED/TradingEconomics 20 Oct, S2/S4.)
- **Hormuz/diplomacy:** strait closed, no implemented agreement; Iran's reopening offer conditional,
  red lines set for US talks, no Saudi/Houthi reply to the peace offer, Iran–Pakistan mediation (the
  reason for Tuesday's small pullback). IRGC: two more tankers on fire after mine hits (unconfirmed),
  at least 18 ships attacked in two weeks (Kpler); the Houthis claim Aramco Yanbu, Shaybah, Riyadh and
  Abha (unconfirmed). (Fox "Iran war news… October 20"; discoveryalert "Oil Prices Whipsaw… Iran
  Talks", Oct 2026; Korean business press/oilprice 20–21 Oct, S2/S3/S4.) → **Abort condition 1 not
  triggered.**
- **Early indicator:** Polymarket Hormuz normalisation by 31 Oct last at ~3 %, not retrievable live
  from the cloud, check before use. (S4 reading.)
- **Week 7 events:** Tesla and Meta Wednesday after the US close; clock change Sun 25 Oct; no Fed, no
  CPI. (`strategy/30-calendar.md` plus CNBC 20 Oct.)
- **Portfolio state:** `depot/positions.md` from 16 Oct 11:10 (5 days old today, past the three-day
  limit; in between only trading days without a live position or due order, so unchanged in practice
  but to be confirmed): Depot A €225,718.19 pure cash, Depot B €81,846.60 pure cash. No open position.
- **Egress/delivery:** `straits.live` via `WebFetch` returned `ENOTFOUND` (cloud egress; WebSearch
  snippets accessible and dated). Telegram not reachable from the cloud (no `.env`, `TELEGRAM_*` not
  set), so the delivery is this repo commit. No access to SG, no order.

---

## Addendum 09:10 Berlin (session with the player): alternatives to oil for the day bet until Thursday evening

**Run:** interactive session (the player, 08:40 Berlin). **Reason:** Depot A has no order; the player
wants a bet until Thursday evening (22 Oct, sell by 21:45), but **not oil** ("too high, too
uncertain"). Wanted: alternatives with a large move within 1.5 trading days.

**State:** Depot A €225,718.19 pure cash (16 Oct), Depot B €81,846.60 cash. The game ends Fri 30 Oct,
7 trading days left after today. Rules section 5 read: €20,000 per leveraged purchase, 20,000 units,
the ask price counts, fee €3.90. The Brent buy alert (FG8V8A, trigger 104.2) runs until 23 Oct.

### Portfolio assessment first

**The only dated catalysts until Thursday evening are quarterly results, and all of them come after
the Stuttgart close.** Tesla, Meta, IBM, Lam Research and Texas Instruments report today after the US
close (from 22:05 Berlin), SAP today at 22:05. Stuttgart trades the reaction only from Thursday 08:00
(SAP from the Xetra open at 09:00, US stocks fully from 15:30). Buying today means holding through the
price gap: the distance to the barrier must be larger than the expected move, otherwise the bet is a
coin toss with total loss on one side.

**No event, but the largest daily move: silver** (3–6 % a day over the last two weeks, turbos with a
5.5 % distance at leverage 18 and zero spread). Gold is tighter (1.3–2.4 % daily range, leverage 38 at a
2.5 % distance).

No direction forecast. The direction is the player's decision.

### Candidates (SG quotes as of 09:00 Berlin)

| Underlying | Catalyst | Expected move | Turbo leverage at a safe distance | Assessment |
|---|---|---|---|---|
| **Tesla** ~$380 | results today 22:05, plus SpaceX merger committees (Musk, 20 Oct) | options ±7.4 %, 10-year average 9.6 % | 8.5 % distance → leverage 11 | **Largest expected move, tight spreads, both directions tradable** |
| **SAP** ~€202 | results today 22:05, reaction at the Xetra open 09:00 | July: −2.8 % then +9 %; stock +58 % since the July low, high expectations | 7.6–8.5 % distance → leverage 11–12 | reaction visible from 09:00, all of Thursday to trade |
| **Meta** ~$694 | results today 22:05; 3 of the last 4 reactions negative, $10bn legal costs, capex worries | options ±7.1 %, 10-year average 10–12 % | at 09:00 SG quotes **no bid** (calls: 0 of 1,000 quoted) | check only from US pre-market |
| **Silver** ~$57.3 | no event; wild in both directions after the crash (−50 % since the January record of 121.79); 14 Oct −6 %, 15 Oct +3 % | 3–6 % a day | 5.5 % distance → leverage 18, zero spread | largest move without an overnight gap, but a knock-out within 1.5 days is realistic |
| **Gold** ~$4,114 | no event; at the 14 Oct low (4,095); rates high, Fed hike risk 28 Oct | 1.3–2.4 % a day | 2.5 % distance → leverage 38 | high leverage, tight distance |
| **Nasdaq-100** ~29,650 | tomorrow's reaction to Tesla/Meta/chips | 1–3 % a day recently | 2.5 % → leverage 37 | only useful as a **purchase tomorrow morning after the results** |
| Netflix ~$65.7 | results yesterday, −6 % after hours (ad forecast cut) | the move has happened | n/a | do not buy |
| IBM ~$241 | results today 22:05, ±7 % | only turbos from 10 % distance, spreads 1.5–15 % | leverage 6–8 | weak |
| Lam Research, Texas Instruments | results today, ±4.5–8.6 % | at 09:00 SG quotes no bid | n/a | only from US pre-market |

Macro until Thursday evening: only US initial jobless claims at 14:30, no CPI, no FOMC (blackout until
29 Oct), ECB only on 29 Oct. DAX firmer pre-market (futures ~25,540).

### Concrete orders (stake €20,000 minus fee each, units = 19,996 / limit, rounded down to 10)

**Only one of them, direction chosen by the player.** Limit = ask + 5 cents (the US quote at 09:00 is
after-hours, the price changes until 15:30). Sell at market by Thu 21:45.

| Bet | WKN | Barrier | Distance | Leverage | Ask 09:00 | Limit | Units |
|---|---|---|---|---|---|---|---|
| Tesla long | **FG6QH3** (BEST call) | $347.17 | 8.5 % | 10.9 | 3.11 | 3.16 | 6,320 |
| Tesla short | **FC96LC** (BEST put) | $412.37 | 8.6 % | 10.8 | 3.14 | 3.19 | 6,260 |
| SAP long | **FG74RQ** (BEST call) | €184.77 | 8.5 % | 10.9 | 1.83 | 1.88 | 10,630 |
| SAP short | **FG81VY** (BEST put) | €217.37 | 7.6 % | 11.7 | 1.71 | 1.76 | 11,360 |
| Silver long | **FC2YV6** (BEST call) | $54.11 | 5.5 % | 17.9 | 2.85 | 2.90 | 6,890 |
| Silver short | **FG7WZQ** (BEST put) | $60.63 | 5.8 % | 16.2 | 3.15 | 3.20 | 6,240 |
| Gold long | **FD12M9** (BEST call) | $4,009.44 | 2.5 % | 38 | 9.65 | 9.70 | 2,060 |
| Gold short | **FG7YWR** (BEST put) | $4,217.30 | 2.5 % | 39 | 9.51 | 9.56 | 2,090 |

Arithmetic for the Tesla turbo through the results: move ±7.4 % × leverage 10.9 = **±80 %**. A gap of
more than 8.5 % against the position is a knock-out and a total loss. The same applies in mirror image
to the put.

**Alternative without a barrier (warrant, the project instructions' recommendation for events after
22:00):** Tesla call **FG4VZM** (strike 380, expiry 20 Nov, ask €1.93, 10,360 units) or put **FG4WP1**
(strike 380, 20 Nov, ask €1.82, 10,980 units). Implied volatility ~51 %. Rough arithmetic: Tesla +7 %
→ call about +50 %, −7 % → about −60 % (volatility drops after the results). Loses to the turbo on
moves up to 10 %, but survives a 12 % gap in the wrong direction. SAP at the money: call FG3WCC (200,
20 Nov, €1.11), put FG8ZPV (200, 20 Nov, €0.91).

**Variant B, less of a lottery:** hold nothing overnight, and **tomorrow at 08:00 after the results**
buy the day's direction (Tesla/SAP with a 3 % distance as in the AMD day bets, or the Nasdaq-100 with
2.5 %). For that, set `depot/bet.json` to 22 Oct; the card arrives at 08:05 with live prices. This
gives up the gap and trades the follow-through.

Chance of winning: **no** for all of them (a day bet, no path to the winning mark; the main prize has
been written off since the €300k mark, the player's decision of 17 Sep).

### What I don't know

- Meta, Lam and TXN turbos: SG quotes no bids at 09:00; distances and spreads can be checked only from
  US pre-market (about 14:00–15:30).
- Implied moves come from tier-4 sources (TipRanks, Benzinga, Investing.com), not computed from an
  option chain.
- Silver daily data on Yahoo has gaps (several days with O=H=L=C); daily ranges from Kitco reports
  (14 Oct −6 %, 15 Oct +3 %).
- Brent not checked today (the player: no oil).

### Sources (tier)

- Tesla date: SEC 8-K (S1); implied move 7.43 % TipRanks/CoinCentral, 6.24 % Benzinga (S4); SpaceX
  committees CNN/NBC/CNBC 20 Oct (S2).
- Meta: ±7.1 % MarketPulse/Admiral (S4); $10bn legal costs, capex $130–145bn (S2/S4).
- SAP: date 21 Oct 22:05 CEST (SAP IR/MarketScreener, S1/S2); July reaction −2.8 %/+9 % (finanzen.net,
  S2); BofA/Jefferies backlog expectations (S2).
- Netflix: −6 % after hours, ad forecast 2.7 instead of 3.0 bn (Deadline/Investing.com, S2).
- Silver/gold: Kitco PM 14 Oct, 15 Oct, 19 Oct (S2); Mining.com/Yahoo on the crash (S2).
- Macro: Investing.com week preview 19–23 Oct, Kiplinger (S2). DAX: dpa-AFX/Reuters 21 Oct (S2).
- Prices/products: SG product finder API 09:00 Berlin (S1), Yahoo daily data 20 Oct (S1).

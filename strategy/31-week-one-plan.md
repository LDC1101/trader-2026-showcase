# Week one: the plan for 7–13 Sep 2026

*Written 4–7 Sep. The Oracle/DAX draft of 4 Sep (part 2) was replaced on 6 Sep by the Brent order card (part 1); on 8 Sep Depot B switched to a directional bet. See season/README.md for how the week went.*

Part 1 is the order card the player used on the first game day. Part 2 is the first draft, kept for
its reasoning and the market situation after the jobs report. All times are Berlin time (CEST).

## Part 1: Monday 7 Sep, 8:00, order card

Print it or keep it open on a second screen. Work through it in order.

### 0. Before the first order: once, irrevocable

**Complete the profile: full name and address.** Placing the first order with an incomplete profile
gives up any prize claim permanently. The choice cannot be undone later.

### 1. What is different today

**US markets are closed for Labor Day.** Oil futures and European stocks trade normally, US single
stocks do not. That is why today's stake goes on oil and not on a US stock.

**The weekend is not priced in.** Brent 96.28 is Friday's close. On Saturday 5 Sep the US disabled
three Iranian tankers (off Kharg, near Jask, in the Gulf of Oman) after the IRGC had fired two
missiles at a carrier and a destroyer; on Sunday 6 Sep the IRGC reported attacks on three tankers
and an unmanned US boat. In this crisis Brent moved more than 1.8% on 19 of 26 weekends, so the
WKNs pulled on Saturday are likely knocked out or too far away by Monday morning. Details are in
the evening update of the 6 Sep briefing.

**Check the overnight news before ordering. Two conditions; as of Sunday 22:50 neither is met:**

| Reported overnight | Then |
|---|---|
| a strike on the **Kharg terminal or Ras Tanura** itself (not on tankers) | do **not** buy the short leg in Depot B; long as on the card |
| "**blockade lifted / strait opens**" (wire, government, straits.live) | do **not** buy the long leg in Depot A; short as on the card |

An X post or IRNA on its own triggers neither; it takes a primary source as defined in
`00-thesis.md`.

### 2. The two orders

Both depots on opposite sides of the same theme, because only the better one counts for the main
prize. **Decided on 6 Sep: variant A.** Numbers in `60-research-2026-09-05.md`.

#### Variant A: Brent, opposite sides

| | Depot A: Brent long | Depot B: Brent short |
|---|---|---|
| Product | BEST turbo call, **pull fresh at 8:05 on Monday** (on Saturday no call under 3.0%) | BEST turbo put **FC8QP6**, barrier 98.04, leverage 47, ask €1.98 |
| Distance | ≤1.5%, otherwise do **not** buy | 2.1% to 96.0 (Saturday) |
| Stake | €20,000 | €20,000 = 10,101 units |
| Pays on | escalation → $120–150 = 26–57× | agreement / end of the blockade (28–35% by 31 Oct) → $72–80 = 9–13× |

If there is no Brent call at ≤1.5%: **leave Depot A empty** and check again every hour (the Watch
sends the card as soon as SG lists one; on 7 Sep it came at 9:30). **No substitute.** The gold put
bought on 7 Sep had no path to the winning mark and had to be sold an hour later. Depot A holds only
instruments that can reach the winning mark; a placeholder costs more than an empty hour.

#### Rotation target after a knock-out: gold, opposite sides

| | Depot A: gold long | Depot B: gold short |
|---|---|---|
| Product | BEST call **FG6QYM**, barrier 4,390.25, leverage 91, ask €4.28 | BEST put **FG6QX8**, barrier 4,486.32, leverage 80, ask €4.71 |
| Distance | 1.05% | 1.12% |
| Units | 4,672 | 4,246 |
| Evidence | one side survives 40 days in 32.8% (Brent 15.1%), ≥10× in 19.1% (Brent 8.2%), spread 0.2% | catalyst Fed 16 Sep 20:00, 49.5% for a hike; managed money −233k short |

No path to the winning mark at 1% (gold never rose 66% in 40 days). Good for rank and the weekly
ranking.

**Rotation:** only after the first knock-out does the affected depot move to gold, opposite to the
other depot. No early rotation, not even for the Fed on 16 Sep: a live Brent position is not
touched.

### 3. Pulling products: no longer by hand

```bash
python3 src/sg_products.py --asset -4 415 --max 0.02 --n 6
```

This reads the SG interface directly: WKN, barrier, distance, leverage, bid, ask, spread. The rules
stay: **BEST or Classic, never X-BEST/X-Classic**, distance **1–2%**, ask above €1.00 (below that the
20,000-unit cap limits the stake: at €0.80 to €16,000), tight spread. The distance is derived from
the product prices; if in doubt, check it against the live price.

| Distance | Leverage | P(winning mark) | P(good rank) | Knock-out |
|---|---|---|---|---|
| **1.0%** | 100 | **1.17%** | **4.3%** | 94.9% |
| 2.0% | 50 | 0.01% | 5.0% | 90.1% |
| 4.0% | 25 | 0.00% | 1.2% | 81.4% |

Count on the knock-out. At 1% the median knock-out day is day 1, for every underlying, measured over
three years.

Then the units:

```bash
python3 src/sizing.py 100000 --ask <ask> --leveraged
```

### 4. Right after each purchase

**A limit sell order at 67.5 times the ask, valid 7 days.** That is the winning mark (€1.35M from
€20,000) placed as an order at entry: "secure only above the winning mark" without anyone having to
watch. `src/morning_card.py` computes the price and puts it in the buy message.

**No limit below that.** This used to say "+150%", which would be a sale at 2.5 times. The thesis
measures exactly that: selling at 3× lowers P(winning mark) from 2.70% to 0.029%, a factor of 93. A
running winner is not touched until it is above the winning mark.

The order can be placed immediately and becomes active after the 5-minute holding period. It is the
platform's own order type, not an automated system. Validity is 7 calendar days: **renew it every
Monday**; the Watch sends a reminder.

**Holding period:** until knock-out or 30 Oct. Measured at 1% distance: median knock-out on day 1,
one side survives 40 days in 15% of cases (Brent). The knock-out is the normal case; re-enter
immediately afterwards, `src/morning_card.py` delivers the order the next morning.

### 5. What you do NOT do today

- **Do not treat knock-outs as mistakes.** At 1–2% distance the position dies in about nine of ten
  cases. Re-enter immediately (this measurably raises the median and P(>500k)), and if the depot
  falls below €100,000, reset it on Monday.
- **Do not take profits.** Measured: selling at 3× lowers the chance of the main prize from 2.70% to
  0.029%, a factor of 93. A running winner is not touched; the only limit order sits at the winning
  mark.
- **Do not buy stocks.** The base stays in cash. Measured as irrelevant (2.728% against 2.852%), and
  it saves eight to ten orders at €10 each on a thin holiday.
- **No second user name.** Immediate exclusion, both depots drop out of the ranking.

### 6. After trading, record it

Fill in `depot/positions.md`: WKN, units, entry price, knock-out barrier, placed sell orders with
their expiry date.

Every cloud routine and every later session reads the state from there. Without the entry nobody
can tell you anything concrete on Tuesday morning.

### 7. This week

| Day | Event | Time | Significance |
|---|---|---|---|
| **Mon 2026-09-07** | US markets closed (Labor Day) | | Stuttgart trades, US underlyings do not move |
| Tue 2026-09-08 | US markets open again | | first normal trading day |
| **Thu 2026-09-10** | Oracle + Adobe earnings | after the US close (from 22:00) | reaction as a price gap on Friday morning |
| **Fri 2026-09-11** | **US consumer prices (CPI)** | **14:30** | during trading; moves oil through the rate channel; according to Morgan Stanley decisive for the Fed meeting |
| Wed 2026-09-16 | FOMC with projections | 20:00 | rate hike ~63% priced in |
| Fri 2026-09-18 | major expiry day | | |

The Hormuz status can change on **any** day. If an agreement is reported: **close Depot A at once,
let Depot B run.**

## Part 2: the first draft of 4 Sep (Oracle and DAX)

Research as of Friday 4 Sep, after the US close. Replaced on 6 Sep by part 1.

### The situation

Friday's jobs report turned the rate outlook around: **162,000 new jobs against an expected
53,000–55,000**, almost three times as many. Unemployment unchanged at 4.1%.

Consequences on Friday:

- Yields jumped, stocks fell. Dow −0.51% to 53,414, S&P −0.38% to 7,718.60, Nasdaq −0.29% to 26,507.
- **The probability of a rate hike on 16 Sep rose to about 63%.** A hike, not a cut.
- Gold fell to $4,419, −2.1% on the week. Gold miners (GDX) −3.76%.
- Bitcoin +3.23% to $81,225.

**The VIX closed at 14.53, up just 0.08 points.** A jobs report that beat expectations threefold and
reversed the rate outlook barely moved implied volatility, which stays at its low for the year.

That is the tradable observation of the week, and it concerns the **price of optionality**, not the
direction of the market: convexity is cheap while a market-moving inflation report and a rate
decision with a 63% hike probability are due within ten days.

### What to do on Monday at 8:00 (draft)

**Do not fire everything at once.** Monday is the worst trading day of the week: US markets are
closed, SG quotes wider spreads on US underlyings, and the first real event is on Thursday. Going
all in at 8:00 on Monday buys illiquidity and loses three days of time value before anything
happens.

**Depot A and Depot B, Monday:**

1. **Check the profile.** Full name and address must be entered before the first order, otherwise
   the prize claim is gone for good.
2. **Build a stock base** (about 60–80% of the capital per depot, European stocks that trade
   normally today). Four to five positions of at most 20% each. This base is not the return engine;
   it is the depot value the 20% rule refers to. (Part 1 replaced it with cash, see `00-thesis.md`.)
3. **No leveraged position on US underlyings on Monday.** Wait until Tuesday, when New York trades
   again and spreads are normal.
4. At most a small DAX leveraged position, if being in the market at once matters, and then as a
   **BEST or Classic turbo, not X-BEST/X-Classic** (see `20-instruments.md`).

**Tuesday/Wednesday: build the leveraged position.**

That is when the €20,000 goes in. Two candidates, deliberately uncorrelated across the two depots:

| | Depot A | Depot B |
|---|---|---|
| Underlying | **Oracle (ORCL)** | **DAX** |
| Occasion | earnings Thu 10 Sep after the close | CPI Fri 11 Sep 14:30 + FOMC Wed 16 Sep |
| Instrument | **warrant** (plain, no knock-out) | **BEST turbo** (not X-BEST) |
| Why this instrument | The report comes when Stuttgart is closed, so the reaction is a price gap. A turbo can run through its barrier overnight with no chance to react; a warrant has no barrier. | CPI comes at 14:30, during trading. A turbo is cheaper than a warrant and gives more leverage. |
| Term | at least until mid-October, so time value remains after the earnings | open end |

**Why Oracle.** The stock moves hard on earnings: −15% on the December report (capex shock), +9% on
11 Mar 2026, most recently an implied move of about ±11%. From its high above $345 in September 2025
it fell about 62% to $130.99 and stabilised. The order backlog of $553–638B is about eight times
annual revenue, and every number on it moves the stock by double digits. A dated event with an
expected double-digit move is the constellation the tournament maths asks for: a guaranteed move,
an open direction.

**On direction.** The draft had none. If a direction has to be chosen (and maximum variance requires
one), treat it as a coin toss, not as analysis. A straddle of call and put reduces variance and is
the wrong choice for this tournament, however sensible it would be as an investment.

### Exit rules, fixed in advance (draft)

Nobody watches continuously, so the exits are fixed now rather than decided in the moment. That is
also more robust, because nobody calculates soberly during the move.

**Oracle warrant (Depot A):**

- Report Thu 10 Sep after the close → **assess on Friday at 8:00, not earlier.**
- Stock +8% or more: **hold**, do not sell. The big hit comes from holding, not from taking profits.
- Stock between −5% and +8%: hold until Monday, then close. From here time value works against the
  position.
- Stock −5% or worse: close during Friday, secure the rest, check the weekly reset for Depot B.

**DAX BEST turbo (Depot B):**

- CPI Fri 11 Sep 14:30. Do nothing before.
- Knocked out: reset the depot on Monday if it is below €100,000.
- In profit: hold until the FOMC on Wed 16 Sep. The rate decision is the real event; CPI is only the
  run-up.
- Reassess after the FOMC.

**For both, the rule from `00-thesis.md` applies:** below €500,000 nothing is secured. At that level
there is nothing to lose, and securing removes the only chance.

### What to send on Friday evening

To plan week two over the weekend, the following is needed:

- the depot values of both depots
- open positions with entry price, current price and WKN
- weekly rank and overall rank

Enter it in `depot/positions.md`. Without that state the answer can only be general; with it, it can
be concrete.

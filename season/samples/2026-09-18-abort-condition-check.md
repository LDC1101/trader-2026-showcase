# Morning briefing, Friday 18 Sep 2026 (week 2, trading day 10)

> **Editor's note:** the copy of the positions file this routine read still stood at 15 Sep. The log
> in `depot/positions.md` shows that FG6MRT was knocked out on 16 Sep between 17:30 and 18:00 Berlin
> (Brent low 104.06 against the barrier 104.74), not on 17 Sep. On 17 Sep the player bought a Brent
> BEST put (FG6SKV, 6,300 units at €3.09) and sold it about ten minutes later for roughly +€1,400 net,
> then ran an AMD day bet with a BEST turbo call on 17/18 Sep. The platform showed Depot A at
> €161,700.09 cash on 19 Sep. The player did not switch to warrants; from 17 Sep they played day bets
> with turbos. The text below is the routine's output as written.

**Run:** cloud routine (morning briefing). **Delivery:** repo commit. Telegram is not reachable from
cloud routines (`test -n` → "not configured", no `.env`; the egress proxy blocks `curl`/POST). In
addition, a push notification to the player, because Depot A has very probably been knocked out and a
decision is due today (see TODAY). This briefing is written to be complete when read in the repo.

**Data basis:** `depot/positions.md` entry of **15 Sep 09:35, 3 days old today, so at the limit of
"stale".** In addition, the Brent call FG6MRT listed there as "alive" has, according to the evening
check of 17 Sep, very probably been **knocked out** and not yet recorded by the player, so the
position state is **no longer reliably current**. I invent no portfolio value, no WKN, no price. The
situation comes from WebSearch on S2 sources (Reuters/CNBC wire across several outlets); **straits.live
and cnbc.com are egress-blocked for WebFetch** (`EGRESS_BLOCKED`), the Hormuz status and the oil price
come from search. No SG bid price is retrievable from the cloud.

---

## Portfolio assessment first

**Depot A: the Brent call FG6MRT has very probably been knocked out. The player must confirm this on
the platform today and then re-enter at once.** Oil has fallen further: Brent is at ~$103.8 and touched
a low of $103.43 today, clearly **below** the FG6MRT knock-out barrier ($104.74). A BEST turbo knocks
out when the barrier is touched; the price has been below it several times since last night. This is
the planned normal case of the thesis, and the loss is capped at the stake (~€19.8k). **To do:** check
on the platform whether FG6MRT has been booked out; on a confirmed knock-out, re-enter immediately.

**And this time switch instrument: warrant instead of turbo.** This would be the **third turbo
knock-out in a row** (Brent put 8 Sep, gold call 11 Sep, FG6MRT 17 Sep). The abort condition "three
knock-outs of the same type → turbo to warrant" exists for exactly this case. It fires now, and the
market fits: the VIX (the fear gauge) is very low at ~15.4, so convexity is cheap; a Brent call warrant
has **no knock-out barrier** that a further slide can hit. Stake as always €19,996 (€20,000 minus fee).
WKN and units come from the morning card or the SG finder on the player's machine; not retrievable
from the cloud. **No direction forecast:** I do not say where oil goes; Depot A remains the oil-long
leg of the thesis, and the thesis re-enters immediately after every knock-out to catch the next large
move.

**Depot B: do nothing, stays cash.** The player's decision of 15 Sep to play only Depot A. No
counter-leg, no new bet.

**No abort of the strategy, no change of theme.** The Strait of Hormuz is still closed (day 201), no
reported opening, no agreement. The oil slide comes from a supply valve (Saudi cargoes via Oman/Sohar),
not from a Hormuz opening; abort condition 1 is explicitly **not** triggered.

---

## Prices (snapshot 18 Sep)

| Instrument | Level | Change | Source/tier |
|---|---:|---|---|
| **Brent (front = Nov 26)** | **~$103.83** | −0.94 % today; daily range **103.43–106.00**; previous close ~104.82 | Reuters/CNBC wire (EnergyNow/Investing), S2 |
| WTI | ~$101.01 | −0.88 %, holds above $100 | CNBC wire, S2 |
| **S&P 500** | **7,637.72** | +1.12 % (17 Sep) | Yahoo/vittarthi quote, S2/S4 |
| **DAX** | **25,331.36** | −0.93 % (17 Sep) | quote, S2/S4 |
| **VIX** | **~15.4** | −2.3 pts, **very low** | Cboe/Yahoo quote, S2/S4 |

**On the barrier:** the FG6MRT barrier is $104.74. Brent has been below it several times since the
evening of 17 Sep (evening check: ~$103.6) and touched $103.43 today → **turbo very probably knocked
out.** The exact SG bid and the book-out are not retrievable from the cloud; the player confirms on the
platform.

**No portfolio value invented.** Last recorded state (`positions.md` 15 Sep 09:35): Depot A
€141,447.49 cash plus call FG6MRT (7,603 units). The call has now very probably been booked out as
worthless, so Depot A falls back to its **cash base of ~€141,447** (the ~€19.8k stake is the capped
loss; above €100,000 → **no reset needed**). Computed, not measured; the player confirms. Depot B
€81,846.60 cash.

## Strait of Hormuz: closed, day 201, no opening

- **Closed, day 201.** Only single-digit transit counts (8 on 13 Sep against a normal ~85 a day). No
  implemented opening, no lifting of the blockade. (straits.live headline "Closed, Day 201" via
  search; CNN/Al Jazeera, S2; straits.live egress-blocked for WebFetch.)
- **The Iran–Gulf states talks on reopening (Oman's plan) remain postponed indefinitely**; the regional
  meeting planned for Salalah has been put off. Trump considers the current state (US escorts for
  tankers) acceptable; the US wants to steer future Iran talks to the nuclear issue, not the strait.
  **No date, no agreement, no opening in sight.** (CNN 13 Sep, Al Jazeera, S2.)
- **Price-relevant today:** (1) Saudi Arabia is rerouting some crude exports through the Strait of
  Hormuz and offering Asian refiners extra cargoes via ship-to-ship transfer off Oman/Sohar to make up
  for the damaged pipeline; this eases the supply fear and pushes the price down. (2) Against that:
  **fresh attacks between Saudi Arabia and the Houthis** keep geopolitical risk high, which is why WTI
  stays above $100 and Brent above $103. (CNBC/EnergyNow 18 Sep, S2.)
- **Effect on oil:** net softer, but no volatility collapse. **Abort condition 1 (Hormuz
  opening/agreement) NOT triggered.**

## News by topic

- **Oil (centre stage):** Brent −0.94 % to ~$103.8, WTI −0.88 % to ~$101.0. Drivers: the Saudi supply
  workaround via Oman/Sohar eases the outage worry, weighed against new Saudi–Houthi strikes. The
  diesel market stays very tight, Saudi infrastructure is damaged, Hormuz traffic still throttled: the
  floor stays firm. (CNBC/EnergyNow wire 18 Sep, S2.)
- **Fed/rates:** the FOMC hike of 16 Sep (+25 bp to 3.75–4.00 %, the first since 2023) has been
  digested; no new rate gap. Equities firm after the Fed. (S2.)
- **Equities:** S&P 500 +1.12 % to 7,637.72, VIX down to ~15.4 (very low), exactly the setting in
  which warrant convexity is cheap. DAX −0.93 % (25,331). For the Depot A re-entry, the low VIX argues
  **for** the warrant.

## Events today and this week

| Day | Event | Meaning |
|---|---|---|
| **Fri 2026-09-18** | **Major expiry day (quadruple witching)** | higher volume, jerky moves; for a turbo re-entry today choose a generous distance to the barrier; argues further for the warrant without a barrier |
| any time | Hormuz / Bab el-Mandeb status; oil supply news (Saudi/Oman) | main catalyst, no fixed date |
| Sun 2026-09-20 | end of game week 2 (scoring overnight Sun to Mon) | the Depot B weekly reset lapses with the week change (put on hold by the player) |

## Check against the abort conditions (`strategy/00-thesis.md`)

| Condition | State 2026-09-18 |
|---|---|
| Hormuz agreement reported → close the long portfolio | **no:** strait closed (day 201), meeting postponed, no opening. Oil slide = supply valve (Saudi/Oman), not a Hormuz opening |
| Portfolio < €100,000 and no position alive | **Depot B: ~€81,847 cash, no position:** reset technically due, but deliberately put on hold on 15 Sep (only Depot A). Depot A falls to ~€141,447 cash after the knock-out → above €100,000, **no reset**, but **a new position at once** (thesis) |
| **Three knock-outs in a row, same instrument type → turbo to warrant** | **TRIGGERED (on a confirmed knock-out):** Brent put 8 Sep, gold call 11 Sep, FG6MRT 17 Sep = 3 turbo knock-outs in a row. Re-enter with a **warrant**, not a turbo. VIX ~15.4 → convexity cheap, fits |
| After week 5 (from 12 Oct) below €300,000 | n/a: week 2 |
| Portfolio above the winning mark AND in the lead | n/a: best recorded portfolio ~€141k cash, factor ~9.6 to €1.35M |
| Oil volatility collapses (strait permanently open) | **no:** strait closed; oil eased because of a supply valve, no volatility collapse |
| VIX above 25 → avoid warrants | **no:** VIX ~15.4, very low → warrant explicitly preferred |
| Sideways regime (Brent efficiency < 0.25 with net move < 5 %) | **watch:** Brent from ~107.5 (16 Sep) to ~103.8 (18 Sep), directionally down, no sideways band yet; `src/regime.py` re-measures on the player's machine |

**Triggered: the three-knock-out condition** (instrument switch turbo to warrant), on a confirmed
FG6MRT knock-out. Abort condition 1 (Hormuz) still not triggered.

## TODAY: what to do

**Depot A, step 1: confirm the knock-out.** Check on the platform whether FG6MRT has been booked out
(the cloud has no SG or portfolio access). Brent has been below the $104.74 barrier several times since
last night (today's low $103.43); the turbo is very probably gone.

**Depot A, step 2: on a confirmed knock-out, re-enter at once, as a warrant.** It is the third turbo
knock-out in a row → the abort condition "turbo to warrant" applies, and the VIX (~15.4) makes
convexity cheap. So a **Brent call warrant** (no knock-out, no gap or expiry-day danger), stake
**€19,996**, WKN and units from the morning card or the SG finder on the player's machine. Then set a
sell limit as the winning-mark safeguard. **No direction forecast:** Depot A remains the oil-long leg,
and the thesis re-enters at once after a knock-out.
*(If the player wants to stay with the turbo after all: BEST call, no X-BEST/X-Classic, and because of
the expiry day a generous barrier today: at least $2.5 distance, preferably more.)*

**Depot A, sell order:** the winning-mark limit of €175.50 on FG6MRT (valid until 22 Sep) is **moot**
after the knock-out; nothing to renew. Set a fresh limit for the new position.

**Depot B: do nothing.** Stays cash (the player's decision of 15 Sep). No purchase, no counter-leg.

**No abort, no change of theme.** Hormuz stays closed (day 201), no opening. Oil remains the most
volatile theme.

**Please record:** `depot/positions.md` stands at 15 Sep (3 days). Please enter the FG6MRT knock-out
and the new position so that the Watch and the regime check compute on reliable figures again.

---

### Short version (Telegram format; not sendable from the cloud, so committed to the repo, plus a push)

> **Depot A: your Brent call has very probably been knocked out.** Oil fell further (Brent ~$103.8,
> today's low $103.4, clearly below the barrier of $104.74). Please check on the platform whether
> FG6MRT has been booked out, and **re-enter at once, this time as a call warrant, not a turbo** (it is
> the third turbo knock-out in a row, and the low VIX makes the warrant cheap; no knock-out, no
> expiry-day danger). Stake €19,996, WKN and units from your morning card. Depot B stays cash. Hormuz
> still closed (day 201), no abort. The loss was capped at the stake, the planned normal case.

### Sources

- **Brent** ~$103.83 (−0.94 %, range 103.43–106.00, previous close ~104.82), **WTI** ~$101.01
  (−0.88 %); reason: the Saudi supply workaround via Oman/Sohar against new Saudi–Houthi strikes
  (CNBC/EnergyNow/Investing wire 18 Sep, S2). cnbc.com egress-blocked for WebFetch, values from search.
- **Hormuz:** closed, day 201, single-digit transits; Salalah meeting postponed, the US steers towards
  the nuclear issue, no opening (straits.live via search, CNN 13 Sep, Al Jazeera, S2). straits.live
  egress-blocked for WebFetch. Abort condition 1 not triggered.
- **Equities/VIX:** S&P 500 7,637.72 (+1.12 %), DAX 25,331.36 (−0.93 %), VIX ~15.4 (−2.3 pts)
  (Yahoo/vittarthi/Cboe quote, S2/S4).
- **Depot A knock-out:** evening check of 17 Sep plus the Brent range on 18 Sep down to $103.43 < the
  $104.74 barrier → FG6MRT very probably knocked out; to be confirmed by the player on the platform. No
  SG bid in the cloud.
- **Egress/delivery:** straits.live and cnbc.com blocked for WebFetch (`EGRESS_BLOCKED`); Telegram not
  reachable from the cloud → the delivery is this repo commit plus a push notification; email is never
  used. No portfolio value and no SG bid invented.
- **Data basis:** `depot/positions.md` entry of 15 Sep 09:35 (3 days old, at the limit; the position
  FG6MRT listed there as "alive" is very probably knocked out and not recorded).

---

## Evening check (cloud routine, after the 22:00 close)

**No new action needed compared with the morning briefing, so no second message.** The only action
still open today (confirm the FG6MRT knock-out and re-enter as a warrant) was already reported last
night **and** this morning (with a push). It stands unchanged; a third message on the same point would
only dull the signal. So tonight only this note, no new push or Telegram.

**Checked:**

1. **Hormuz: no change that forces a decision.** The strait is still **closed, day 202** (this morning
   day 201). Iran and Oman have an **understanding** on a temporary corridor, but that means **no**
   immediate opening; an earlier Oman agreement was rejected by the US, and the regional meeting still
   has no date. The US blockade has **not** been lifted. So **abort condition 1 (implemented
   opening/lifting of the blockade) is NOT triggered**; a mere Iran–Oman understanding is explicitly
   not enough under the routine's instructions. (straits.live "Closed, Day 202"; CBS/Al Jazeera/The Hill
   via search, S2; straits.live and cnbc.com egress-blocked for WebFetch.)
2. **Position knocked out?** FG6MRT has been suspected knocked out since yesterday and was reported as
   such; **nothing new tonight**. `positions.md`, at 15 Sep 09:35, is now **older than 3 days**, so the
   knock-out book-out, cash and portfolio value **cannot be checked reliably from the cloud**. No price,
   no portfolio value invented. The player confirms on the platform.
3. **Other abort condition?** Only the three-knock-out rule (turbo to warrant) triggered this morning,
   already covered in the briefing, nothing new. VIX ~15.4 (below 25), no volatility collapse, no
   sideways abort confirmed (measured by `regime.py` on the player's machine).
4. **Limit or stop orders about to expire?** The winning-mark limit of €175.50 on FG6MRT (valid until
   22 Sep) is moot on a confirmed knock-out. Because `positions.md` is stale it **cannot be checked
   reliably** whether another order expires soon; already noted in the morning briefing.
5. **Reset due?** Depot A falls to its cash base after the knock-out (~€141k, computed, not measured)
   → above €100,000, **no reset**. Depot B ~€81,847 cash without a position: reset technically due,
   but deliberately put on hold by the player on 15 Sep (only Depot A). **Nothing new.**

**Oil today:** Brent front ~$103–104, WTI ~$101 (third losing session in a row; supply fear eased by
Saudi cargoes via Oman/Sohar). Directionally down, no volatility collapse. (CNBC/tradingeconomics wire
18 Sep, S2.)

**Conclusion:** strait still closed, no abort, no new order trigger. Only the action already reported
remains open. Please update `depot/positions.md` (FG6MRT knock-out and any new position) so the Watch
computes on reliable figures again.

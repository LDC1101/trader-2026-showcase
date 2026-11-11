# Season record

**Result: Depot A more than doubled (over +100 %), top 1 % out of 23,982 participants**, per the
official participation certificate dated 30 Oct 2026. The positions log's last confirmed state is
€232,469.59 cash on 26 Oct. Depot B's last
recorded state is €81,846.60 cash (−18.15 % from its 8 Sep reset, idle since 15 Sep); whether it
was played on the last day is not documented.

The game ran from 7 Sep to 30 Oct 2026 (40 trading days). Every order was typed by hand on the
game platform; no part of the system had access to the game account (Rule 10).

| Path | Contents |
|---|---|
| [../depot/positions.md](../depot/positions.md) | the positions log, every order with its reason and outcome |
| [weekly/](weekly/) | the seven weekly reviews (13 Sep to 25 Oct), translated |
| [final-review.md](final-review.md) | the final review of 1 Nov, translated |
| [samples/](samples/) | three translated daily briefings |

The cloud routines read the positions file from the remote repo, which often lagged the real
trades (between 15 Sep and 16 Oct, and again after 21 Oct). Their reviews are translated as
written; an editor's note under each affected header states what the log shows. The routines kept
running after the game (daily briefings 2–10 Nov and a weekly review on 8 Nov, all "no action
needed") until they were paused on 11 Nov 2026. Those post-game runs are not included.

## Trades

Entry and exit are product prices in €. Net P/L includes the €3.90 order fee on each side.
Return is exit price over entry price minus one, before fees. All products are SG BEST turbos.

| # | Depot | In | Out | Underlying | Product | Dir. | Units | Entry | Exit | Net P/L (€) | Return |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| 1 | A | 2026-09-07 | 2026-09-07 | Gold | put FG6SFQ | short | 4,000 | 4.91 | 4.97 | +232.20 [1] | +1.2 % |
| 2 | A | 2026-09-07 | 2026-09-10 | Brent | call FG6GK5 | long | 14,489 | 1.38 | 5.59 | +60,990.89 | +305.1 % |
| 3 | A | 2026-09-15 | 2026-09-16 | Brent | call FG6MRT | long | 7,603 | 2.60 | knock-out | −19,764.10 [2] | −100 % |
| 4 | A | 2026-09-17 | 2026-09-17 | Brent | put FG6SKV | short | 6,300 | 3.09 | ~3.31 | ~+1,400 [3] | ~+7.1 % |
| 5 | A | 2026-09-17 | 2026-09-18 | AMD | call (FG7EES recommended) | long | not recorded | not recorded | not recorded | ~+18,840 [4] | not recorded |
| 6 | A | 2026-09-21 | 2026-09-24 | AMD | call FG7EGK | long | 6,770 | 2.85 | 5.46 | +17,661.90 | +91.6 % |
| 7 | A | 2026-09-24 | not recorded | AMD | call FG7KMN | long | 9,560 | 2.03 | 4.84 [5] | +26,855.80 [5] | +138.4 % [5] |
| 8 | A | 2026-10-05 | 2026-10-09 | Brent | call FG7MXN | long | 3,880 | 5.03 | 7.95 | +11,321.80 | +58.1 % |
| 9 | A | 2026-10-12 | 2026-10-14 | Brent | call FG8V8A | long | 3,790 | 5.23 | 7.39 | +8,178.60 | +41.3 % |
| 10 | A | 2026-10-21 | 2026-10-26 | Tesla | call FG8GV8 | long | 5,680 | 3.45 | 4.64 | +6,751.40 | +34.5 % |
| 11 | A | 2026-10-27 (order) | not recorded | Seagate | call FE4E7Y | long | 2,890 (order) | limit 6.90 | not recorded | not recorded [6] | not recorded |
| 12 | B | 2026-09-07 | 2026-09-08 | Brent | put FC8QQU | short | 11,288 | 1.45 | knock-out | −16,371.50 | −100 % |
| 13 | B | 2026-09-08 | 2026-09-08 | Brent | call FG6GLL | long | 8,500 | 1.98 | ~2.14 | +1,352.20 | +8.1 % |
| 14 | B | 2026-09-08 | 2026-09-11 | Gold | call FG6PCD | long | 2,660 | 7.33 | knock-out | −19,501.70 [7] | −100 % |

Depot B was reset to €100,000 on 8 Sep between trades 12 and 13.

1. The log text says +€228 net. 4,000 × (4.97 − 4.91) − 2 × €3.90 = €232.20 is the figure that
   reconciles with the recorded cash of €161,223.09 on 10 Sep.
2. Stake €19,767.80 plus €3.90 fee, less a €7.60 residual credit. The log's cash figures
   (€161,223.09 before, €141,455.09 after) imply −€19,768.00; the source does not explain the
   €3.90 difference.
3. The player's figure. The exit price is recorded only as "about 3.31"; at 3.31 the computed net
   is €1,378.20.
4. Units, prices and the number of round trips were not recorded. Derived from cash: ~€142,860
   after the put sale to €161,700.09 on the platform on 19 Sep.
5. Sale price and date not recorded (sold by 5 Oct). Derived: the log's cash went from €159,951.29
   (24 Sep, after the purchase) to €206,217.79 (5 Oct, before the next purchase), net proceeds of
   €46,266.50, which is exactly 9,560 × €4.84 − €3.90. This assumes no other trade in between.
6. Fill and exit not recorded, so the result of everything Depot A did after 26 Oct is unknown.
7. Stake €19,497.80 plus €3.90 fee. Depot B's recorded cash after the knock-out (€81,846.60) is
   €3.90 lower than the listed trades give; the source does not explain the difference.

## Timeline

**Week 1 (7–13 Sep).** Brent rose 9 % to ~$104.6 while the S&P lost 0.8 %; the Strait of Hormuz
stayed closed. Depot A swapped a gold put for the Brent call FG6GK5 on day one and sold it on
10 Sep at +305 % (€161,223.09); the tighter re-entry limit never filled. Depot B lost a Brent put
and a gold call to knock-outs around a reset; the weekly review said to buy oil long again on
Monday and to reset Depot B.

**Week 2 (14–20 Sep).** Brent consolidated (net about −1.4 % to $103.87). The player bought
FG6MRT on 15 Sep, parked Depot B the same day, and lost FG6MRT to a two-hour dip on 16 Sep that
the Watch missed because it checked prices rather than lows (it was changed to check the low and
high since its last run). From 17 Sep the player switched to day bets: a Brent put sold after ten
minutes and an AMD call intraday took Depot A to €161,700.09; the weekly review, working from the
stale file, said the three-knock-outs abort condition had fired and the re-entry should be a
warrant.

**Week 3 (21–27 Sep).** A Houthi strike on Yanbu sent Brent from about $98 to $108.23 and Trump
rejected Iran's phased reopening plan on 26 Sep. The AMD call FG7EGK returned +91.6 % (Depot A
€179,361.99 on 24 Sep) and the player bought FG7KMN the same day and held it overnight. The review
could not see Depot A's value and urged a Brent call warrant and an update of the positions file.

**Week 4 (28 Sep–4 Oct).** Brent swung from 107 to 96.8 and back to 102.25 (a third US carrier, a
100-million-barrel reserve release, unchanged OPEC+ quotas). FG7KMN was sold at a price and date
not recorded, leaving €206,217.79 cash. The review called week 5 decisive because of the €300,000
mark on 12 Oct.

**Week 5 (5–11 Oct).** Brent ranged ~$97–106 and closed at ~$104.72 (+2.4 %), with attacks at a
wartime high. The player bought the Brent call FG7MXN with 5 % distance to barrier on 5 Oct and
sold it on 9 Oct at +58 % (€217,539.59). The review, still assuming ~€141k, said the 300k abort
condition applied from 12 Oct and recommended writing off the main prize (Path A), leaving the
choice to the player.

**Week 6 (12–18 Oct).** Brent broke out of its 101.5–107 range to $109.86 (+4.9 %, highest since
May). The player bought FG8V8A on 12 Oct and sold it on 14 Oct at +41.3 % (€225,718.19). A buy
alert in GitHub Actions was added for a pullback entry; the review said the sideways regime was
ending and advised against a forced buy at the high.

**Week 7 (19–25 Oct).** Brent rose about 7 % to ~$117, a five-month high, on attacks on tankers and
Saudi infrastructure. The pullback the player waited for never came, so on 21 Oct the player bought the
Tesla call FG8GV8 as an earnings day bet. The review said never to reset Depot A, to close the
Tesla call if still open and not to buy oil at the high.

**Week 8 (26–30 Oct).** Brent eased to ~$114 on Qatari mediation and talks in Tehran (last
confirmed ~$115–116 on 28 Oct), the strait still closed; the FOMC held rates on 28 Oct. The player
sold Tesla on 26 Oct at +34.5 % (€232,469.59) and placed a Seagate earnings order on 27 Oct whose
outcome was not recorded. The briefings repeated daily: hold Depot A, do not reset, do not buy oil
on deal hopes.

## The shift on 17 Sep

**Before.** The thesis (`strategy/00-thesis.md`) was to hold one leveraged position per depot and
roll it toward the winning mark (€1.35M, the 2025 winner): never take profits, because taking them
at 3× cuts P(≥€1.35M) from 2.70 % to 0.029 % (a factor of 93), and run the two depots in opposite
directions. Depot A held FG6GK5 from €1.38 to €5.59 and sold it only to re-enter with a tighter
barrier (a simulation gave P(>500k) 6.9 % → 9.6 %); FG6MRT was bought on 15 Sep with a sell limit
at the winning mark (€175.50, 67.5× entry) and the instruction "hold until knock-out or winning
mark". It was knocked out the next day. Depot A stood at €141,455.09.

**After.** From 17 Sep Depot A played day bets out of cash and took every profit: a Brent put held
ten minutes, AMD calls held from hours to several days, Brent calls with ~5 % distance to barrier
held two to four days and sold at +41 % to +58 %, then earnings bets on Tesla and Seagate. The
morning card took the day's bet from `depot/bet.json`, and orders were written as WKN, limit and
units. From 22 Oct the briefings record this as the player's decision of 17 Sep: main prize written
off, Depot A plays day bets. From 16 Sep to 26 Oct Depot A grew from €141,455.09 to €232,469.59
(+64.3 %); all seven recorded bets after 17 Sep were profitable and none was knocked out.

**What the final review concluded.** The topic thesis held: Hormuz stayed closed for all eight
weeks and oil moved more than anything else. Abandoning "never take profits" produced what the
thesis predicts: gains added up instead of compounding, because each new bet was again capped at
€20,000. The result (estimated at ~€224k in the review) sits in the lower middle of the thesis
distribution (median for "hold and roll" €383k) and below every line aimed at the main prize. The
review calls it a deliberate choice of capital preservation over a lottery tail, not a mistake,
and the reason the main prize was mathematically out of reach. The opposite-direction pair, which
the thesis rated as its biggest lever (P(>500k) 40 % → 56 %), was never tested, since Depot B was
parked on 15 Sep.

## Numbers

| | |
|---|---|
| Positions opened | 14 (Depot A 11, Depot B 3), counting the AMD intraday trades of 17/18 Sep as one and including the Seagate order whose fill was not recorded; 13 with a recorded outcome |
| Wins / losses | 10 / 3 (Depot A 9 / 1, Depot B 1 / 2); Seagate outcome not recorded |
| Platform trade counter, Depot A | 4 on 10 Sep, 12 on 19 Sep, 14 on 24 Sep; later counts not recorded |
| Best trade | FG6GK5, Brent call, 7–10 Sep: +€60,990.89 (+305.1 %) |
| Worst trade | FG6MRT, Brent call, knocked out 16 Sep: −€19,764.10 |
| Knock-outs | 3, all in the first ten days: FC8QQU (B, 8 Sep), FG6PCD (B, 11 Sep), FG6MRT (A, 16 Sep), at 1.5–2.5 % distance to barrier on entry |
| Resets | 1 (Depot B, 8 Sep) |
| Sum of net P/L, Depot A trades 1–10 | +€132,468.49, against a recorded cash gain of +€132,469.59 by 26 Oct (the gap comes from the approximate figures in trades 4 and 5) |
| Depot A, 7–16 Sep | €100,000 → €141,455.09 (+41.5 %) |
| Depot A, 17 Sep–26 Oct | €141,455.09 → €232,469.59 (+64.3 %, last recorded state) |
| Depot B | −18.15 % from the €100,000 reset, idle from 15 Sep |
| Weekly ranks | not recorded |

Depot A's recorded cash states: €161,223.09 (10 Sep), €141,455.09 (16 Sep), €161,700.09
(19 Sep), €179,361.99 (24 Sep), €206,217.79 (5 Oct), €217,539.59 (9 Oct), €225,718.19 (14 Oct),
€232,469.59 (26 Oct).

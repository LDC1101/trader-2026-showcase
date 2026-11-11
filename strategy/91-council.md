# The Council: checking every item before it is passed on (7 Sep 2026)

Task (the player): before a piece of information reaches them, several agents, each
specialised in its own field, should read it independently, cross-check it, discuss it
with each other, and only then pass on their joint verdict or a reasoned weighing of the
views.

## Structure (`src/council.py`)

Five members, each with its own field, its own question and its own sources (only tiers
1–2 from `src/sources.py`):

| Member | Checks | Sources |
|---|---|---|
| Maritime | Is the incident or status change documented? Advisory number, ship, position, time; new or rehashed? | UKMTO, straits.live, gCaptain, TankerTrackers, Lloyd's List, CENTCOM, gov.uk |
| Diplomacy | Official statement or a named official? Signed and implemented? What does the other side say? | State, DoD/CENTCOM, FCDO, Oman FM, Reuters, AP, Bloomberg |
| Oil market | Do Brent and Polymarket react in the direction of the report, and by how much? Which comparison case from `71-event-moves.md`? | Reuters, Bloomberg, WSJ, CNBC, FT, EIA, CFTC, Polymarket, ICE |
| Fact-checker | Tries to refute: original source, wording, timestamp, duplicate, translation; tier of every source | Reuters, AP, UKMTO, straits.live, State, gov.uk |
| Depot | What it means for A and B, whether an abort condition applies, which rule-compliant action in which order | SG, ICE, repo |

Each member runs as its own `claude -p` (Sonnet) with Read, Grep, WebSearch and WebFetch.
No browser (the Playwright profile belongs to the hourly browser round), no orders, no
depot access. Each answers in JSON: confirmed yes/no/unclear, signal, direction, evidence
with source and tier, abort, action, reasoning, reply to the others.

## Procedure

1. **Round 1:** all five in parallel, independently of each other.
2. **Unanimity** means the same class for ABORT (no/YES) and ACTION
   (none/check/buy/close). Then the Council stops.
3. **Otherwise rounds 2 and 3:** each member sees the others' verdicts and replies
   concretely in the "reply" field: which evidence the other member overlooked, or which it
   overlooked itself. A verdict changes only if evidence convinces. No agreement without
   evidence.
4. **After three rounds without unanimity:** a split verdict (`SPLIT` in the message). The headline takes the more
   cautious class (none before check before buy/close; "no" for abort if one member says
   no), and the dissent appears in the message with names and reasons.

## Evidence and gate

- The result counts as **evidenced** only if its evidence includes a tier 1 source or
  two different tier 2 sources. The tier comes from the register, not from the agent's own
  rating.
- The Watch and the browser round let "buy/close" through only if the item itself passes
  the gate (`sources.may_trigger`) **or** the Council result is evidenced. Otherwise
  "WATCH".
- If the Council fails (timeout, no JSON), the simple assessment steps in and may trigger
  at most "check".

## What reaches the player

Only the result: the five lines SIGNAL/WHAT/DEPOTS/ABORT/ACTION, then one line per member
with verdict and evidence, and if they disagree, the line DISSENT. It is sent under the
existing rule: signal medium or higher, or a named action; otherwise it stays in the log
`data/council.log`.

## Cost and duration

Five agents in parallel, each up to 4 minutes; one round takes about 2–4 minutes, three
rounds up to 12. Hence the lock in `watch.py`: one run at a time, and launchd starts
during a Council session are skipped and logged.

## Probe

`python3 src/council.py --probe "[IRNA English|S3] Iran says Strait of Hormuz fully reopened…" --rounds 2`
The result is in the log below.

## Probe log, 7 Sep 11:41–11:46

Translated output. The WHAT, DEPOTS and DISSENT fields are cut at a fixed length by the
script, which is why they end mid-sentence.

```
SIGNAL: weak neutral Brent (council of 5 members, 2 round(s), SPLIT, evidence S1/2xS2 yes)
WHAT: Own search for Reuters/AP reports of an Iran-US agreement on 7 Sep 2026 returns not a single hit, and straits.live (primary source, timestamp two hours before the reports) contradicts the IRNA claim explicitly and with numbers. The IRNA report names a signin
DEPOTS: If the report were confirmed, row 1 of the abort table would apply literally (close Depot A (long, call) immediately, let Depot B (short, put) run), but Depot A has no automatic mechanism for that: the only resting order is the take-profit limit sell at Brent ~173 USD, which
ABORT: no (S1/2xS2)
ACTION: none
EVIDENCED: yes
COUNCIL:
- Maritime: no, weak neutral, abort no, none | straits.live S1; ukmto.org/recent-incidents S1
- Diplomacy: no, weak neutral, abort no, check | Bloomberg S2; fm.gov.om S1; state.gov S1
- Oil market: no, weak neutral, abort no, none | bloomberg.com S2; polymarket.com S1
- Fact-checker: no, weak neutral, abort no, none | straits.live S1
- Depot: no, weak neutral, abort no, check | IRNA English S3; depot/positions.md S4
DISSENT: Maritime: none, I cannot add to the S2 sources you cited (Bloomberg Iran-Oman corridor), but I cover the same gap from / Diplomacy: check, Adding one concrete piece of evidence from today for Oil market and Depot: Bloomberg (S2, 7 Sep 2026, 'Iran Says Strait of Hormuz Deal / Oil market: none, Adding the market side for Maritime/Diplomacy/Fact-checker/Depot: Polymarket (S1) gives the reopening claim only 0.5% (15 / Fact-checker: none, I am not overlooking any deviating verdict: all four Council members (Maritime, Diplomacy, Oil market, Depot) independently ar / Depot: check, I agree with Maritime/Diplomacy/Oil market/Fact-checker: no S1 and no two S2 present, IRNA (S3) is contradicted by the only
```

Two rounds, four minutes. All five: not confirmed, abort no. straits.live (S1) and the
absence of agency reports refute the IRNA line; Polymarket gives the opening 0.5%. Round 2
arose only from "none" against "check"; since then both count as non-action and as
unanimous. Fixed afterwards: "evidenced" counts only evidence from members who confirm the
item; an S1 source against the item does not make it evidenced.

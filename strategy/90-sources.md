# Source review and gate, 7 Sep 2026

Task (the player): check whether the sources that feed into assessments and
recommendations are reputable and reliable, and build a gate that keeps one-sided or
opinion-based sources away from action recommendations.

## Where sources lead to an action

| Path | Reads | Triggers |
|---|---|---|
| `situation.py` → `watch.py` every 15 min | RSS: State, DoD, FCDO, MoD, IRNA, WSJ, CNBC, gCaptain, Fed | headline → assessment (`claude -p`) → Telegram "ALERT: ACT" on buy/close |
| `browser_round.py` hourly | X search, @UK_MTO, @TankerTrackers, @gCaptain, @IrnaEnglish, @FMofOman, @CENTCOM, @JavierBlas, UKMTO list, r/geopolitics | the same assessment |
| `reply_bot.py` | WebSearch/WebFetch, unrestricted | reply to the player |
| Sessions (this repo) | WebSearch/WebFetch | recommendation to the player |

Until today only `00-thesis.md` distinguished between "noticing" and "triggering"; the
scripts passed every source to the assessment unmarked, and `reply_bot.py` could search
anywhere.

## Review of the sources

Tier 1 = primary, may trigger on its own. Tier 2 = news agency or trade press: two of them,
or one quoting a tier 1 source. Tier 3 = party or state media, proves only its own
statement. Tier 4 = opinion, social media or aggregator: a reason to look, not evidence.
The short labels S1–S4 stand for source tiers 1–4. Register with the reasoning for each
source: `src/sources.py`.

| Source | Tier | Finding |
|---|---|---|
| UKMTO, @UK_MTO | 1 | Royal Navy office, "verified and corroborated" incident reports for 25 years; primary source according to the thesis |
| US State / DoD / @CENTCOM | 1 for their own actions, 3 about the adversary | the CENTCOM statement on three tankers (5 Sep) is primary; claims about Iranian losses are party claims |
| UK FCDO / MoD | 1 | government feeds |
| @FMofOman | 1 | mediator; primary for the state of the talks |
| Fed, CFTC, EIA, ICE, SEC, BaFin, SG | 1 | official data, not reports |
| straits.live | 1 | unfunded, no advertising; every number linked to a primary feed (IMF PortWatch, EIA, AIS, OFAC), method published, JSON endpoint; a status change counts as a trigger according to the thesis |
| Polymarket | 1 (price) | measures expectation, not facts; early indicator according to the thesis |
| Reuters, AP | 2 | MBFC: least biased, very high factual; Ad Fontes: highly reliable |
| Bloomberg, WSJ, FT, CNBC | 2 | news sections rated very high/high accuracy; columns and "Opinion" are tier 4 |
| gCaptain, @gCaptain | 2 | maritime trade press with an editorial staff, quotes UKMTO/TankerTrackers; was hours ahead of the agencies on 5/6 Sep |
| @TankerTrackers | 2 | AIS + satellite, exposes AIS spoofing; private company, method verifiable |
| IRNA, @IrnaEnglish | 3 | Iranian state agency; primary only for statements of the Iranian government. Iran ranks 178 of 180 on the press freedom index |
| Mehr, Press TV, Tasnim | 3 | MBFC: Mehr "low credibility, poor sourcing, state propaganda"; Press TV "questionable, fake news" |
| Iran International | 3 | close to the opposition, i.e. the opposing party |
| X search | 4 | unfiltered; a reason to look |
| r/geopolitics | 4 | forum |
| @JavierBlas | 4 | Bloomberg columnist, knowledgeable, but opinion; look the numbers up |
| Yahoo Finance (RSS rssindex) | 4 | mixes AP/Reuters with Motley Fool, Benzinga and Zacks; the feed does not name the source. **Removed from `situation.py`.** Evidence: the run on 7 Sep at 8:35 delivered "[Yahoo Finance] Nvidia Barely Moved. These 2 AI Connectivity Stocks Jumped…" (Motley Fool) |
| Seeking Alpha, Motley Fool, Substack, goldesel, finanzen.net | 4 | contributions without consistent editorial selection or with a subscription interest; finanzen.net only with a dpa tag |

What went into recommendations today and where it stands in the register: ICE trading
calendar (S1), SG interface (S1), BaFin (S1), Persistent/Uber/VINCI press releases (a party
speaking for itself, S3, but primary for offer price and deadlines), CNBC on Paramount
(S2), straits.live (S1), Wikipedia on 2026 events (S2, only with an individual citation),
MBFC/Ad Fontes for this review itself (secondary sources with their own method; their
ratings of IRNA, Mehr and Press TV match the RSF press freedom index).

## The gate

`src/sources.py`:
- `tier(name_or_domain)`: unknown = 4.
- Every headline now carries its tier: `[CNBC|S2] …`, `[@IrnaEnglish|S3] …`.
- The assessment prompt receives the tier rule; an `ABORT` must name the tier.
- `may_trigger(items)`: true only with a tier 1 source or two different tier 2 sources.
  Our own measurements (knock-out, Brent jump, Polymarket, COT) are data and count as
  tier 1.
- If the assessment says "buy/close" but the gate says no, the item is downgraded to
  "WATCH" with a note that the source is not confirmed ("WATCH (source not yet
  confirmed)" in the Watch, "WATCH: source S3/S4, no action without S1 or two S2" in the
  browser round), and the downgrade is logged. This applies in the Watch and in
  the browser round.
- `reply_bot.py` now searches only with `allowed_domains` from `sources.py --domains`
  (tiers 1–2).
- `python3 src/sources.py --check` reports every source in the feeds or accounts that is
  not in the register.

Probe 7 Sep 11:20: "[IRNA English|S3] Iran says Strait of Hormuz fully reopened, agreement
with US signed in Muscat" → SIGNAL weak, ABORT no (S3), ACTION check. Before the gate the
same line could have triggered "agreement reported" and with it "close Depot A".

## What the gate cannot do

It checks origin, not content. A Reuters report quoting an anonymous official is tier 2
and still unconfirmed; that is why it takes two tier 2 sources or one tier 1. And it only
knows what is in the register: new feeds or accounts go into the register first, otherwise
they count as tier 4.

Sources for this review: [MBFC Mehr](https://mediabiasfactcheck.com/mehr-news-agency/),
[MBFC Press TV](https://mediabiasfactcheck.com/press-tv/), [MBFC Reuters](https://mediabiasfactcheck.com/reuters/),
[straits.live/about](https://straits.live/about), [UKMTO](https://www.ukmto.org/),
[gCaptain](https://gcaptain.com/), Yahoo feed run of `situation.py` on 7 Sep at 8:35.

# Themes and their triggers

*Research as of 5 Sep. The plan to put the two depots on opposite sides was dropped on 8 Sep in favour of directional bets (see 00-thesis.md); oil stayed the theme for the whole season, see season/README.md.*

Each theme comes with what would move it and the size of the move, not with a forecast of the
direction.

## How an underlying qualifies (pre-game criteria)

The one finding that held across all model versions: **volatility in the underlying helps in every
constellation.** A turbo on a quiet index was the worst choice in the whole grid; leverage is
useless when nothing moves. Volatility can be observed, direction cannot. Criteria, in this order:

1. **A dated event inside the game window:** earnings, a regulatory decision, a rate decision. A
   date guarantees a move without revealing its direction.
2. **High realised volatility:** weekly swings of 5% or more.
3. **A running trend.** In 2025 it was gold. Trends tend to last longer than they should, and a
   turbo on a running trend is the constellation behind the only documented million-euro result.
4. **SG issues turbos on it.** Only SG derivatives on EUWAX are tradable. This rules out a large
   share of the interesting candidates and belongs at the start of the check, not the end.

The 5 Sep analysis refined criterion 2: the quantity to look for is trend relative to noise, not
volatility on its own (`20-instruments.md`, "Distance to barrier").

## 1. Oil / Strait of Hormuz: the main theme

**Situation.** Closed since **day 188**. 6 instead of 85 ships per day (7% of normal), 363 ships
stuck, war-risk insurance at **40 times** the pre-crisis level (about $10M per supertanker). Crisis
index 91/100. Normally **25% of the world's seaborne crude** passes through the strait.

**Brent: $96.28**, +33.7% above the pre-crisis level, +9% in the past week, the strongest week since
mid-July. Cause: resumed US-Iran strikes; Iran reports a tanker hit at Kharg Island, the US hit
three Iranian tankers.

**Negotiations.** In August the US, Iran and Oman were "close" to a 60-day arrangement with separate
northern and southern shipping lanes and no fees. Nothing is signed. An agreement can be announced
on any day.

**Probabilities** (straits.live model, not market-implied, to be read as an order of magnitude):
reopening **<1% by 15 Sep**, **27% by 31 Dec**.

**Move sizes:**

| Scenario | Brent | Move from $96 |
|---|---|---|
| agreement, strait opens | $72–80 | **−17 to −25%** |
| status quo, attrition | $90–105 | ±10% |
| escalation (JPMorgan) | $120–130 | **+25 to +35%** |
| sustained total disruption | $150–200 | **+56 to +108%** |

**Why this theme and not Oracle:** Oracle moves ±11% on earnings. Oil can move 25–55% here. On a
leveraged product that is the difference between a 10-fold and a 50-fold gain. It also has exactly
the structure of the 2025 win: a commodity in a trend with daily news flow, not a single quarterly
report.

**Implementation:** both depots on opposite sides, **turbos** (no volatility premium, and oil
volatility is expensive), barrier **1–2%** away (leverage 50–100, reasoning in `20-instruments.md`,
"Distance to barrier").

**Triggers for immediate action:**

- a Hormuz agreement is reported → close the long depot, let the short run
- an attack on oil infrastructure (Kharg Island, Ras Tanura) → close the short
- an OPEC production increase → dampens the upside

## 2. AI energy: the replacement theme

Data centres used 448 TWh in 2025; more than **1,000 TWh** is expected by the end of 2026, Japan's
annual consumption. US data-centre demand 19 GW (2023) → 35 GW (2030). Uranium at about $86/lb,
supply 173M lb against demand of 204M lb.

Names: **CEG** (largest private nuclear operator, 55 GW, the largest US power producer after the
$16.4B Calpine acquisition), **OKLO**, **SMR**, **GEV**. Three Mile Island is contracted to Microsoft
with about 835 MW.

OKLO and SMR are small, extremely volatile stocks, suitable if oil fails as a theme. Before using
them, check whether SG issues turbos on them.

## 3. Semiconductors: a counter-position, not a core theme

Chip stocks have lost more than **$1 trillion** in market value. NVIDIA fell almost 10% in one day,
and the DOJ has issued an antitrust subpoena. At the same time NVIDIA bought **Hugging Face for
$12.93B on 3 Sep**, its second-largest acquisition after $20B for Groq assets, closing in the first
half of 2027.

NVIDIA made the largest AI acquisition of the year into sector weakness. As a theme of its own it is too unspecific; the sector is volatile, but the triggers are diffuse. It is
usable as a **counter-position** if both oil depots are knocked out and a new theme is needed.

## 4. Rates: the background, not a theme of its own

US inflation 3.4% headline, 2.5% core. The jobs report of 4 Sep showed 162,000 new jobs against an
expected 53,000–55,000. A rate hike on 16 Sep is priced at **~63%**, and the **VIX is still at
14.53**, close to its low for the year.

Market backdrop as of 4 Sep, researched, not forecast:

- S&P 500 at 7,708, about +16% for the year, close to its all-time high
- **VIX at 14.5, the 2026 low.** Its seasonal median rises toward 18 in mid-September and 19 in
  early October.
- DAX near its all-time high around 26,600
- September has been the weakest stock-market month since 1950 (−0.6% on average)
- in midterm-election years the average peak-to-trough decline is 18%; October of a midterm year is
  a typical upward turning point
- open risks: a new Fed chair, the Supreme Court ruling on tariffs, a possible government shutdown

The gap between the rate outlook and the VIX is the only market statement this file relies on, and
it concerns the **price** of optionality, not direction: stock and index convexity is cheap while
two rate decisions and the earnings season fall inside the game window, and seasonality points to
higher volatility. If the oil theme fails, index **warrants** are therefore the preferred
replacement.

## What is deliberately not here

No forecast of direction. For each theme the triggers and the size of the move are documented;
which side materialises is open. That is why the two depots cover both sides.

# Trader 2026: agent instructions

These are the working instructions every Claude session, cloud routine and helper agent read
before doing anything in this repo during the season. They are written so an agent with no
prior context can work from them. The season ended on 30 Oct 2026 and all automation was
paused on 11 Nov 2026; the instructions are kept as they applied during play, with paths
updated to this repo's layout.

## The hard limit first

**Rule 10 of the game bans automated trading systems.** A violation or a reasonable
suspicion leads to exclusion without a hearing, and winnings are forfeited. Therefore:

- No code in this repo gets access to the game account.
- You never place orders. You research, calculate and propose.
- The player executes every order by hand in the game's web interface.
- Stop-loss and limit orders are order types of the platform itself and explicitly allowed;
  they are not an automated system.

## What is being played

| | |
|---|---|
| Game | Trader 2026, Société Générale |
| Period | 7 Sep to 30 Oct 2026, 8 weeks, about 40 trading days |
| Players | about 30,000 expected (23,982 ranked at the end), two depots of €100,000 play money each |
| Main prize | highest **absolute** depot value on 30 Oct; the **better** of a player's two depots counts |
| Weekly prize | 8 × €2,222, by **percentage** gain in the week |
| Winning mark 2025 | **€1,350,000** (13.5×), second place €1,240,000 |

The 2025 winner used **three resets** and *one* BEST turbo on gold (+5,000 %) that they **sold
before the final week**. The others at the top held and lost in the correction.

## The rules that decide everything

Limits, all at the time of purchase, on the ask price:

- per security **in total** at most 20 % of depot value (cumulative over all purchases)
- all leveraged derivatives together at most 20 % of depot value
- **additionally at most €20,000 in leveraged derivatives, regardless of depot size**
- at most 20,000 units per leveraged derivative

A position that later grows beyond 20 % stays compliant. **That is the only mechanism by which
€20,000 can become a million.**

Also: 20 buy orders per depot and day, sells unlimited. 5-minute holding period after each
purchase. Trading 8:00–22:00 Stuttgart/EUWAX. SG products only. Fees €10 per stock order,
€3.90 per derivative order (the platform counts the fee against the €20,000 limit). Orders
valid 1 day or 7 days. **Reset:** once per week per depot back to €100,000, erasing all game
data. Cash counts fully toward the score.

Before every order, calculate:

```bash
python3 src/sizing.py <depot value> --ask <ask price> [--leveraged] \
        [--already <leveraged total>] [--already-position <this security>]
```

Read the rules reference (`strategy/11-rules-reference.md`, section 5) before every order
recommendation, not this summary.

## The thesis

Without a leveraged derivative, first place is not unlikely but **unreachable**: in 250,000
simulated game rounds it never happened, because the 20 % rule caps every stock position.
Details: `python3 src/tournament.py`.

Hence: put €20,000 (the rule maximum) into *one* leveraged product on an underlying with a
**dated or ongoing catalyst**, hold it, re-enter after a knock-out, and lock in gains only
above the winning mark.

Measured behavior rules (tables in `strategy/00-thesis.md`):

| Rule | Evidence |
|---|---|
| **Never** take profits | selling at 3× lowers P(≥ €1.35M) from 2.70 % to 0.029 %, a factor of 93 |
| Re-enter **immediately** after a knock-out | median 382k → 403k, P(> 500k) 36.9 % → 38.4 % |
| Depots in **opposite** directions | P(> 500k) 40 % → 56 %, median 80k → 571k |
| Lock in only above the winning mark | locking in at 250k → P(main prize) 0.00 % |
| Base in cash | volatility of the base irrelevant (2.728 % vs 2.852 %) |

From 17 Sep the player chose day bets with profit-taking instead (see `season/README.md`).
The agents kept stating the trade-off and then followed the player's decision.

## Choice of instrument

| Situation | Instrument | Why |
|---|---|---|
| Underlying with **high** implied volatility (oil) | **turbo** | pays linearly, contains no volatility premium |
| Underlying with **low** implied volatility (stocks, VIX 14.5) | **warrant** | convexity is cheap |
| Report or event **after** 22:00 Stuttgart | **warrant** | no knock-out barrier that a price gap can tear through |
| DAX turbo | **BEST or Classic**, never X-BEST/X-Classic | knocks out only 9:00–17:30 instead of 8:00–22:00; 2–9 % higher survival rate, at no cost (`python3 src/knockout_window.py`) |

## Notifications

Notifications go through Telegram only; email is never used. A private Telegram bot sends to
the player's chat. Token and chat ID live in `.env` in the repo root (never commit it; see
`.env.example`):

```bash
set -a; . ./.env; set +a
curl -sS -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
     --data-urlencode chat_id="$TELEGRAM_CHAT_ID" --data-urlencode text="..."
```

In a cloud routine there is no `.env`, and the trigger API does not accept environment
variables (server reply, 5 Sep 2026: "environment_variables is not supported on triggers").
Writing the token into the prompt would bypass exactly that restriction, because prompts are
persisted and replayed too. In routines the **repo commit** is the notification channel; write
the briefing so it is complete when read in the repo.

## Messages to the player

Feedback from 7 Sep 2026: messages were too long and the relevant part was cryptic. The player
reads on a phone and wants the assessment for the depots, not the context.

1. **Assessment for the depots first.** First sentence: what this means for Depot A and Depot
   B and what to do (hold, lock in, add, do nothing).
2. **Two or three sentences of reasoning** in plain language. Technical terms, WKNs and
   tickers only with a plain explanation next to them.
3. **Stop.** No log of what you checked, no source list, no derivation.

It must fit on a phone screen without scrolling. Everything else belongs in `season/` or the
data logs. Messages use the game platform's names "Depot 1" and "Depot 2", which the files call
Depot A and Depot B. Format details: `strategy/95-message-format.md`.

## The local jobs (ran on the player's Mac)

- `src/watch.py` every 15 minutes, 8:00–22:00 Berlin: messages **only on triggers**
  (Hormuz/Iran headline with an action word, Polymarket jump ≥ 5 points, Brent ±3 % since the
  last message, knock-out of a position from `depot/positions.md`, COT swing on Fridays).
  Messages carry "ALERT: ACT" when the assessment says buy or close, "WATCH" when it says
  check. Dry run: `python3 src/watch.py --test --ignore-quiet-hours`.
- `src/morning_card.py` Mon–Fri 8:05 and 9:05 (later also 14:05 and 15:05 for US stocks): the
  order card for every depot without a live position, or the day bet from `depot/bet.json`.
- `src/reply_bot.py`, always on: answers the player's Telegram questions with repo context.
- `src/daily_report.py`, from the Watch on weekdays at 21:00: value of both depots from cash in
  `depot/positions.md` plus units × SG bid, P/L and distance to barrier per position. SG stops
  quoting via its API at about 21:30, so bids are cached hourly in `data/sg_quotes.json`.
- `src/regime.py`, attached to the daily report: is Brent moving sideways (10-day efficiency
  < 0.25 with net move < 5 %) and are the gains on pace (+12 % per week, €300,000 by 12 Oct)?
  Reports on Fridays and on level changes.
- `src/browser_round.py`: hourly reading of X accounts, UKMTO and Reddit through a logged-in
  browser. **Retired on 22 Oct 2026**, see below.

launchd templates: `ops/launchd/`.

## The cloud environment

Measured 5 Sep 2026 in a dedicated test routine: the egress proxy blocks `curl` as such, not
individual hosts (five fetches, five times `CONNECT tunnel failed, response 403`).

- `src/situation.py` returns nothing there, for every feed.
- WebSearch and WebFetch are the only ways out; `WebFetch https://straits.live/` returns the
  Hormuz status.
- Telegram is unreachable from routines (`sendMessage` needs POST, WebFetch cannot do that).
- This is policy, not a bug. Do not try to route around it.

New routines created through the trigger API get the account's connectors attached
automatically. This project clears them right after creation and checks that
`mcp_connections` is empty. Routine prompts: `ops/routines/`.

## The browser, and where it must never go

**Retired since 22 Oct 2026, the player's decision** (security concerns about an agent reading
third-party sites in a logged-in browser). Research runs through WebSearch/WebFetch and the SG
product API via `curl`. Since then X accounts, Reddit and UKMTO's incident list are not read
directly; UKMTO reports come only through news agencies (tier 2).

What it was for: pages that load their data by JavaScript and stay empty for `curl` and
WebFetch. Measured 5 Sep 2026: the SG product finder returned a 15,801-byte SPA shell without a
single WKN or ask price, `x.com` 240,632 bytes without a single post, Reddit's JSON endpoint
answered non-browser clients with 403.

**Forbidden without exception:** the Société Générale game platform. No visit, no login, no
order, no depot balance, not even read-only. A browser that can operate the game page is what
Rule 10 means by "automated trading system", no matter who presses Enter. The depot state
comes from `depot/positions.md`, entered by the player.

## Source gate

Every source has a tier in `src/sources.py` (evidence in `strategy/90-sources.md`): 1 primary
(authority, UKMTO, a government about its own actions, market data), 2 agency or trade press,
3 party or state media (IRNA, Mehr, CENTCOM about the adversary), 4 opinion, social or
aggregator. **Action only with tier 1 or two tier-2 sources**; the Watch downgrades everything
else to "WATCH". For WebSearch: `allowed_domains` from `python3 src/sources.py --domains`.
Every factual claim in a recommendation carries its source and tier. New feeds go into the
register first, and `python3 src/sources.py --check` must pass.

## The Council: nothing reaches the player unchecked

`src/council.py`: five specialist agents (maritime, diplomacy, oil market, auditor, depot),
each with its own question and its own tier-1/2 sources, assess every news item independently,
then see each other's verdicts and respond, until ABORT and ACTION agree (at most three
rounds). Without agreement the more cautious class wins and the dissent goes into the message.
"Confirmed" only with tier 1 or two tier-2 sources. The Watch calls the Council before every
message; the simple rule-based assessment is only a fallback and may then trigger at most
"check". Details: `strategy/91-council.md`. Probe:
`python3 src/council.py --probe "[Source|T3] text" --rounds 2`.

## Your workflow

0. Before every order recommendation: read `strategy/11-rules-reference.md`.
1. Read `depot/positions.md`. That is the state. Without a current entry you can only answer in
   general terms; say so.
2. Read the latest files in `season/` for the history.
3. Research the situation: `python3 src/situation.py`, plus WebSearch for news since the last
   briefing.
4. Check against the abort conditions in `strategy/00-thesis.md`.
5. Write the briefing and commit.
6. Report only what the player needs to know today.

## Rules for yourself

- **Calculate instead of asserting.** Every number in this repo is measured or sourced. If you
  make a new claim, recompute it.
- **Check your own results for nonsense.** Early versions of the simulation produced a winning
  value of €24M and recommended infinite leverage. Both were model errors, not insights. If a
  result looks too good, it is a bug.
- **Status code 200 does not mean an endpoint exists.** The SG website returns the same SPA
  shell for every path.
- **No direction forecasts.** Historical data gives the *size* of a move, not its sign. Size is
  what the strategy needs.
- **Say what you do not know.** Never invent a number you have not checked.
- **Every buy recommendation carries the line "Winning chance: yes/no".** No means the
  instrument cannot reach the winning mark arithmetically (the underlying would have to rise
  more than 100 % or fall below 0). For Depot A a "no" is not a recommendation but "wait". On
  7 Sep a gold put was bought as a substitute and sold an hour later because the Brent call
  arrived at 9:30.

## Buy alert (from 16 Oct 2026)

On a pullback the player wanted a message "buy, WKN, limit, units" instead of a blind 7-day
limit order (which would also fill into a slide caused by a peace deal).

- Config `depot/buy_alert.json` (depot, WKN, barrier, trigger, stake, markup on the ask, valid
  until; example in `depot/examples/`). Deleting the file or backdating `valid_until` turns it
  off. It goes quiet by itself once `depot/positions.md` lists an open position for that depot.
- Ran in GitHub Actions every 15 minutes Mon–Fri (`ops/github-actions/buy-alert.yml`, script
  `src/buy_alert.py`), not in the local Watch, because the MacBook slept during the day.
  At most 3 messages per day, repeated after 2 h or when Brent is $0.75 lower.
- It stays a price alert with an order proposal. Nothing places orders.

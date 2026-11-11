# Messages to the player: format

Applies to every message the project sends: Telegram messages, Watch alerts, market updates,
briefings and the results of scheduled runs. Notifications go through Telegram only; email is never
used.

The format comes from the player's feedback on 7 Sep 2026: the messages were too long and the
relevant content was cryptic. The context of what happened is needed for the work, not for reading
the message. What the player wants is the assessment for their depots, written so that it is easy to
understand.

## Structure

1. **The depot assessment first.** First sentence: what this means for Depot A and Depot B and what
   to do (hold, secure, add, do nothing).
2. **Reasoning in two to three sentences**, in everyday language. Technical terms, WKNs, tickers and
   abbreviations only with a plain explanation next to them ("knock-out on Brent, barrier $68").
3. **Stop.** No log, no list of sources, no derivation, no Council rounds.

## Length

Fits on a phone screen without scrolling. Whatever does not fit belongs in the repo (`season/`,
`strategy/`, `depot/positions.md`), not in the message.

## What is left out

- what was checked, read or computed
- market events with no consequence for the depots
- intermediate steps, discussion of uncertainty, variants that are not recommended

## In the Watch

`src/watch.py` implements this in `for_player`: Telegram receives only the depot assessment, the
action and one sentence of reasoning. The long version with headlines and Council verdicts goes to
`data/watch_full.log`. Alerts are labelled "ALERT: ACT" when the assessment says buy or close,
and "WATCH" when it says check.

## Example

> Depot A: hold, change nothing. Depot B: do not add to the DAX knock-out today; after yesterday's
> slide the buffer to the barrier is too small. Next look tomorrow after the US inflation numbers at
> 14:30.

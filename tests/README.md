# Tests

Known answers for the parts that have to be right before an order is typed in. No network,
no `claude` call, no Telegram message: every test feeds fixed text or numbers into a pure
function. Position fixtures use the English number format of `depot/positions.md`
(`4,390.25`); the German format (`4.390,25`) must be rejected, not misread.

    python3 -m unittest discover -s tests -v

| File | Module | What it pins down |
|---|---|---|
| `test_situation.py` | `situation.py` | RSS/Atom parser (CDATA, title attributes, `updated`/`published`, HTML entities decoded, feed title is not an entry, limit); topic matching at word starts only; IRNA needs a second topic word |
| `test_state.py` | `situation.py` | state files: atomic round trip without a `.tmp` left behind, missing file gives the default, a corrupt file is moved aside as `.corrupt` |
| `test_sources.py` | `sources.py` | tiers by name, domain and URL; unknown sources are tier 4; the gate: one tier-1 source or two different tier-2 sources, never state media or social media alone; the Watch's own measurements count as tier 1, its reminders and order cards do not; every feed in `situation.py` is in the register |
| `test_council.py` | `council.py` | action and abort classes; when the Council counts as agreed (none and check are both passive); evidence only from members who confirm; a split Council reports the more cautious action and its dissent; the strategy-doc headings the prompts quote still exist |
| `test_message.py` | `watch.py` | the Telegram message: depot assessment first, then what to do and one sentence why, without council rounds, tiers or headline lists, under 900 characters; the Watch's own calls to action (knock-out, buy card, a replacement card that failed) stay in; the ACTION label itself is not read as an action; trigger words match whole words only; the fallback without the Council never sends ALERT: ACT; the headline memory drops the oldest entries; COT reads the Managed Money columns and ignores micro gold; futures highs and lows are mapped onto spot |
| `test_positions.py` | `watch.py` | the positions parser: empty template, filled table, sell orders are not positions, unreadable rows are logged rather than skipped, German number format is rejected, missing file |
| `test_sizing.py` | `sizing.py` | the rule calculator: 20 % of the depot and at most €20,000 for leveraged products, with the fee counted toward the volume (the platform rejected 4,040 × 4.95 on 7 Sep 2026), the 20,000-unit cap on cheap products, leverage already held, the cumulative 20 % for stocks without a unit cap, never a negative size, a zero ask or depot value is rejected |
| `test_sg_products.py` | `sg_products.py` | the underlying price is derived per futures contract (SG lists several months at once), largest contract first; too few products give no price |
| `test_morning_card.py` | `morning_card.py` | which depot value the card sizes from (depot value with a live position, cash without one, bold values, defaults when empty) and that the order size keeps the 20 % limit |
| `test_daily_report.py` | `daily_report.py` | number parsing, the positions reader, depot values, the SG quote cache (a zero bid falls back to the cache, yesterday's cache does not count), and the evening text (short, readable, close to barrier, knocked out, no position) |
| `test_regime.py` | `regime.py` | the sideways check: a trend is not sideways, a zigzag triggers, too little data; depot status and knock-out count; the assessment (calm, switch to weekly mode, three knock-outs, writing off the main prize, weekly result) in plain words and English number format |

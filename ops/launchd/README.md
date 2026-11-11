# launchd jobs (macOS)

During the season these jobs ran on the player's MacBook as per-user launch agents. All of
them were stopped and disabled on 11 Nov 2026.

| Label | Script | Schedule | Purpose |
|---|---|---|---|
| `de.trader2026.watch` | `src/watch.py` | every 15 min (the script itself only acts 8:00–22:00 Berlin) | news, price and knock-out triggers, Telegram on trigger only; hourly SG quote cache; daily report and regime check at 21:00 |
| `de.trader2026.morning` | `src/morning_card.py` | Mon–Fri 8:05, 9:05, 14:05, 15:05 | order card for every depot without a live position, or the day bet from `depot/bet.json` |
| `de.trader2026.reply` | `src/reply_bot.py` | always on (`KeepAlive`) | answers the player's Telegram questions with repo context via `claude -p` |
| `de.trader2026.browser-round` | `src/browser_round.py` | hourly | **retired 22 Oct 2026**, see the module docstring |

The `.plist` files are templates with three placeholders: `__REPO__` (absolute path of this
checkout), `__PYTHON__` (absolute path of a Python 3 interpreter) and `__PATH__` (a `PATH`
that contains the `claude` CLI, because launchd starts jobs with a minimal environment).

To run one again, fill the placeholders into a copy under `~/Library/LaunchAgents/` and load
it with `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/<label>.plist`. Stop it with
`launchctl bootout gui/$(id -u)/<label>`. Logs go to `data/<job>_launchd.log`; the scripts
write their own logs to `data/` as well.

Telegram needs `.env` in the repo root (see `.env.example`). Without it the scripts log the
message instead of sending it.

One lesson from the season: a MacBook that sleeps during the day misses scheduled runs (on
15 Oct no Watch run happened between 5:00 and 18:00 Berlin). The buy alert was moved to
GitHub Actions for that reason, see `ops/github-actions/`.

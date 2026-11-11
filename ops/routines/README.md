# Cloud routines

Three Claude Code routines (scheduled cloud agents) wrote the written record of the season.
Each run started a fresh cloud session with the repo checked out, read the strategy docs
and the positions file, researched the situation with WebSearch and WebFetch, wrote a
Markdown file into `season/`, and committed and pushed it. None of them had access to the
game account or placed orders (Rule 10); the player typed every order by hand.

| Routine | Prompt | Cron (UTC) | Berlin time | Output |
|---|---|---|---|---|
| Morning briefing | [morning-briefing.md](morning-briefing.md) | `12 6 * * 1-5` | Mon–Fri 08:12 CEST / 07:12 CET | `season/<YYYY-MM-DD>.md` |
| Evening check | [evening-check.md](evening-check.md) | `12 20 * * 1-5` | Mon–Fri 22:12 CEST / 21:12 CET | a `## Evening check` note in the day's briefing |
| Weekly review | [weekly-review.md](weekly-review.md) | `12 16 * * 0` | Sun 18:12 CEST / 17:12 CET | `season/weekly/<YYYY-MM-DD>.md` |

All three ran on `claude-opus-4-8` with the tools Bash, Read, Write, Edit, Glob, Grep,
WebSearch and WebFetch, no connectors and no persisted session. They were created on
5 Sep 2026, ran through the season (7 Sep to 30 Oct) and beyond, and were paused on
11 Nov 2026. Berlin moved from CEST to CET on 25 Oct; the schedules stayed in UTC, so the
local times moved one hour earlier.

The routines were the slow, written layer. The fast layer ran elsewhere: the Watch, the
morning card and the daily report ran on the player's laptop under launchd (`ops/launchd/`),
and the buy alert ran in GitHub Actions (`ops/github-actions/`). Those sent Telegram
messages through a private Telegram bot.

## Why the routines committed instead of messaging

Each prompt tells the routine to send a Telegram message if it can, and to fall back to the
repo commit otherwise. In practice the commit was the only channel.

- **The egress proxy blocks `curl` as such, not individual hosts.** Measured on 5 Sep 2026
  in a dedicated test routine: five fetches, five times
  `curl: (56) CONNECT tunnel failed, response 403`, and `%{http_code}` stayed `000`, including
  for `straits.live`, which had been assumed to be allowed. The agent proxy reported
  `connect_rejected (organization policy)` for every target host. None of the addresses was
  reached. (The ENVIRONMENT paragraph in each prompt names four blocked hosts; the
  measurement showed the block applies to every host.)
- **WebSearch and WebFetch are the only way out.** They are routed differently.
  `WebFetch` on `https://straits.live/` returns the Hormuz status.
- **Telegram is unreachable from a routine.** `sendMessage` needs a POST, which `WebFetch`
  cannot do, and `curl` does not get through.
- **Secrets cannot be passed in the routine either.** The trigger API rejected
  `environment_variables` under `job_config.ccr.session_context`, because trigger configs are
  persisted and replayed on every fire. Under `job_config.ccr` the same field was silently
  dropped: HTTP 200, and `environment_variables` stayed `{}`. Writing the bot token into the
  prompt would defeat the reason for that restriction, since prompts are persisted and
  replayed as well. Variables can be set on the cloud environment in the claude.ai web
  interface, but with no outbound path to Telegram nothing could have used them.
- **`src/situation.py` returns nothing in a routine**, for every feed, for the same reason.

All of this is policy, not a bug, and the prompts tell the routine not to work around it
through other hosts, ports or services. So each routine wrote its result into the repo,
complete enough to be read on its own, and the player read it there. The measurements were
recorded on 5 Sep 2026 in the cloud-environment section of the project's `CLAUDE.md`.

## Recreating a routine

1. Push this repo to a Git host that Claude Code's cloud environment can clone, and make
   sure the environment's Git access allows pushing to the branch the prompt pushes to
   (`origin`, default branch).
2. Keep a `CLAUDE.md` in the repo root. Every prompt starts by reading it; it holds the hard
   limits (Rule 10, no orders, no access to the game platform), the game rules, the message
   format and the working routine for any agent in the repo.
3. Create the routine from Claude Code, for example with the `/schedule` command, or from the
   routines page on claude.ai:
   - repository: `<your-repo-url>`
   - schedule: the cron expression from the prompt file (UTC)
   - model: the one in the prompt file's header, or a current equivalent
   - allowed tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
   - prompt: the fenced block from the prompt file, unchanged
4. **Clear the auto-attached connectors right after creating it.** When a routine is created
   through the API, the server attaches the account's connectors on its own, even if the
   request names none (measured 5 Sep 2026: calendar, email, drive and a remote-control
   connector). The routines need none of them, and an email connector must not be reachable.
   Update the new routine with `{"clear_mcp_connections": true}` (or remove the connectors in
   the web interface), then check that its `mcp_connections` is `[]`.
5. Run it once by hand and confirm that a new file appears in `season/` and that the commit
   reached the remote.
6. Optional Telegram delivery: only if your environment allows outbound POST requests. Set
   `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as variables of the cloud environment, never in
   the prompt or the routine config. Without that, the commit remains the channel and the
   prompts already handle it.
7. To pause a routine, disable it; to stop it for good, delete it.

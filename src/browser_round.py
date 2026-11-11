"""
Browser round: the Watch's second layer. RETIRED.

Retired on 22 Oct 2026 by the player's decision: an agent browsing third-party
sites with a logged-in browser was a security concern. The launchd job was
unloaded and disabled, and the Playwright MCP server was removed from the
project's MCP configuration. Research continued through WebSearch/WebFetch
and the SG API via curl only; X accounts, Reddit and UKMTO /recent-incidents
were no longer read directly, so UKMTO reports came in only through the wires
(tier 2). The code stays as a reference implementation. main() exits at once
unless --i-know-it-is-retired is passed.

What it did: once an hour, `claude -p` with the Playwright MCP tools read X,
UKMTO and Reddit in a logged-in browser (sources that curl does not get) and
handed anything new to the Watch's assessment. Telegram only for a signal of
at least "medium" or when the assessment named an action; otherwise only the
log.

The reader may only navigate, read out, wait and close: no typing, no
clicking, no posting. No account access, no orders.

Running it needs a Playwright MCP server registered under the name
`playwright` (this repo registers none). The browser profile and its login
belong to that server's own configuration; nothing here points to a local
profile path. If another session holds the profile, the start fails; the run
is logged and retried an hour later.

Usage:    python3 src/browser_round.py --i-know-it-is-retired --test   # reads, does not send
          python3 src/browser_round.py --i-know-it-is-retired
"""

import argparse
import datetime as dt
import io
import json
import os
import subprocess
import sys
import zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data")
sys.path.insert(0, HERE)
from watch import (send_telegram, log, polymarket, PLACE_RE, ACTION_RE, load_state, CLAUDE,  # noqa: E402
                   consult_or_assess, wants_action, wants_check, short_date, PRICES)
from situation import quote_cnbc, load_json, write_json  # noqa: E402
import sources  # noqa: E402

TZ = zoneinfo.ZoneInfo("Europe/Berlin")
STATE = os.path.join(DATA, "browser_round_state.json")
TOOLS = "mcp__playwright__browser_navigate,mcp__playwright__browser_evaluate,mcp__playwright__browser_wait_for,mcp__playwright__browser_close"
ALWAYS_RELEVANT = ("UKMTO", "@UK_MTO", "@TankerTrackers")
RETIRED_ON = "2026-10-22"


def read_pages():
    prompt = io.open(os.path.join(HERE, "browser_round_prompt.txt"), encoding="utf-8").read()
    environment = dict(os.environ, PATH=os.path.dirname(CLAUDE) + ":" + os.environ.get("PATH", "/usr/bin:/bin"))
    r = subprocess.run([CLAUDE, "-p", "--model", "sonnet", "--allowedTools", TOOLS],
                       input=prompt, capture_output=True, text=True, timeout=420, cwd=REPO, env=environment)
    out = r.stdout
    i, j = out.find("{"), out.rfind("}")
    if r.returncode != 0 or i < 0:
        log(f"browser round: reader failed rc={r.returncode} {out[:120]!r} {r.stderr[:120]!r}")
        return None
    try:
        return json.loads(out[i:j + 1])
    except Exception as e:
        log(f"browser round: JSON unreadable {type(e).__name__}: {out[i:i+120]!r}")
        return None


def main():
    ap = argparse.ArgumentParser(description="Retired browser round (reference implementation).")
    ap.add_argument("--test", action="store_true", help="read, but do not send and do not save state")
    ap.add_argument("--ignore-quiet-hours", action="store_true", help="also run between 22:00 and 8:00")
    ap.add_argument("--i-know-it-is-retired", action="store_true",
                    help=f"run anyway; the browser round was retired on {RETIRED_ON}")
    a = ap.parse_args()
    if not a.i_know_it_is_retired:
        msg = (f"browser round: retired since {RETIRED_ON} (security concerns about an agent browsing "
               f"with a logged-in browser); not run. Pass --i-know-it-is-retired to run the reference implementation.")
        log(msg)
        print(msg, file=sys.stderr)
        return
    now = dt.datetime.now(TZ)
    if not a.ignore_quiet_hours and not (8 <= now.hour < 22):
        return
    st = load_json(STATE)
    first = not st
    seen = set(st.get("seen", []))
    d = read_pages()
    if not d:
        return
    new = {}
    for e in d.get("entries", []):
        key = e.get("url") or e.get("text", "")[:100]
        if not key or key in seen:
            continue
        seen.add(key)
        q, t = e.get("source", "?"), e.get("text", "")
        relevant = q.startswith(ALWAYS_RELEVANT) or bool(PLACE_RE.search(t) and ACTION_RE.search(t))
        if relevant and not first:
            new.setdefault(q, []).append(f"[{q}|S{sources.tier(q)}] {t}" + (f" ({e['url']})" if e.get("url") else ""))
    st["seen"] = sorted(seen)[-4000:]
    st["last_run"] = now.strftime("%Y-%m-%d %H:%M")
    if not a.test:
        write_json(STATE, st)
    log(f"browser round: {len(d.get('entries', []))} read, {sum(len(v) for v in new.values())} new and relevant, errors {d.get('errors') or 'none'}")
    if first:
        print(f"First run: {len(seen)} stored. Errors: {d.get('errors') or 'none'}")
        return
    if not new:
        if a.test:
            print("nothing new")
        return
    alerts = []
    for q in ("UKMTO",) + tuple(k for k in new if k != "UKMTO"):
        if q in new:
            alerts.append(q.upper() + "\n" + "\n".join("• " + m[:320] for m in new[q][:6]))
    prices = {}
    for name, sym in PRICES.items():
        k = quote_cnbc(sym)
        if k:
            prices[name] = k[1]
    before = load_state().get("brent_last_run")
    delta = f"{prices['Brent']/before-1:+.2%}" if (prices and before) else "?"
    result = consult_or_assess(alerts, prices, polymarket(), delta)
    text = f"BROWSER ROUND {short_date(now)}\n" + "\n\n".join(alerts)
    important = False
    if result:
        sig = result.splitlines()[0].lower()
        action_line = next((z for z in result.splitlines() if z.startswith("ACTION")), "")
        important = ("strong" in sig or "medium" in sig) or ("action: none" not in action_line.lower())
        act = wants_action(action_line, include_act=False)
        if act and not (sources.may_trigger(alerts) or "EVIDENCED: yes" in result):
            log(f"browser round gate: action on an S3/S4 source downgraded: {action_line[:80]!r}")
            text = "WATCH: source S3/S4, no action without S1 or two S2\n" + text
        elif act:
            text = "ALERT: ACT\n" + text
        elif wants_check(action_line):
            text = "WATCH\n" + text
        text += "\n\nASSESSMENT\n" + result
        try:
            os.makedirs(DATA, exist_ok=True)
            with io.open(os.path.join(DATA, "signals.md"), "a", encoding="utf-8") as f:
                f.write(f"| {now:%Y-%m-%d %H:%M} | {result.splitlines()[0].replace('SIGNAL:', '').strip()} | Brent {prices.get('Brent')} | browser round | {alerts[0].splitlines()[1][:90]} | Outcome 7d: |\n")
        except Exception:
            pass
    else:
        text += "\n\n(assessment failed)"
    if a.test:
        print(text); print("\n-> would send:", important)
    elif important:
        send_telegram(text)
    else:
        log("browser round: not sent (weak, no action): " + text.replace("\n", " | ")[:220])


if __name__ == "__main__":
    main()

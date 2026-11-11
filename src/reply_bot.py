"""
Reply bot: answers the player's questions in the Telegram chat with repo context.

Long polling on getUpdates, one `claude -p` call in the repo per message, the
answer goes back into the chat of a private Telegram bot. Only messages from
the configured chat ID count. Reading, searching and the analysis scripts are
allowed; no account access, no orders, nothing is changed or committed.

Runs under launchd with KeepAlive (template in ops/launchd/). Stop it with
  launchctl bootout gui/$(id -u)/<label>
"""

import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data")
sys.path.insert(0, HERE)
from watch import load_env, log, CLAUDE  # noqa: E402
from situation import load_json, write_json  # noqa: E402

STATE = os.path.join(DATA, "reply_state.json")


def api(token, method, **params):
    args = ["curl", "-sS", "-m", "70", f"https://api.telegram.org/bot{token}/{method}"]
    for k, v in params.items():
        args += ["--data-urlencode", f"{k}={v}"]
    r = subprocess.run(args, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def answer(question):
    try:
        pos = io.open(os.path.join(REPO, "depot", "positions.md"), encoding="utf-8").read()[:3000]
    except FileNotFoundError:
        pos = ""
    st = load_json(os.path.join(DATA, "watch_state.json"))
    state = (f"Brent at the last alert {st.get('brent_alerted')}, Hormuz P {st.get('pm_alerted')} %, COT {st.get('cot')}"
             if st else "?")
    prompt = f"""The player asks via Telegram. You do not place orders.
Answer in English, evidence-based, at most 10 short lines, fitting on a phone screen without scrolling. First sentence: what it means for Depot 1 and Depot 2 (Depot A and Depot B in the files) and what to do (hold, protect, add, do nothing). Then the reasoning in two or three plain sentences. Technical terms, WKNs, tickers and abbreviations only with plain words next to them. No introduction, no hedging, no protocol, no derivation, never invent a number.
First read strategy/70-hormuz-dossier.md (chronology, actors, precedents) and strategy/71-event-moves.md (what Brent did after comparable events); if needed strategy/00-thesis.md, strategy/60-research-2026-09-05.md, the newest briefing in season/, data/watch.log and data/signals.md. Always back a size estimate with the comparison case and its number. You may run python3 src/*.py (situation.py, sg_products.py, candidates.py) and use WebSearch/WebFetch when the question needs it. Source gate (src/sources.py, strategy/90-sources.md): WebSearch only with allowed_domains from `python3 src/sources.py --domains` (tiers 1 and 2); state media (IRNA, Mehr, Press TV) only evidence their own statements; X, Reddit, Seeking Alpha, Motley Fool, Substack and columns are not evidence. Name the source behind every factual claim, and say so in plain words when a claim rests only on state media or social media.

WATCH STATE: {state}
POSITIONS:
{pos}

QUESTION: {question}"""
    environment = dict(os.environ, PATH=os.path.dirname(CLAUDE) + ":" + os.environ.get("PATH", "/usr/bin:/bin"))
    for model in ("sonnet", "opus"):
        try:
            r = subprocess.run([CLAUDE, "-p", "--model", model,
                                "--allowedTools", "Read,Glob,Grep,WebSearch,WebFetch,Bash(python3 src/*)"],
                               input=prompt, capture_output=True, text=True, timeout=240, cwd=REPO, env=environment)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()[:3800]
            log(f"reply {model} rc={r.returncode} {r.stderr[:100]!r}")
        except Exception as e:
            log(f"reply {model}: {type(e).__name__}")
    return "No answer possible right now; see data/watch.log."


def main():
    e = load_env()
    token, chat = e.get("TELEGRAM_BOT_TOKEN"), e.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Telegram not configured (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID in .env)"); return
    offset = load_json(STATE).get("offset")
    if offset is None:
        # On the first start, skip everything old
        d = api(token, "getUpdates", timeout=0)
        ups = d.get("result", [])
        offset = (ups[-1]["update_id"] + 1) if ups else 0
    while True:
        d = api(token, "getUpdates", timeout=50, offset=offset)
        for u in d.get("result", []):
            offset = u["update_id"] + 1
            m = u.get("message") or {}
            if str(m.get("chat", {}).get("id")) != str(chat) or not m.get("text"):
                continue
            question = m["text"].strip()
            log(f"question: {question[:100]}")
            api(token, "sendChatAction", chat_id=chat, action="typing")
            api(token, "sendMessage", chat_id=chat, text=answer(question))
        write_json(STATE, {"offset": offset})
        if not d.get("ok"):
            time.sleep(10)


if __name__ == "__main__":
    main()

"""
The Council: five specialist agents check every alert before it reaches the player.

Each agent reads only its own sources (tiers 1-2 from src/sources.py), searches
for confirmation or refutation itself and returns a verdict as JSON. Then every
agent sees the other verdicts and replies to them, until all agree on ABORT and
ACTION, at most MAX_ROUNDS. Without agreement, the weighing goes to the player
together with the dissent.

No account access, no orders, no browser (the Playwright profile belonged to
the hourly browser round). Tools per agent: Read, Glob, Grep, WebSearch, WebFetch.

    python3 src/council.py --probe "[IRNA English|S3] Iran says strait reopened"
    python3 src/council.py --probe "..." --rounds 1
"""

import argparse
import concurrent.futures as cf
import datetime as dt
import io
import json
import os
import subprocess
import sys
import zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sources  # noqa: E402
from watch import CLAUDE, log, load_state, read_section  # noqa: E402

TZ = zoneinfo.ZoneInfo("Europe/Berlin")
MAX_ROUNDS = 3
MODEL = "sonnet"
TIMEOUT = 240
TOOLS = "Read,Glob,Grep,WebSearch,WebFetch"

ROLES = {
    "Maritime": dict(
        focus="shipping and incidents in the Strait of Hormuz, the Gulf and the Gulf of Oman",
        sources=["ukmto.org", "straits.live", "gcaptain.com", "tankertrackers.com", "lloydslist.com", "centcom.mil", "gov.uk"],
        question="Is the reported incident or status change backed by UKMTO, straits.live or the maritime trade press? UKMTO advisory number, ship name, position, time. Is the report new, or an older incident being recycled?",
    ),
    "Diplomacy": dict(
        focus="governments, negotiations, agreements, blockade, sanctions",
        sources=["state.gov", "war.gov", "defense.gov", "centcom.mil", "gov.uk", "fm.gov.om", "reuters.com", "apnews.com", "bloomberg.com"],
        question="Is there an official statement (US, UK, Oman, Iran) or a wire report naming an official? Signed AND implemented, or a declaration of intent? What does the other side say? State media (IRNA, Mehr) only evidence their own statement.",
    ),
    "Oil market": dict(
        focus="Brent, supply and demand, positioning, comparison cases",
        sources=["reuters.com", "bloomberg.com", "wsj.com", "cnbc.com", "ft.com", "eia.gov", "cftc.gov", "polymarket.com", "ice.com"],
        question="Does the market (Brent, Polymarket) react in the direction of the alert, and by how much? Which comparison case from strategy/71-event-moves.md fits, with its number? Is the move a supply loss/return (large) or an incident without a supply effect (small, back within 20 days)?",
    ),
    "Fact-checker": dict(
        focus="fact check and refutation: source, wording, timestamp, duplicates, translation errors, old reports",
        sources=["reuters.com", "apnews.com", "ukmto.org", "straits.live", "state.gov", "gov.uk"],
        question="Try to refute the alert. Who reported it first, when, in what words? Does the original source really say what the headline claims? Tier of every source you use, per src/sources.py. Is there an identical earlier report (duplicate)?",
    ),
    "Depot": dict(
        focus="positions, barriers, abort conditions, game rules, choice of instrument",
        sources=["sg-zertifikate.de", "ice.com"],
        question="If the alert is true, what does it mean for Depot A and B (depot/positions.md, barriers, distance)? Does an abort condition from strategy/00-thesis.md apply? Which action would be within the rules, and in which order (order book first, then the sale)? Take the live distance to the barrier into account: below 1 % distance, the market's reaction to the alert can knock the position out before an order goes through. Recommend nothing the thesis forbids (taking profits, a replacement without a chance to win). Write 'action' and 'reasoning' so that the player understands them on a phone without background knowledge: first sentence, what to do with Depot A and B; technical terms, WKNs and abbreviations only with plain words next to them; no evidence tiers, no source abbreviations.",
    ),
}

SCHEMA = '''{"role": "<role>", "confirmed": "yes|no|unclear", "signal": "strong|medium|weak", "direction": "long|short|neutral",
 "evidence": [{"source": "<name or domain>", "tier": 1, "what": "<one sentence, with date/time>", "url": "<URL or empty>"}],
 "abort": "no|YES: <condition>", "action": "none|check: <what>|buy: <what>|close: <depot>",
 "reasoning": "<two sentences>", "reply": "<round >= 2: what you are replying to in the others' verdicts, or empty>"}'''


def position_distances(prices):
    """Distance of every open position to its barrier, from the live price and positions.md."""
    try:
        from watch import open_positions
        lines = []
        for depot, wkn, name, direction, barrier in open_positions():
            k = (prices or {}).get(name)
            if not k:
                lines.append(f"- Depot {depot} {wkn} ({name} {direction}): barrier {barrier:.2f}, price unknown")
                continue
            dist = (k / barrier - 1) if direction == "long" else (barrier / k - 1)
            lines.append(f"- Depot {depot} {wkn} ({name} {direction}): price {k:.2f}, barrier {barrier:.2f}, distance {dist*100:+.2f} % "
                         f"({'BROKEN' if dist <= 0 else 'alive'}); knock-out if {name} goes {'below' if direction == 'long' else 'above'} {barrier:.2f}")
        return "\n".join(lines) or "no open position"
    except Exception as e:
        return f"could not be computed ({type(e).__name__})"


def context(prices, p_hormuz, brent_delta):
    pos = read_section("depot/positions.md", "## Open positions", "## Log", 2500)
    thesis = read_section("strategy/00-thesis.md", "## Abort conditions", "\n## ", 4000)
    dossier = read_section("strategy/70-hormuz-dossier.md", "## Summary", "## Chronology", 3000)
    moves = read_section("strategy/71-event-moves.md", None, None, 3500)
    try:
        cot = load_state().get("cot") or {}
        cot_txt = ", ".join(f"{k} Managed Money net {v['net']:+,} ({v['date']})" for k, v in cot.items())
    except Exception:
        cot_txt = "?"
    return (
        f"PRICES: {', '.join(f'{k} {v:.2f}' for k, v in (prices or {}).items()) or '?'}\n"
        f"BRENT since the last look: {brent_delta}\n"
        f"POLYMARKET Hormuz normal by 31 Oct: {p_hormuz if p_hormuz is not None else '?'} %\n"
        f"COT: {cot_txt or '?'}\n\n"
        f"POSITIONS WITH LIVE DISTANCE TO THE BARRIER:\n{position_distances(prices)}\n\n"
        f"OPEN POSITIONS AND ORDERS (depot/positions.md):\n{pos}\n\n"
        f"ABORT CONDITIONS AND SOURCE RULE (strategy/00-thesis.md):\n{thesis}\n\n"
        f"MEMORY (strategy/70-hormuz-dossier.md):\n{dossier}\n\n"
        f"COMPARISON CASES (strategy/71-event-moves.md):\n{moves}\n"
    )


def prompt_for(role, alert, ctx, rnd, others):
    r = ROLES[role]
    discussion = ""
    if others:
        discussion = "\n\nVERDICTS OF THE OTHER COUNCIL MEMBERS (round " + str(rnd - 1) + "):\n" + \
            "\n".join(f"- {o['role']}: confirmed={o.get('confirmed')}, signal={o.get('signal')} {o.get('direction')}, abort={o.get('abort')}, action={o.get('action')}: {o.get('reasoning', '')[:300]}"
                      + (f" | Reply: {o.get('reply', '')[:200]}" if o.get('reply') else "")
                      for o in others if o.get("role") != role) + \
            "\n\nYou can see where the others judge differently. Reply to that concretely in the 'reply' field: which evidence they missed, or which you missed. Change your verdict only if evidence convinces you; otherwise explain why you stay. The goal is a shared ABORT and ACTION, but no agreement without evidence."
    return f"""You are the council member "{role}" in the Council of Trader 2026 (no orders, no account access, no browser). Your field: {r['focus']}.
Round {rnd} of at most {MAX_ROUNDS}. It is now {dt.datetime.now(TZ):%Y-%m-%d %H:%M} Berlin time.

YOUR TASK: {r['question']}

YOUR SOURCES for WebSearch (allowed_domains) and WebFetch: {', '.join(r['sources'])}. Other domains only if one of your sources points there; never use tier 3/4 (state media, X, Reddit, columns, aggregators) as evidence, at most as a labelled hint. Read files in the repo if needed (Read/Grep). At most 4 searches, then give your verdict.

{sources.rule_text()}

ALERT to be checked:
{alert}

CONTEXT:
{ctx}{discussion}

Answer ONLY with a JSON object following this schema, no introduction, no Markdown:
{SCHEMA}
Rules: 'confirmed' = yes only with S1 or two independent S2 in 'evidence'. 'abort' = YES only if an abort condition is met word for word AND confirmed. 'action' buy/close only with confirmed=yes. Rhetoric without an act is 'weak'. Never invent a number; what you have not checked is 'unclear'."""


def _json_from(text):
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        return json.loads(text[i:j + 1])
    except Exception:
        return None


def agent(role, alert, ctx, rnd, others):
    p = prompt_for(role, alert, ctx, rnd, others)
    environment = dict(os.environ, PATH=os.path.dirname(CLAUDE) + ":" + os.environ.get("PATH", "/usr/bin:/bin"))
    try:
        r = subprocess.run([CLAUDE, "-p", "--model", MODEL, "--allowedTools", TOOLS],
                           input=p, capture_output=True, text=True, timeout=TIMEOUT, cwd=REPO, env=environment)
        d = _json_from(r.stdout)
        if r.returncode != 0 or not d:
            log(f"council {role} R{rnd}: rc={r.returncode} unreadable {r.stdout[:100]!r} {r.stderr[:100]!r}")
            return dict(role=role, confirmed="unclear", signal="weak", direction="neutral", evidence=[],
                        abort="no", action="check: council member without an answer", reasoning="Agent returned no verdict.", error=True)
        d["role"] = role
        return d
    except Exception as e:
        log(f"council {role} R{rnd}: {type(e).__name__} {e}")
        return dict(role=role, confirmed="unclear", signal="weak", direction="neutral", evidence=[],
                    abort="no", action="check: council member without an answer", reasoning=f"{type(e).__name__}", error=True)


def _action_class(h):
    h = (h or "").strip().lower()
    for k in ("close", "buy", "check", "none"):
        if h.startswith(k):
            return k
    return "check"


def _abort_class(a):
    return "YES" if (a or "").strip().upper().startswith("YES") else "no"


def _consensus_class(h):
    """'none' and 'check' are both non-actions; the Council does not need to
    argue about them (probe of 7 Sep: a second round only because of none/check)."""
    k = _action_class(h)
    return "passive" if k in ("none", "check") else k


def agreed(verdicts):
    hs = {_consensus_class(v.get("action")) for v in verdicts}
    ab = {_abort_class(v.get("abort")) for v in verdicts}
    return len(hs) == 1 and len(ab) == 1


def evidenced(verdicts):
    """The alert counts as evidenced if members with confirmed=yes together name
    one S1 source or two different S2 sources (tier from the register)."""
    s1, s2 = set(), set()
    for v in verdicts:
        if str(v.get("confirmed", "")).lower() != "yes":
            continue   # evidence from a member who does NOT confirm the alert does not support it
        for b in v.get("evidence") or []:
            q = b.get("url") or b.get("source") or ""
            s = sources.tier(q)
            if s == 1:
                s1.add(q)
            elif s == 2:
                s2.add(sources.source_from_item(f"[{q}]") or q)
    return bool(s1) or len(s2) >= 2


def _majority(values):
    from collections import Counter
    c = Counter(values)
    return c.most_common(1)[0][0]


def summarize(verdicts, rounds, alert):
    hs = [_action_class(v.get("action")) for v in verdicts]
    aborts = [_abort_class(v.get("abort")) for v in verdicts]
    sig = [v.get("signal", "weak") for v in verdicts]
    dirs = [v.get("direction", "neutral") for v in verdicts]
    e = agreed(verdicts)
    # Consensus: without agreement, the more cautious class goes into the headline
    rank = {"none": 0, "check": 1, "buy": 2, "close": 2}
    h_head = _majority(hs) if e else min(hs, key=lambda x: rank[x])
    ab_head = "no" if (not e and "no" in aborts) else _majority(aborts)
    sig_rank = {"weak": 0, "medium": 1, "strong": 2}
    sig_head = min(sig, key=lambda x: sig_rank.get(x, 0)) if not e else _majority(sig)
    # Full action text: from the member whose class matches the headline (Depot preferred)
    h_txt = next((v.get("action") for v in verdicts if v["role"] == "Depot" and _action_class(v.get("action")) == h_head), None) \
        or next((v.get("action") for v in verdicts if _action_class(v.get("action")) == h_head), h_head)
    ab_txt = next((v.get("abort") for v in verdicts if _abort_class(v.get("abort")) == ab_head), ab_head)
    ev = evidenced(verdicts)
    what = next((v.get("reasoning") for v in verdicts if v["role"] == "Fact-checker"), "") or verdicts[0].get("reasoning", "")
    dep = next((v.get("reasoning") for v in verdicts if v["role"] == "Depot"), "")
    lines = [
        f"SIGNAL: {sig_head} {_majority(dirs)} Brent (council of {len(verdicts)} members, {rounds} round(s), {'agreed' if e else 'SPLIT'}, evidence {'S1/2xS2 yes' if ev else 'NOT sufficient'})",
        f"WHAT: {what[:300]}",
        f"DEPOTS: {dep[:300]}",
        f"ABORT: {ab_txt[:200]} ({'S1/2xS2' if ev else 'only S3/S4 or unconfirmed'})",
        f"ACTION: {h_txt[:300]}",
        f"EVIDENCED: {'yes' if ev else 'no'}",
        "COUNCIL:",
    ]
    for v in verdicts:
        b = "; ".join(f"{x.get('source', '?')} S{sources.tier(x.get('url') or x.get('source') or '')}" for x in (v.get("evidence") or [])[:3]) or "no evidence"
        lines.append(f"- {v['role']}: {v.get('confirmed', '?')}, {v.get('signal', '?')} {v.get('direction', '')}, abort {_abort_class(v.get('abort'))}, {_action_class(v.get('action'))} | {b}")
    if not e:
        lines.append("DISSENT: " + " / ".join(f"{v['role']}: {_action_class(v.get('action'))}, {v.get('reply', '')[:120] or v.get('reasoning', '')[:120]}" for v in verdicts))
    return "\n".join(lines)


def deliberate(alerts, prices=None, p_hormuz=None, brent_delta="?", max_rounds=MAX_ROUNDS, roles=None):
    """Convene the Council. Returns text in the assessment format (starts with SIGNAL)."""
    alert = "\n\n".join(str(m) for m in alerts)
    ctx = context(prices, p_hormuz, brent_delta)
    roles = roles or list(ROLES)
    verdicts, rnd = [], 0
    for rnd in range(1, max_rounds + 1):
        others = verdicts
        with cf.ThreadPoolExecutor(max_workers=len(roles)) as ex:
            new = list(ex.map(lambda r: agent(r, alert, ctx, rnd, others), roles))
        verdicts = new
        log(f"council R{rnd}: " + ", ".join(f"{v['role']}={_action_class(v.get('action'))}/{_abort_class(v.get('abort'))}" for v in verdicts))
        if agreed(verdicts):
            break
    text = summarize(verdicts, rnd, alert)
    try:
        data = os.path.join(REPO, "data")
        os.makedirs(data, exist_ok=True)
        with io.open(os.path.join(data, "council.log"), "a", encoding="utf-8") as f:
            f.write(f"\n### {dt.datetime.now(TZ):%Y-%m-%d %H:%M} rounds {rnd}\n{alert[:400]}\n{text}\n")
    except Exception:
        pass
    return text


def main():
    ap = argparse.ArgumentParser(description="Convene the Council on one alert and print its summary.")
    ap.add_argument("--probe", required=True, help="alert text, e.g. '[IRNA English|S3] ...'")
    ap.add_argument("--rounds", type=int, default=MAX_ROUNDS, help=f"maximum number of rounds (default {MAX_ROUNDS})")
    ap.add_argument("--roles", help="comma-separated list of roles, default all: " + ", ".join(ROLES))
    a = ap.parse_args()
    roles = [r.strip() for r in a.roles.split(",")] if a.roles else None
    print(deliberate([a.probe], max_rounds=a.rounds, roles=roles))


if __name__ == "__main__":
    main()

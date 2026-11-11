"""
Source register and gate. Every source that can deliver an alert has a tier.
The tier decides what an alert may do:

  1  Primary: speaks for itself (agency, government, UKMTO, exchange, market
     data). May trigger an abort condition on its own, for what the body
     itself does or reports.
  2  Wire / trade press with an editorial desk and a corrections practice
     (Reuters, AP, Bloomberg, WSJ news, CNBC, gCaptain, Lloyd's List,
     TankerTrackers). May trigger when two tier-2 sources report the same
     event, or when one tier-2 source quotes a tier-1 body.
  3  Party / state media (IRNA, Mehr, Press TV, Tasnim; also CENTCOM about the
     adversary). Only evidences what the party says about itself. Signal at
     most "weak", never the basis for an order.
  4  Opinion, aggregator, social (X search, Reddit, Seeking Alpha, Motley
     Fool, Substack, columns, the Yahoo feed). A reason to look, not evidence.
     Listed as "unconfirmed" in the assessment and triggers nothing.

Evidence for the tiers: strategy/90-sources.md (review of 7 Sep 2026).

    python3 src/sources.py --check      # all feeds/accounts against the register
    python3 src/sources.py --domains    # allowed domains (tiers 1 and 2)
    python3 src/sources.py cnbc.com     # tier of a source
"""

import re
import sys

# Key: the source name as it appears in alerts ("[CNBC] ...", "[@UK_MTO] ...").
# "domains" feed the WebSearch/WebFetch filter.
SOURCES = {
    # ---- Tier 1: primary ----------------------------------------------------
    "UKMTO":            dict(tier=1, kind="agency",     domains=["ukmto.org"],           reason="UK Maritime Trade Operations, Royal Navy; verified incident reports for 25 years"),
    "@UK_MTO":          dict(tier=1, kind="agency",     domains=[],                      reason="official X account of UKMTO"),
    "US State Dept":    dict(tier=1, kind="government", domains=["state.gov"],           reason="primary for US diplomacy; a party to the conflict, so only tier 3 about Iran"),
    "US DoD":           dict(tier=1, kind="government", domains=["war.gov", "defense.gov"], reason="primary for its own operations; tier 3 about the adversary"),
    "@CENTCOM":         dict(tier=1, kind="government", domains=["centcom.mil"],         reason="primary for its own strikes (5 Sep: three tankers); claims about the adversary tier 3"),
    "UK FCDO":          dict(tier=1, kind="government", domains=["gov.uk"],              reason="primary for the British position, travel advice, sanctions"),
    "UK MoD":           dict(tier=1, kind="government", domains=["gov.uk"],              reason="primary for Royal Navy deployments"),
    "@FMofOman":        dict(tier=1, kind="government", domains=["fm.gov.om"],           reason="mediator of the Iran-US talks; primary for the state of negotiations"),
    "Fed press releases": dict(tier=1, kind="agency",   domains=["federalreserve.gov"],  reason="rate decision verbatim"),
    "straits.live":     dict(tier=1, kind="data",       domains=["straits.live"],        reason="unfunded monitor, every number linked to a primary feed (IMF PortWatch, EIA, AIS, OFAC); per the thesis a status change counts as a trigger"),
    "Polymarket":       dict(tier=1, kind="market",     domains=["polymarket.com"],      reason="a price, not a report; measures expectation, not facts"),
    "CFTC COT":         dict(tier=1, kind="agency",     domains=["cftc.gov"],            reason="official positioning data"),
    "EIA":              dict(tier=1, kind="agency",     domains=["eia.gov"],             reason="official energy data"),
    "ICE":              dict(tier=1, kind="exchange",   domains=["ice.com"],             reason="trading calendar, contracts"),
    "SG":               dict(tier=1, kind="issuer",     domains=["sg-zertifikate.de"],   reason="the issuer's product data"),
    "BaFin":            dict(tier=1, kind="agency",     domains=["bafin.de"],            reason="offering documents"),
    "SEC":              dict(tier=1, kind="agency",     domains=["sec.gov"],             reason="mandatory filings"),
    # ---- Tier 2: wire / trade press -----------------------------------------
    "Reuters":          dict(tier=2, kind="wire",       domains=["reuters.com"],         reason="MBFC: least biased, very high factual"),
    "AP":               dict(tier=2, kind="wire",       domains=["apnews.com"],          reason="Ad Fontes: highly reliable, minimally biased"),
    "Bloomberg":        dict(tier=2, kind="wire",       domains=["bloomberg.com"],       reason="news section; columns (Blas, Opinion) are tier 4"),
    "dpa":              dict(tier=2, kind="wire",       domains=["dpa.com"],             reason="German news agency"),
    "AFP":              dict(tier=2, kind="wire",       domains=["afp.com"],             reason="news agency"),
    "WSJ Markets":      dict(tier=2, kind="press",      domains=["wsj.com", "dj.com"],   reason="news section very high accuracy; opinion section excluded"),
    "CNBC":             dict(tier=2, kind="press",      domains=["cnbc.com"],            reason="financial news with an editorial desk; labels market commentary"),
    "FT":               dict(tier=2, kind="press",      domains=["ft.com"],              reason="above-average factual accuracy"),
    "Handelsblatt":     dict(tier=2, kind="press",      domains=["handelsblatt.com"],    reason="business desk"),
    "gCaptain":         dict(tier=2, kind="trade press", domains=["gcaptain.com"],       reason="maritime trade press, quotes UKMTO/TankerTrackers, corrections practice"),
    "@gCaptain":        dict(tier=2, kind="trade press", domains=[],                     reason="the desk's X account"),
    "Lloyd's List":     dict(tier=2, kind="trade press", domains=["lloydslist.com"],     reason="shipping trade press"),
    "@TankerTrackers":  dict(tier=2, kind="analytics",  domains=["tankertrackers.com"],  reason="AIS plus satellite, exposes AIS spoofing; private but verifiable"),
    "Boersen-Zeitung":  dict(tier=2, kind="press",      domains=["boersen-zeitung.de"],  reason="business desk"),
    "onvista":          dict(tier=2, kind="press",      domains=["onvista.de"],          reason="game partner; rule texts and EQS announcements verbatim"),
    "Wikipedia":        dict(tier=2, kind="reference",  domains=["wikipedia.org"],       reason="only with an individual citation; for the chronology, never for a daily alert"),
    # ---- Tier 3: party / state media ----------------------------------------
    "IRNA English":     dict(tier=3, kind="state media", domains=["irna.ir"],            reason="Iranian state agency; primary only for statements of the Iranian government"),
    "@IrnaEnglish":     dict(tier=3, kind="state media", domains=[],                     reason="IRNA's X account"),
    "Mehr":             dict(tier=3, kind="state media", domains=["mehrnews.com"],       reason="MBFC: low credibility, poor sourcing, state propaganda"),
    "Press TV":         dict(tier=3, kind="state media", domains=["presstv.ir"],         reason="MBFC: questionable, fake news"),
    "Tasnim":           dict(tier=3, kind="state media", domains=["tasnimnews.com"],     reason="close to the IRGC"),
    "Tehran Times":     dict(tier=3, kind="state media", domains=["tehrantimes.com"],    reason="state-owned"),
    "Iran International": dict(tier=3, kind="exile media", domains=["iranintl.com"],     reason="close to the opposition, the other party; also only tier 3"),
    # ---- Tier 4: opinion / aggregator / social ------------------------------
    "X search":         dict(tier=4, kind="social",     domains=["x.com", "twitter.com"], reason="unfiltered; a reason to look, never evidence"),
    "r/geopolitics":    dict(tier=4, kind="social",     domains=["reddit.com"],          reason="forum"),
    "@JavierBlas":      dict(tier=4, kind="column",     domains=[],                      reason="Bloomberg columnist, well informed but opinion; look the numbers up"),
    "Yahoo Finance":    dict(tier=4, kind="aggregator", domains=["finance.yahoo.com"],   reason="mixes AP/Reuters with Motley Fool, Benzinga, Zacks; the source is not visible in the feed"),
    "Seeking Alpha":    dict(tier=4, kind="opinion",    domains=["seekingalpha.com"],    reason="contributions without consistent selection"),
    "Motley Fool":      dict(tier=4, kind="opinion",    domains=["fool.com"],            reason="advertising for subscription services"),
    "Substack":         dict(tier=4, kind="opinion",    domains=["substack.com"],        reason="individual authors"),
    "goldesel":         dict(tier=4, kind="opinion",    domains=["goldesel.de"],         reason="retail investor portal"),
    "finanzen.net":     dict(tier=4, kind="aggregator", domains=["finanzen.net"],        reason="mixes dpa with sponsored posts; only with an agency tag"),
}

TIERS = {1: "primary", 2: "wire/trade press", 3: "party/state media", 4: "opinion/social"}
UNKNOWN = 4   # anything not in the register counts as tier 4


def tier(source):
    """Tier for a source name or a domain/URL. Unknown = 4."""
    if not source:
        return UNKNOWN
    q = source.strip()
    m = re.fullmatch(r"(.+)\|S([1-4])", q)
    if m:
        q = m.group(1).strip()
    if q in SOURCES:
        return SOURCES[q]["tier"]
    ql = q.lower()
    for name, v in SOURCES.items():
        if name.lower() == ql:
            return v["tier"]
        for d in v["domains"]:
            if d in ql:
                return v["tier"]
    return UNKNOWN


def source_from_item(line):
    """'[CNBC] Title' -> 'CNBC'; '• [@UK_MTO] ...' -> '@UK_MTO'."""
    m = re.search(r"\[([^\]]+)\]", line)
    return m.group(1).strip() if m else ""


def tag(line):
    """Appends the tier to the source name: '[CNBC|S2] Title'."""
    q = source_from_item(line)
    if not q or "|S" in line:
        return line
    return line.replace(f"[{q}]", f"[{q}|S{tier(q)}]", 1)


def best_tier(alerts):
    """Lowest (= best) tier of all sources in a list of alert blocks."""
    best = 5
    for block in alerts:
        for line in str(block).splitlines():
            q = source_from_item(line)
            if q:
                best = min(best, tier(q))
    return best if best < 5 else None


MEASUREMENTS = ("KNOCK-OUT", "BRENT", "POLYMARKET", "COT")   # BRENT also covers BRENT FAST


def may_trigger(alerts):
    """Gate: an action (buy/close) only if a tier-1 source is present or at
    least two different tier-2 sources."""
    s1, s2 = set(), set()
    for block in alerts:
        lines = str(block).splitlines()
        if not any(source_from_item(z) for z in lines):
            # Blocks without a source tag are the Watch's own output. Only its
            # measurements are data and count as tier 1 (strategy/90-sources.md).
            # Reminders, order cards and untagged headlines are not evidence; before
            # 11 Nov 2026 the Monday "LIMIT ORDERS" reminder let any S3 headline pass.
            if lines and lines[0].startswith(MEASUREMENTS):
                s1.add(lines[0][:20])
            continue
        for line in lines:
            q = source_from_item(line)
            if not q:
                continue
            s = tier(q)
            if s == 1:
                s1.add(q)
            elif s == 2:
                s2.add(q)
    return bool(s1) or len(s2) >= 2


def allowed_domains(max_tier=2):
    out = []
    for v in SOURCES.values():
        if v["tier"] <= max_tier:
            out += v["domains"]
    return sorted(set(out))


def rule_text():
    """For the assessment prompt."""
    return (
        "SOURCE TIERS (shown after every source as |S1..S4): S1 primary (agency, UKMTO, a government about its own actions, market data): "
        "may trigger on its own. S2 wire/trade press: triggers when two S2 report the same event or an S1 is quoted. "
        "S3 party/state media (IRNA, Mehr, CENTCOM about the adversary): only evidences its own statement, signal at most weak. "
        "S4 opinion/social/aggregator (X search, Reddit, Yahoo feed, columns): not evidence, signal weak, ACTION at most 'check'. "
        "ABORT: YES only with S1 or two S2. Name the tier of the source in ABORT."
    )


def check():
    """All feeds and accounts used by the scripts against the register."""
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    missing = []
    try:
        from situation import FEEDS
        for name, url, _ in FEEDS:
            s = tier(name)
            print(f"  situation.py   {name:24} S{s}  {url[:60]}")
            if name not in SOURCES:
                missing.append(name)
    except Exception as e:
        print("situation.py:", type(e).__name__, e)
    try:
        txt = open(os.path.join(here, "browser_round_prompt.txt"), encoding="utf-8").read()
        accounts = sorted(set(re.findall(r"https://x\.com/([A-Za-z0-9_]+)", txt)) - {"search"})
        for k in accounts:
            name = "@" + k
            print(f"  browser_round  {name:24} S{tier(name)}")
            if name not in SOURCES:
                missing.append(name)
        for q in ("X search", "UKMTO", "r/geopolitics"):
            print(f"  browser_round  {q:24} S{tier(q)}")
    except Exception as e:
        print("browser_round_prompt.txt:", type(e).__name__, e)
    if missing:
        print("NOT IN THE REGISTER (count as S4):", ", ".join(missing))
        return 1
    print("all sources are in the register")
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Source register: tier of a source, register check, allowed search domains.")
    ap.add_argument("names", nargs="*", help="source names or domains to rate, e.g. Reuters irna.ir")
    ap.add_argument("--check", action="store_true", help="report sources in the feeds and accounts that are not in the register")
    ap.add_argument("--domains", action="store_true", help="print the tier 1-2 domains the reply bot may search")
    a = ap.parse_args()
    if a.check:
        sys.exit(check())
    if a.domains:
        print("\n".join(allowed_domains()))
        sys.exit(0)
    if not a.names:
        ap.print_help()
    for n in a.names:
        print(n, "-> tier", tier(n), TIERS.get(tier(n)))

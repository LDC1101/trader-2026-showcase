"""
Daily situation: news, prices and the Strait of Hormuz status in one place.

All sources are free and need no key; each was checked on 5 Sep 2026. If one
fails, the script keeps going and says so: a silent gap would be worse than a
reported one.

User-Agent: government servers expect a descriptive client name. The SEC's
fair-access policy also asks for a contact address in it and answers 403
without one. `RESEARCH_UA` is a generic placeholder; add your own contact to it
before querying sec.gov.

Cloud: in a cloud routine, outbound traffic goes through an egress proxy that
blocks yahoo, cnbc, dj.com and federalreserve.gov, so this script returns
nothing there. That is policy and cannot be worked around; use WebSearch and
WebFetch in the cloud instead, they are routed differently. So that a failed
run cannot destroy a good briefing, --write only writes when data actually came
in (see below).

Usage:    python3 src/situation.py
          python3 src/situation.py --write    (to season/<date>.md)
"""

import argparse
import datetime as dt
import html
import io
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

RESEARCH_UA = "trader2026-research/1.0"
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")

FEEDS = [
    # Government bodies first: per strategy/00-thesis.md only a primary source
    # may trigger an abort condition, and a government statement is one. Until
    # 6 Sep 2026, CENTCOM, IRNA and Oman came in only as X posts via the hourly
    # browser round. All five checked with curl on 6 Sep 2026 (200, 10-30
    # entries). The CENTCOM RSS returns an empty body, OPEC 403, IEA 404, the
    # Iranian foreign ministry a redirect loop; those stay out.
    ("US State Dept", "https://www.state.gov/rss-feed/press-releases/feed/", BROWSER_UA),
    # defense.gov redirects to war.gov with a 301; fetch() follows no
    # redirects, so war.gov directly.
    ("US DoD", "https://www.war.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10", BROWSER_UA),
    ("UK FCDO", "https://www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom", BROWSER_UA),
    ("UK MoD", "https://www.gov.uk/government/organisations/ministry-of-defence.atom", BROWSER_UA),
    ("IRNA English", "https://en.irna.ir/rss", BROWSER_UA),
    ("WSJ Markets", "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", BROWSER_UA),
    ("CNBC", "https://www.cnbc.com/id/100003114/device/rss/rss.html", BROWSER_UA),
    # Yahoo Finance (rssindex) removed on 7 Sep 2026: it mixes AP/Reuters with
    # Motley Fool, Benzinga and Zacks without a source tag in the feed, which is
    # tier 4 in the source register (src/sources.py). Evidence:
    # strategy/90-sources.md.
    ("Fed press releases", "https://www.federalreserve.gov/feeds/press_all.xml", RESEARCH_UA),
    # Maritime trade press: regularly reports Gulf incidents before the wires.
    # Checked on 5 Sep 2026: HTTP 200, 12 entries, no login. The actual primary
    # source, UKMTO, sits behind Cloudflare (403) and was reachable only through
    # a browser, not this way.
    ("gCaptain", "https://gcaptain.com/feed/", BROWSER_UA),
]

# Words relevant to our topics (see strategy/40-themes.md)
TOPICS = {
    "Oil/Hormuz": ["oil", "crude", "brent", "hormuz", "opec", "iran", "tanker",
                   "strait", "refinery", "wti",
                   # maritime terms, deliberately narrow so that gCaptain does
                   # not tip every container story into this topic
                   "ukmto", "kharg", "war risk", "convoy", "irgc"],
    "Rates/Fed": ["fed", "fomc", "inflation", "cpi", "rate", "powell", "yield",
                  "treasury", "jobs", "payroll"],
    "AI energy": ["nuclear", "uranium", "data center", "datacenter", "grid",
                  "electricity", "power demand"],
    "Semiconductors": ["chip", "semiconductor", "nvidia", "amd", "tsmc", "micron"],
}


def fetch(url, ua, timeout=20):
    """Through curl instead of urllib.

    Yahoo and a few other services answer urllib with 429 and curl with 200;
    they filter on the client's TLS fingerprint. curl exists on every system
    this repo runs on, including the cloud routine.
    """
    r = subprocess.run(
        ["curl", "-sS", "--compressed", "--max-time", str(timeout),
         "-A", ua, "-H", "Accept: */*", url],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"curl {r.returncode}: {r.stderr.strip()[:120]}")
    if not r.stdout:
        raise RuntimeError("empty response")
    return r.stdout


def load_json(path, default=None):
    """Read state. Missing file: `default` (else {}). A corrupt file (typical
    after a crash in the middle of a write) is moved aside as .corrupt and
    `default` is returned, so the next run does not fail at the same spot."""
    empty = {} if default is None else default
    try:
        with io.open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return empty
    except (json.JSONDecodeError, UnicodeDecodeError):
        try:
            os.replace(path, path + ".corrupt")
        except OSError:
            pass
        return empty


def write_json(path, obj, **kw):
    """Atomic: write .tmp first, then os.replace. A crash leaves either the old
    or the new file, never half of one."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, **kw)
    os.replace(tmp, path)


def _tier(name):
    try:
        import sources
        return sources.tier(name)
    except Exception:
        return "?"


def feed_entries(xml, limit=25):
    """Pull title and date out of RSS or Atom without an external library."""
    raw = re.findall(r"<(?:item|entry)\b.*?</(?:item|entry)>", xml, re.S)
    out = []
    for r in raw[:limit]:
        t = re.search(r"<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", r, re.S)
        d = re.search(r"<(?:pubDate|updated|published)>(.*?)</", r, re.S)
        if t:
            # CNBC titles arrive with entities such as &apos; inside CDATA
            title = html.unescape(re.sub(r"<[^>]+>", "", t.group(1))).strip()
            out.append((title, (d.group(1)[:16] if d else "")))
    return out


def classify(title, source=""):
    """Topics of a headline. Words count only at a word start: "rate" matches
    "rates" but not "strategic" or "commemorates"."""
    tl = title.lower()
    topics = []
    for topic, words in TOPICS.items():
        hits = [w for w in words if re.search(r"\b" + re.escape(w), tl)]
        # On the Iranian state feed "iran" is in almost every line and says
        # nothing; there a second word has to match as well.
        if source.startswith("IRNA"):
            hits = [w for w in hits if w != "iran"]
        if hits:
            topics.append(topic)
    return topics


def hormuz_status():
    """Status of the Strait of Hormuz, the main running catalyst."""
    try:
        html = fetch("https://straits.live/", BROWSER_UA)
    except Exception as e:
        return None, f"unreachable ({type(e).__name__})"
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    values = {}
    # Anchor on the context word. A free-standing decimal matches anything: an
    # earlier version read 26.56 instead of 96.28 and reported it as Brent.
    for name, pattern in [
        ("Days closed", r"Day\s+(\d{1,4})"),
        ("Brent", r"Brent[^0-9$]{0,40}\$?\s*(\d{2,3}\.\d{2})"),
        ("Vessels/day", r"(\d{1,3})\s+vessels?\s+transit"),
        ("Reopening by year end", r"Dec\s*31[^0-9]{0,40}(\d{1,3})\s*%"),
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            values[name] = m.group(1)
    return values, text[:400]


def quote_cnbc(symbol):
    """Fallback source. Yahoo rate-limits per IP and then answers 429."""
    try:
        html = fetch(f"https://www.cnbc.com/quotes/{symbol}", BROWSER_UA)
        # Allow thousands separators: "4,429.80" otherwise came out as 4.00
        m = re.search(r'"last":"?([\d,]+\.?\d*)"?', html)
        m2 = re.search(r'"change_pct":"?(-?[\d,]+\.?\d*)"?', html)
        if m:
            value = float(m.group(1).replace(",", ""))
            pct = float(m2.group(1).replace(",", "")) / 100 if m2 else 0.0
            return "CNBC", value, pct
    except Exception:
        pass
    return None


def quote(symbol):
    """Close and daily change from the Yahoo chart endpoint.

    stooq originally delivered CSV but now returns a JavaScript bot wall,
    hence Yahoo. No key needed.
    """
    try:
        raw = fetch(f"https://query1.finance.yahoo.com/v8/finance/chart/"
                    f"{symbol}?range=5d&interval=1d", BROWSER_UA)
        d = json.loads(raw)["chart"]["result"][0]
        closes = [x for x in d["indicators"]["quote"][0]["close"] if x]
        stamp = d["timestamp"][-1]
        date = dt.datetime.fromtimestamp(stamp).strftime("%Y-%m-%d")
        return date, closes[-1], closes[-1] / closes[-2] - 1
    except Exception as e:
        return ("ERROR", type(e).__name__, str(e)[:60])


def main():
    ap = argparse.ArgumentParser(description="Daily situation: prices, Hormuz status, news by topic.")
    ap.add_argument("--write", action="store_true",
                    help="write the result to season/<date>.md")
    a = ap.parse_args()

    lines = []
    counts = {"prices": 0, "hormuz": 0, "news": 0}

    def p(s=""):
        print(s)
        lines.append(s)

    today = dt.datetime.now()
    p(f"# Situation {today:%Y-%m-%d %H:%M}")
    p()

    # --- Prices ------------------------------------------------------------
    p("## Prices")
    p()
    # Gold as spot (XAU), not GC=F (the future); the Yahoo symbol was
    # unverified on 7 Sep because Yahoo did not answer.
    for name, sym, cnbc in [("Brent", "BZ=F", "@LCO.1"), ("WTI", "CL=F", "@CL.1"),
                            ("Gold", "XAUUSD=X", "XAU="),
                            # ("DAX", "%5EGDAXI", ".GDAXI"),  # disabled
                            ("S&P 500", "%5EGSPC", ".SPX"), ("VIX", "%5EVIX", ".VIX")]:
        k = quote(sym)
        if not k or k[0] == "ERROR":
            k = quote_cnbc(cnbc)
        if k and k[0] != "ERROR":
            date, close, change = k
            counts["prices"] += 1
            p(f"- **{name}** {close:,.2f} ({change:+.2%}, as of {date})")
        else:
            reason = f"{k[1]}: {k[2]}" if k else "unknown"
            p(f"- {name}: **no data** ({reason})")
    p()

    # --- Hormuz ------------------------------------------------------------
    p("## Strait of Hormuz")
    p()
    values, rest = hormuz_status()
    if values:
        counts["hormuz"] = len(values)
        for k, v in values.items():
            p(f"- {k}: {v}")
    else:
        # unreachable, or reachable without a recognised value: show the raw start
        p(f"- {rest}")
    p()
    p("Triggers per `strategy/40-themes.md`: report of an agreement → close the")
    p("long. Attack on oil infrastructure → close the short.")
    p()

    # --- News --------------------------------------------------------------
    p("## News by topic")
    p()
    by_topic = {t: [] for t in TOPICS}
    errors = []
    for name, url, ua in FEEDS:
        try:
            for title, date in feed_entries(fetch(url, ua)):
                for topic in classify(title, name):
                    by_topic[topic].append((name, title, date))
        except Exception as e:
            errors.append(f"{name}: {type(e).__name__}")
    counts["news"] = sum(len(v) for v in by_topic.values())

    for topic, hits in by_topic.items():
        p(f"### {topic} ({len(hits)})")
        if not hits:
            p("- nothing relevant")
        for source, title, date in hits[:10]:
            p(f"- [{source}|S{_tier(source)}] {title[:130]}")
        p()

    if errors:
        p("## Unreachable sources")
        p()
        for f in errors:
            p(f"- {f}")
        p()

    p("---")
    p("Next step: check against `strategy/00-thesis.md`. Does an abort condition")
    p("apply? Then check `depot/positions.md` and report.")

    if a.write:
        import pathlib
        target = pathlib.Path(REPO) / "season" / f"{today:%Y-%m-%d}.md"
        target.parent.mkdir(exist_ok=True)
        total = sum(counts.values())

        # A failed run must NOT overwrite a good briefing. That is exactly what
        # happened on the first cloud test run: the egress proxy blocked every
        # source, and the script replaced a briefing with real prices by one
        # full of "no data".
        if total == 0:
            print("\n[NOT written: not a single source returned data.")
            print(f" {target} stays unchanged. In a cloud routine this is")
            print(" the normal case; use WebSearch/WebFetch there.]")
        elif target.exists() and total < 3:
            partial = target.with_name(f"{today:%Y-%m-%d}-partial.md")
            partial.write_text("\n".join(lines) + "\n")
            print(f"\n[only {total} data points, written to {partial};")
            print(f" {target} is kept]")
        else:
            target.write_text("\n".join(lines) + "\n")
            print(f"\n[written to {target}, {total} data points]")


if __name__ == "__main__":
    main()

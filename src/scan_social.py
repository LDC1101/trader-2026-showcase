"""
Attention scanner for Reddit (with a placeholder for X/StockTwits).

PURPOSE. Not to derive price forecasts (that does not work, see
strategy/93-ai-trading-models.md), but to find underlyings that are MOVING
right now. The tournament maths in src/tournament.py: leverage achieves nothing
if the underlying does not move, and a seven-figure result needs a large move
within weeks. (The pre-game version said "volatility helps in every
constellation"; the current grid shows it hurts at very tight barriers.) Social attention is
a usable, early and cheap indicator of elevated volatility. It says nothing
about DIRECTION, and it is used here only in that sense.

The scanner was written for Reddit's public JSON without an API key. Reddit
closed anonymous access in 2023, so it now needs a free OAuth "script" app
(see token() below). X/Twitter requires paid access and is only provided as
a hook.

Usage:   python3 src/scan_social.py
         python3 src/scan_social.py --subs mauerstrassenwetten stocks
"""

import argparse
import base64
import collections
import json
import os
import re
import sys
import urllib.error
import urllib.request

HEADERS = {"User-Agent": "trader2026-research/1.0 (personal research)"}

# Reddit closed anonymous JSON access in 2023; without OAuth it answers 403.
# Create a free "script" app at reddit.com/prefs/apps and set
#   export REDDIT_CLIENT_ID=...
#   export REDDIT_CLIENT_SECRET=...
# Without these variables the script stops with a hint instead of silently
# returning empty lists.


def token():
    cid = os.environ.get("REDDIT_CLIENT_ID")
    secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not (cid and secret):
        return None
    auth = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=b"grant_type=client_credentials",
        headers={**HEADERS, "Authorization": f"Basic {auth}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())["access_token"]


SUBS = ["wallstreetbets", "mauerstrassenwetten", "stocks", "options"]

# Words that look like tickers but are not
STOPWORDS = {
    "THE", "AND", "FOR", "YOU", "ARE", "ALL", "NOT", "BUT", "CAN", "WILL",
    "USA", "CEO", "CFO", "IPO", "ETF", "FED", "CPI", "GDP", "ATH", "YOLO",
    "DD", "TA", "IMO", "EPS", "PE", "IV", "OTM", "ITM", "WSB", "EOD", "PM",
    "AH", "FD", "LOL", "EDIT", "TLDR", "USD", "EUR", "NEW", "ONE", "NOW",
    "GET", "GOT", "HAS", "HAD", "WAS", "SEE", "WHY", "HOW", "OUT", "OFF",
    "ITS", "DAX", "SEC", "IRS", "AI", "ER", "MOASS", "HODL", "BUY", "PUT",
}
TICKER_RE = re.compile(r"\$?\b([A-Z]{2,5})\b")


def fetch(sub, tok, sort="hot", limit=100):
    base = "https://oauth.reddit.com" if tok else "https://www.reddit.com"
    url = f"{base}/r/{sub}/{sort}.json?limit={limit}"
    headers = dict(HEADERS)
    if tok:
        headers["Authorization"] = f"bearer {tok}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def count_mentions(listing):
    mentions = collections.Counter()
    weight = collections.Counter()
    for child in listing.get("data", {}).get("children", []):
        d = child.get("data", {})
        text = f"{d.get('title', '')} {d.get('selftext', '')[:1500]}"
        score = max(int(d.get("score", 0)), 0)
        comments = max(int(d.get("num_comments", 0)), 0)
        seen = set()
        for m in TICKER_RE.findall(text):
            if m in STOPWORDS or len(m) < 2:
                continue
            if m in seen:
                continue
            seen.add(m)
            mentions[m] += 1
            # attention weighted by the post's reach
            weight[m] += score + 3 * comments
    return mentions, weight


def main():
    ap = argparse.ArgumentParser(description="Reddit attention scanner: which tickers are being talked about (a volatility signal, not a direction).")
    ap.add_argument("--subs", nargs="*", default=SUBS, help=f"subreddits to scan (default: {' '.join(SUBS)})")
    ap.add_argument("--top", type=int, default=25, help="number of symbols to list (default 25)")
    a = ap.parse_args()

    tok = token()
    if not tok:
        print("""
  No Reddit access configured.

  Since 2023 Reddit answers anonymous requests with HTTP 403. The scanner
  needs a free read-only access:

    1. reddit.com/prefs/apps -> "create app" -> type "script"
    2. export REDDIT_CLIENT_ID=<client id>
       export REDDIT_CLIENT_SECRET=<secret>
    3. python3 src/scan_social.py

  X/Twitter and StockTwits also block (403) and require paid access; neither
  is built in.
""")
        return

    total, total_weight = collections.Counter(), collections.Counter()
    per_sub = {}
    for sub in a.subs:
        try:
            listing = fetch(sub, tok)
        except urllib.error.HTTPError as e:
            print(f"  r/{sub}: HTTP {e.code}, skipped", file=sys.stderr)
            continue
        except Exception as e:
            print(f"  r/{sub}: {type(e).__name__}, skipped", file=sys.stderr)
            continue
        t, g = count_mentions(listing)
        per_sub[sub] = t
        total.update(t)
        total_weight.update(g)
        print(f"  r/{sub:<24} {sum(t.values()):>5} mentions, "
              f"{len(t):>4} distinct symbols")

    if not total:
        print("\n  No data. Reddit blocks anonymous queries at times;")
        print("  try again later or change --subs.")
        return

    print(f"\n  {'Symbol':<10}{'Mentions':>11}{'Reach':>12}{'Subs':>7}")
    for sym, n in total_weight.most_common(a.top):
        subs_with = sum(1 for t in per_sub.values() if sym in t)
        print(f"  {sym:<10}{total[sym]:>11}{n:>12,}{subs_with:>7}")

    print("""
  How to read this: the list is a candidate list for VOLATILITY, not a buy
  list. A symbol near the top means a lot is happening there right now, and
  the move can go either way.

  Next step: for the top candidates, check whether SG issues turbos on them
  at all (only SG products are tradable in the game) and whether a dated
  event is coming up (strategy/30-calendar.md).

  Mention counts can be manipulated and are being manipulated. Nothing here
  replaces a look at the chart and the event date.
""")


if __name__ == "__main__":
    main()

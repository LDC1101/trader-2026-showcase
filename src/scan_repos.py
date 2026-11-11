"""
Searches GitHub and Hugging Face for ready-made stock prediction models and
rates them by features that correlate with actually working.

The rating is deliberately sceptical. The three mistakes that sink practically
every public "stock predictor" repo are exactly the three measured in lessons
5, 7 and 9 of the sister repo ML-training-area:

  Leakage        The model sees information from the future during training.
                 Lesson 9: without a causal mask the training loss falls from
                 1.55 to 0.03, and the model then only produces line breaks.
                 A backtest with leakage ALWAYS looks good.
  Overfitting    Tuned on the validation period until the curve looks nice.
                 Lesson 5: the model selected for the best validation score
                 was WORSE on the larger test set.
  No baseline    No comparison with "buy and hold" or "random".
                 Lesson 7: an untrained benchmark produces an advantage of
                 4.9% that disappears under a fair budget.

A repo without a walk-forward test, without costs and without a baseline says
nothing about whether it makes money, however many stars it has.

Usage:   python3 src/scan_repos.py
         python3 src/scan_repos.py --deep        (reads READMEs, slower)
"""

import argparse
import base64
import json
import time
import urllib.parse
import urllib.request

HEADERS = {"User-Agent": "trader2026-research/1.0", "Accept": "application/vnd.github+json"}

GITHUB_QUERIES = [
    "stock price prediction deep learning",
    "algorithmic trading machine learning",
    "quantitative trading strategy backtest",
    "stock market forecasting transformer",
    "reinforcement learning trading agent",
]
HF_QUERIES = ["stock prediction", "financial time series", "trading"]

# Terms that speak for or against methodological care
GOOD = ["walk-forward", "walk forward", "out-of-sample", "out of sample",
        "purged", "combinatorial", "transaction cost", "slippage",
        "cross-validation", "benchmark", "baseline", "sharpe", "drawdown",
        "look-ahead", "lookahead", "survivorship"]
BAD = ["100% accuracy", "99% accuracy", "guaranteed", "get rich",
       "never loses", "holy grail", "profit every"]


def fetch_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


def github(query, n=10):
    q = urllib.parse.quote(query)
    url = (f"https://api.github.com/search/repositories?q={q}"
           f"&sort=stars&order=desc&per_page={n}")
    try:
        return fetch_json(url).get("items", [])
    except Exception as e:
        print(f"    GitHub '{query}': {type(e).__name__}")
        return []


def huggingface(query, n=10):
    q = urllib.parse.quote(query)
    url = f"https://huggingface.co/api/models?search={q}&limit={n}&sort=downloads"
    try:
        return fetch_json(url, {"User-Agent": HEADERS["User-Agent"]})
    except Exception as e:
        print(f"    HF '{query}': {type(e).__name__}")
        return []


def readme(full_name):
    url = f"https://api.github.com/repos/{full_name}/readme"
    try:
        d = fetch_json(url)
        return base64.b64decode(d.get("content", "")).decode("utf-8", "ignore")
    except Exception:
        return ""


def rate(text):
    t = text.lower()
    good = sorted({g for g in GOOD if g in t})
    bad = sorted({b for b in BAD if b in t})
    return good, bad


def main():
    ap = argparse.ArgumentParser(description="Search GitHub and Hugging Face for ready-made stock prediction models and rate them sceptically.")
    ap.add_argument("--deep", action="store_true", help="read and rate the READMEs (slower)")
    ap.add_argument("--top", type=int, default=12, help="number of repos to list (default 12)")
    a = ap.parse_args()

    print("=" * 78)
    print("GitHub / Hugging Face: search for ready-made prediction models")
    print("=" * 78 + "\n")

    seen, hits = set(), []
    for q in GITHUB_QUERIES:
        print(f"  GitHub: {q}")
        for r in github(q):
            if r["full_name"] in seen:
                continue
            seen.add(r["full_name"])
            hits.append(r)
        time.sleep(2)  # unauthenticated: 10 requests per minute

    hits.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
    print(f"\n  {len(hits)} distinct repos found. The largest:\n")
    print(f"  {'Repo':<44}{'Stars':>8}{'Last push':>14}")
    for r in hits[:a.top]:
        print(f"  {r['full_name'][:43]:<44}{r.get('stargazers_count', 0):>8,}"
              f"{r.get('pushed_at', '')[:10]:>14}")

    print("\n  Hugging Face:")
    hf = []
    for q in HF_QUERIES:
        hf.extend(huggingface(q))
    hf = {m["modelId"]: m for m in hf}.values()
    hf = sorted(hf, key=lambda m: m.get("downloads", 0), reverse=True)
    print(f"  {'Model':<52}{'Downloads':>12}")
    for m in list(hf)[:8]:
        print(f"  {m['modelId'][:51]:<52}{m.get('downloads', 0):>12,}")

    if a.deep:
        print("\n" + "=" * 78)
        print("Methodology check of the READMEs")
        print("=" * 78)
        print("\n  Looks for terms that point to clean testing")
        print("  (walk-forward, out-of-sample, transaction costs, baseline)")
        print("  and for warning signs (guaranteed returns).\n")
        with_terms, without = 0, 0
        for r in hits[:a.top]:
            good, bad = rate(readme(r["full_name"]))
            mark = "OK  " if good else "--  "
            if good:
                with_terms += 1
            else:
                without += 1
            print(f"  {mark}{r['full_name'][:40]:<42}"
                  f"{('good: ' + ', '.join(good[:3])) if good else 'no evidence'}")
            if bad:
                print(f"      WARNING: {', '.join(bad)}")
            time.sleep(1)
        print(f"""
  {with_terms} of {with_terms + without} of the largest repos mention even one of
  the methods without which a backtest says nothing. A mention is the lowest
  possible bar: it does not prove the work was done correctly, only that the
  term appears.
""")

    print("""
  Assessment for our purpose (details in strategy/93-ai-trading-models.md):

  No model of this kind will deliver a usable directional forecast within the
  game period. The reason is arithmetic, not scepticism. To show a hit rate of
  53% instead of 50% with statistical confidence (5% significance, 80% power)
  takes 2,178 trades. For 52% it takes 4,900. The game lasts eight weeks and
  leaves room for one to three dozen held positions. On a sample that small a
  real edge of three percentage points cannot be told apart from luck, even
  if it really exists.

  What these repos can still provide: code for fetching and preparing price
  data, volatility calculations, a backtest scaffold. They work as a toolbox,
  not as an oracle.
""")


if __name__ == "__main__":
    main()

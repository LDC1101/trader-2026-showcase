"""
SG product finder via the open interface of the issuer's website.

The site is a single-page app; the table comes from
  https://www.sg-zertifikate.de/EmcWebApi/api/ProductSearch/Search
with AssetId (underlying), ProductClassificationId (47 = BEST open end,
43 = Classic; 7145/7146 = X-BEST/X-Classic, which we do NOT want) and
CallPutRadio (0 = call, 1 = put). Checked on 5 Sep 2026, curl is enough.

The API does not return the current price of the underlying. It is derived
from the products themselves: for calls, bid = (S - strike) * ratio * FX,
a straight line in the strike with slope -ratio*FX and root S. A least-squares
line over all tradeable calls yields S and FX without an external price
source, and it does so for exactly the contract SG quotes against
(Oil Brent Future Nov 2026, not spot).

Filter per strategy/20-instruments.md: distance to barrier 0.5-3.5%,
ask above EUR 1.00 (otherwise the 20,000-unit cap binds), not sold out,
BEST or Classic.

Usage:    python3 src/sg_products.py                 # all candidates
          python3 src/sg_products.py --asset -4 415  # Brent and gold only
          python3 src/sg_products.py --write
"""

import argparse
import datetime as dt
import json
import os
import subprocess
import time

import numpy as np

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
BASE_URL = "https://www.sg-zertifikate.de/EmcWebApi/api/ProductSearch/Search"
CLASSES = {47: "BEST", 43: "Classic"}
# Below an ask of EUR 1.00 the 20,000-unit cap binds before the EUR 20,000 cap.
# At EUR 0.80 that means EUR 16,000, which is acceptable; below that it gets thin.
MIN_ASK = 0.60
# AssetId per /EmcWebApi/api/ProductSearch/Assets?productClassificationId=47 (5 Sep 2026)
ASSETS = {
    -4:   "Brent (Oil Brent Future)",
    -5:   "WTI (Oil WTI Light Crude Future)",
    415:  "Gold (XAUUSD)",
    423:  "Silver (XAGUSD)",
    320:  "NVIDIA",
    4772: "Constellation Energy",
    5294: "NuScale Power (SMR)",
    5072: "GE Vernova",
    389:  "DAX 40",
    315:  "Nasdaq-100",
}
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data")


def fetch_page(params, attempts=3):
    url = BASE_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    error = None
    for i in range(attempts):
        r = subprocess.run(["curl", "-sS", "-m", "40", "-A", UA, "-H", "Accept: application/json",
                            "-H", "Referer: https://www.sg-zertifikate.de/", url],
                           capture_output=True, text=True)
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError as e:
            # 7 Sep 2026 9:20: two empty responses in a row (rc 0, stdout ""),
            # back to normal minutes later. Wait briefly and retry.
            error = f"SG response unreadable ({len(r.stdout)} bytes, curl rc {r.returncode}): {e}"
            time.sleep(3 * (i + 1))
    raise RuntimeError(error)


def products(asset_id, product_class, callput):
    out, page = [], 0
    while True:
        d = fetch_page(dict(PageNum=page, PageSize=500, ProductClassificationId=product_class,
                            CallPutRadio=callput, AssetId=asset_id))
        out += d.get("Products", [])
        if len(out) >= d.get("TotalCount", 0) or not d.get("Products"):
            break
        page += 1
    return out


def implied_spot(calls, puts):
    """S and ratio*FX from the line bid = (S - K) * ratio*FX over tradeable calls;
    cross-check with puts. Uses the bid because the ask is 0 when 'sold out'."""
    def fit(px, sign):
        k = np.array([p.get("Strike") or 0 for p in px], float); g = np.array([p.get("Bid") or 0 for p in px], float)
        r = np.array([p.get("Ratio") or 0 for p in px], float)
        ok = (g > 0) & (r > 0) & (k > 0)
        if ok.sum() < 5:
            return None, None
        k, g, r = k[ok], g[ok] / r[ok], r[ok]      # per unit of ratio
        # Only close to the money: for calls the highest strikes, for puts the
        # lowest. Old products deep in the money have stale quotes and skew
        # the line (NVIDIA: 169 instead of 229 USD).
        order = np.argsort(k)[::-1] if sign > 0 else np.argsort(k)
        n_near = max(8, len(k) // 4)
        idx = order[:n_near]
        k, g = k[idx], g[idx]
        # g = fx * sign * (S - k)  ->  g = a + b*k,  b = -sign*fx,  S = -a/b
        A = np.vstack([np.ones_like(k), k]).T
        a, b = np.linalg.lstsq(A, g, rcond=None)[0]
        if b == 0:
            return None, None
        return -a / b, -sign * b
    s_c, fx_c = fit(calls, +1)
    s_p, fx_p = fit(puts, -1)
    return s_c, fx_c, s_p, fx_p


def spots_by_contract(calls, puts):
    """Implied underlying price per contract (AssetName), largest contract first.

    SG lists products on several futures months at once (11 Nov 2026: seven Brent
    contracts among the Classic turbos, calls and puts 24 % apart when fitted as one).
    A single line through all of them mixes prices several dollars apart, so every
    distance derived from it is wrong. Contracts with too few products are left out."""
    groups = {}
    for side, px in ((0, calls), (1, puts)):
        for p in px:
            groups.setdefault(p.get("AssetName"), ([], []))[side].append(p)
    out = {}
    for name, (c, pu) in sorted(groups.items(), key=lambda kv: -(len(kv[1][0]) + len(kv[1][1]))):
        s_c, fx_c, s_p, fx_p = implied_spot(c, pu)
        S = (s_c + s_p) / 2 if (s_c and s_p) else (s_c or s_p)
        if S:
            out[name] = dict(S=S, s_c=s_c, s_p=s_p, fx=fx_c or fx_p, calls=c, puts=pu)
    return out


def table(px, S, direction, lo, hi, n):
    rows = []
    seen = set()
    for p in px:
        if p.get("Code") in seen:
            continue
        seen.add(p.get("Code"))
        bar = p.get("BarrierTurboCertificate") or p.get("Strike")
        if not bar or not S:
            continue
        dist = (S - bar) / S if direction == "Call" else (bar - S) / S
        ask, bid = p.get("Offer") or 0, p.get("Bid") or 0
        if not (lo <= dist <= hi) or ask <= 0 or ask < MIN_ASK:
            continue
        spread = (ask - bid) / ask if ask else 1
        rows.append((dist, p.get("Code"), bar, p.get("CurrentLeverage") or 0, bid, ask, spread,
                     "Q" if p.get("IsQuanto") else "", p.get("Ratio") or 1, p.get("AssetName")))
    rows.sort()
    return rows[:n]


def main():
    ap = argparse.ArgumentParser(description="SG turbo finder (BEST and Classic)")
    ap.add_argument("--asset", type=int, nargs="*", help="AssetIds, default: all candidates")
    ap.add_argument("--min", type=float, default=0.005, help="minimum distance to barrier")
    ap.add_argument("--max", type=float, default=0.035, help="maximum distance to barrier")
    ap.add_argument("--n", type=int, default=8, help="rows per table")
    ap.add_argument("--write", action="store_true", help="also write the result to data/")
    args = ap.parse_args()
    ids = args.asset or list(ASSETS)
    out = []
    P = out.append
    P(f"# SG products, as of {dt.datetime.now():%Y-%m-%d %H:%M}, distance {args.min:.1%}-{args.max:.1%}, ask >= {MIN_ASK:.2f} EUR")
    P("")
    P("S = underlying price derived from the product prices (SG quote, possibly Friday's close). Distance = barrier to S.")
    P("")
    for aid in ids:
        name = ASSETS.get(aid, str(aid))
        for cl, clname in CLASSES.items():
            calls = products(aid, cl, 0)
            puts = products(aid, cl, 1)
            if not calls and not puts:
                P(f"## {name}, {clname}: no products"); P(""); continue
            spots = spots_by_contract(calls, puts)
            if not spots:
                P(f"## {name}, {clname}: {len(calls)} calls, {len(puts)} puts, too few tradeable products to derive the price")
                P(""); continue
            for contract, c in spots.items():
                S, s_c, s_p = c["S"], c["s_c"], c["s_p"]
                currency = (c["calls"] or c["puts"])[0].get("AssetCurrency", "")
                P(f"## {name}, {clname}, {contract}: {len(c['calls'])} calls, {len(c['puts'])} puts")
                P("")
                if s_c and s_p and abs(s_c - s_p) / S > 0.01:
                    P(f"**WARNING: call and put prices differ by {abs(s_c-s_p)/S:.1%}, distances uncertain, check against a live price.**")
                    P("")
                P(f"S implied from calls {s_c if s_c else float('nan'):.2f} {currency}, from puts {s_p if s_p else float('nan'):.2f}; "
                  f"FX*ratio {c['fx'] if c['fx'] else float('nan'):.4f}")
                P("")
                for direction, px in (("Call", c["calls"]), ("Put", c["puts"])):
                    rows = table(px, S, direction, args.min, args.max, args.n)
                    P(f"### {direction} ({'long' if direction=='Call' else 'short'})")
                    P("")
                    if not rows:
                        P("no products in the filter"); P(""); continue
                    P("| Distance | WKN | Barrier | Leverage | Bid | Ask | Spread | max. EUR (20k units) | Quanto | Ratio | Underlying |")
                    P("|---:|---|---:|---:|---:|---:|---:|---:|:-:|---:|---|")
                    for dist, wkn, bar, lev, bid, ask, spread, q, ratio, an in rows:
                        P(f"| {dist:.2%} | **{wkn}** | {bar:.2f} | {lev:.0f} | {bid:.2f} | {ask:.2f} | {spread:.1%} | {min(20000, 20000*ask):,.0f} | {q} | {ratio:g} | {an} |")
                    P("")
    text = "\n".join(out)
    print(text)
    if args.write:
        path = os.path.join(DATA, f"sg_products_{dt.date.today().isoformat()}.md")
        os.makedirs(DATA, exist_ok=True)
        with open(path, "w") as f:
            f.write(text + "\n")
        print(f"-> {path}")


if __name__ == "__main__":
    main()

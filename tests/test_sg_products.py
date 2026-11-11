import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from sg_products import spots_by_contract  # noqa: E402


def turbos(contract, spot, side, n=10):
    """Synthetic SG products on one contract: bid = (S - K) for calls, (K - S) for puts, ratio 1."""
    out = []
    for i in range(n):
        k = spot - 1 - i if side == "call" else spot + 1 + i
        bid = (spot - k) if side == "call" else (k - spot)
        out.append(dict(Code=f"{contract[:3]}{side[0]}{i}", Strike=k, Bid=bid, Ratio=1, AssetName=contract))
    return out


class Contracts(unittest.TestCase):
    def test_price_per_contract(self):
        # 11 Nov 2026: Classic Brent turbos on seven futures months; fitted as one line,
        # calls gave 94.70 and puts 74.45
        calls = turbos("Brent Jan 2027", 92.0, "call") + turbos("Brent Dec 2027", 80.0, "call", 6)
        puts = turbos("Brent Jan 2027", 92.0, "put") + turbos("Brent Dec 2027", 80.0, "put", 6)
        s = spots_by_contract(calls, puts)
        self.assertEqual(list(s), ["Brent Jan 2027", "Brent Dec 2027"])   # largest first
        self.assertAlmostEqual(s["Brent Jan 2027"]["S"], 92.0, places=6)
        self.assertAlmostEqual(s["Brent Dec 2027"]["S"], 80.0, places=6)

    def test_too_few_products(self):
        self.assertEqual(spots_by_contract(turbos("X", 50.0, "call", 3), []), {})


if __name__ == "__main__":
    unittest.main()

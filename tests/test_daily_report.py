import datetime as dt
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import daily_report as dr  # noqa: E402

TEXT = """# Positions
Date: 2026-09-07, 9:50
| | Depot A | Depot B |
|---|---|---|
| Depot value | 100,228.30 (9:50) | 101,237.78 (9:01) |
| Cash | 80,233.48 | 83,628.50 |
## Open positions
| Depot | WKN | Product | Underlying | Qty | Entry | Current | P/L % | Knock-out barrier |
|---|---|---|---|---|---|---|---|---|
| A | FG6GK5 | SG BEST Turbo Call, open end | Brent Nov 2026 | 14,489 | €1.38 (7 Sep 9:49) | 1.38 (9:50) | 0% | 95.86 USD |
| B | FC8QQU | SG BEST Turbo Put, open end | Brent Nov 2026 | 11,288 | €1.45 (7 Sep 9:01) | 1.56 (9:01) | +7.6% | 98.91 USD |
## Resting sell orders
"""
SG = {"FG6GK5": dict(bid=1.77, offer=2.04, hit=None), "FC8QQU": dict(bid=1.38, offer=1.15, hit=None)}
BASE = {"brent": dict(price=97.65, day=0.014)}
NOW = dt.datetime(2026, 9, 7, 21, 31)


class Numbers(unittest.TestCase):
    def test_number(self):
        self.assertEqual(dr.number("80,233.48"), 80233.48)
        self.assertEqual(dr.number("14,489"), 14489.0)
        self.assertEqual(dr.number("€1.38 (7 Sep 9:49)"), 1.38)
        self.assertEqual(dr.number("95.86 USD"), 95.86)
        self.assertEqual(dr.number("**232,469.59** (cash)"), 232469.59)
        self.assertIsNone(dr.number(""))


class Positions(unittest.TestCase):
    def test_read(self):
        d = dr.read_positions(TEXT)
        self.assertEqual(d["cash"], {"A": 80233.48, "B": 83628.50})
        self.assertEqual(d["date"], dt.date(2026, 9, 7))
        self.assertEqual(len(d["positions"]), 2)
        p = d["positions"][0]
        self.assertEqual((p["depot"], p["wkn"], p["units"], p["entry"], p["barrier"], p["direction"]),
                         ("A", "FG6GK5", 14489.0, 1.38, 95.86, "long"))


class Calculation(unittest.TestCase):
    def test_depot_values(self):
        dep = dr.compute(dr.read_positions(TEXT), SG, BASE)
        self.assertAlmostEqual(dep["A"]["value"], 80233.48 + 14489 * 1.77, places=2)
        self.assertAlmostEqual(dep["B"]["value"], 83628.50 + 11288 * 1.38, places=2)
        a = dep["A"]["positions"][0]
        self.assertAlmostEqual(a["distance"], 97.65 / 95.86 - 1, places=6)
        self.assertAlmostEqual(a["since_buy"], 1.77 / 1.38 - 1, places=6)

    def test_without_quote(self):
        dep = dr.compute(dr.read_positions(TEXT), {}, BASE)
        self.assertIsNone(dep["A"]["value"])


class Cache(unittest.TestCase):
    def setUp(self):
        self._path = dr.QUOTE_CACHE
        dr.QUOTE_CACHE = os.path.join(os.path.dirname(__file__), "_sg_quotes_test.json")
        if os.path.exists(dr.QUOTE_CACHE):
            os.remove(dr.QUOTE_CACHE)

    def tearDown(self):
        if os.path.exists(dr.QUOTE_CACHE):
            os.remove(dr.QUOTE_CACHE)
        dr.QUOTE_CACHE = self._path

    def test_zero_bid_falls_back_to_cache(self):
        held = {"FG6GK5"}
        live = {"FG6GK5": dict(bid=1.77, offer=2.04, time="17:03")}
        dr.with_cache(live, held, NOW.replace(hour=17, minute=3))
        evening = {"FG6GK5": dict(bid=None, offer=None, time=None)}
        q = dr.with_cache(evening, held, NOW)
        self.assertEqual(q["FG6GK5"]["bid"], 1.77)
        self.assertTrue(q["FG6GK5"]["from_cache"])
        self.assertEqual(q["FG6GK5"]["time"], "17:03")

    def test_yesterdays_cache_does_not_count(self):
        held = {"FG6GK5"}
        dr.with_cache({"FG6GK5": dict(bid=1.77, offer=2.0, time="17:03")}, held, NOW - dt.timedelta(days=1))
        q = dr.with_cache({"FG6GK5": dict(bid=None)}, held, NOW)
        self.assertIsNone(q["FG6GK5"]["bid"])

    def test_text_names_quote_time(self):
        sg = {"FG6GK5": dict(bid=1.77, from_cache=True, time="17:03"), "FC8QQU": dict(bid=1.38, time="21:03")}
        dep = dr.compute(dr.read_positions(TEXT), sg, BASE)
        t = dr.render(dep, BASE, NOW)
        self.assertIn("(SG price from 17:03)", t)
        self.assertNotIn("(SG price from 21:03)", t)

    def test_no_quote_no_zero_value(self):
        dep = dr.compute(dr.read_positions(TEXT), {"FG6GK5": dict(bid=None), "FC8QQU": dict(bid=None)}, BASE)
        t = dr.render(dep, BASE, NOW)
        self.assertNotIn("-19.8%", t)
        self.assertIn("no longer quotes", t)
        self.assertIn("Cash €80,233", t)


class Text(unittest.TestCase):
    def test_readable_and_short(self):
        dep = dr.compute(dr.read_positions(TEXT), SG, BASE)
        t = dr.render(dep, BASE, NOW)
        self.assertTrue(t.startswith("Daily status 7 Sep 21:31"))
        self.assertIn("Depot 1: €105,879 (+5.9% since start)", t)
        self.assertIn("Depot 2: €99,206 (-0.8% since start)", t)
        self.assertIn("Depot 1 is ahead.", t)
        self.assertIn("To do: Nothing.", t)
        self.assertNotIn("Depot A", t)
        self.assertLess(len(t), 700)

    def test_close_to_barrier(self):
        base = {"brent": dict(price=96.5, day=-0.01)}
        dep = dr.compute(dr.read_positions(TEXT), SG, base)
        t = dr.render(dep, base, NOW)
        self.assertIn("less than 1% from the barrier", t)
        self.assertIn("do nothing", t)

    def test_knocked_out(self):
        base = {"brent": dict(price=95.0, day=-0.03)}
        dep = dr.compute(dr.read_positions(TEXT), SG, base)
        t = dr.render(dep, base, NOW)
        self.assertIn("knocked out", t)
        self.assertIn("8:05", t)

    def test_no_position(self):
        empty = TEXT.split("## Open positions")[0] + "## Open positions\n## Resting sell orders\n"
        dep = dr.compute(dr.read_positions(empty), {}, {})
        t = dr.render(dep, {}, NOW)
        self.assertIn("Depot 1: €80,233", t)
        self.assertIn("No position, cash only", t)


if __name__ == "__main__":
    unittest.main()

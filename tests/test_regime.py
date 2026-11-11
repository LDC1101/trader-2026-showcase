import datetime as dt
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import regime  # noqa: E402

TODAY = dt.date(2026, 9, 18)  # Friday


def series(prices, end=TODAY):
    """Trading days backwards from the end date, weekends skipped."""
    out, d = [], end
    for c in reversed(prices):
        while d.weekday() >= 5:
            d -= dt.timedelta(days=1)
        out.append((d, c))
        d -= dt.timedelta(days=1)
    return list(reversed(out))


TREND = series([80 + i for i in range(16)])                       # +1 every day
ZIGZAG = series([90, 92, 90, 92, 90, 92, 90, 92, 90, 92, 90, 92, 90, 92, 90, 91])

POSITIONS = """# Positions
Date: 2026-09-17, 21:50
| | Depot A | Depot B |
|---|---|---|
| Depot value | 98,500.10 (21:50) | 131,237.78 (21:01) |
## Log
| Date | Action | Why | Result |
|---|---|---|---|
| 2026-09-07 | A: Gold put sold (+228). B: Brent put bought | x | y |
| 2026-09-10 | A: Brent call FG6GK5 knock-out, new FG7AAA. B: alive | x | y |
| 2026-09-14 | A: FG7AAA knocked out, new FG7BBB | x | y |
"""


class Window(unittest.TestCase):
    def test_trend_is_not_sideways(self):
        level, f10, f5 = regime.sideways(TREND, TODAY)
        self.assertEqual(level, 0)
        self.assertGreater(f10["eff"], 0.9)

    def test_zigzag_triggers(self):
        level, f10, f5 = regime.sideways(ZIGZAG, TODAY)
        self.assertEqual(level, 2)
        self.assertLess(f10["eff"], 0.25)
        self.assertLess(abs(f10["net"]), 0.05)

    def test_too_little_data(self):
        self.assertIsNone(regime.window(TREND[:5], 10))

    def test_plain_text_without_jargon(self):
        t = regime.plain_text(regime.window(ZIGZAG, 10))
        self.assertIn("two weeks", t)
        self.assertNotIn("efficiency", t.lower())


class Depot(unittest.TestCase):
    def test_status_and_knockouts(self):
        s = regime.depot_status(POSITIONS)
        self.assertEqual(s["A"], 98500.0)
        self.assertEqual(s["B"], 131237.0)
        self.assertEqual(s["date"], dt.date(2026, 9, 17))
        self.assertEqual(s["ko_a_streak"], 2)

    def test_bold_final_value(self):
        s = regime.depot_status("Date: 2026-10-26, last recorded state (the final week's Seagate trade was not logged)\n"
                                "| Depot value | **232,469.59** (cash) | 81,846.60 (cash) |\n")
        self.assertEqual((s["A"], s["B"]), (232469.0, 81846.0))

    def test_empty(self):
        s = regime.depot_status("")
        self.assertIsNone(s["A"])
        self.assertEqual(s["ko_a_streak"], 0)


class Assessment(unittest.TestCase):
    def test_calm(self):
        status = regime.depot_status(POSITIONS)
        b = regime.assess(TREND, status, [], TODAY)
        self.assertIn(b["stage"], ("calm", "warning"))  # two knock-outs -> warning
        self.assertIn("Depot", b["text"])
        self.assertNotIn("efficiency", b["text"].lower())
        self.assertIn("131,237 EUR", b["text"])
        self.assertIn("+31.2%", b["text"])

    def test_switch_to_weekly_mode(self):
        status = regime.depot_status(POSITIONS)
        b = regime.assess(ZIGZAG, status, [], TODAY)
        self.assertEqual(b["stage"], "switch")
        self.assertIn("weekly mode", b["text"])
        self.assertIn("2% distance", b["text"])

    def test_three_knockouts(self):
        status = regime.depot_status(POSITIONS.replace("| 2026-09-07 | A: Gold put sold (+228).", "| 2026-09-07 | A: call breached."))
        self.assertEqual(status["ko_a_streak"], 3)
        b = regime.assess(TREND, status, [], TODAY)
        self.assertEqual(b["stage"], "switch")
        self.assertIn("3 times in a row", b["text"])

    def test_write_off_main_prize(self):
        status = regime.depot_status(POSITIONS)
        today = dt.date(2026, 10, 13)
        b = regime.assess(series([80 + i for i in range(16)], today), status, [], today)
        self.assertEqual(b["stage"], "main_prize_off")
        self.assertIn("weekly scoring", b["text"])

    def test_weekly_result_from_history(self):
        history = [dict(date="2026-09-11", A=100000.0, B=110000.0)]
        ref, d = regime.last_friday_value(history, TODAY)
        self.assertEqual(ref, 110000.0)
        self.assertEqual(d, dt.date(2026, 9, 11))
        status = regime.depot_status(POSITIONS)
        b = regime.assess(TREND, status, history, TODAY)
        self.assertIn("+19.3% this week", b["text"])

    def test_date_in_header(self):
        b = regime.assess(TREND, regime.depot_status(POSITIONS), [], TODAY)
        self.assertTrue(b["text"].startswith("Regime check: warning 18 Sep\n"), b["text"][:40])

    def test_english_numbers(self):
        b = regime.assess(TREND, regime.depot_status(POSITIONS), [], TODAY)
        self.assertIn("The winning mark is 10x that", b["text"])
        self.assertNotIn("131.237", b["text"])
        self.assertNotIn("+31,2", b["text"])


if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import morning_card  # noqa: E402

TEXT = """| | Depot A | Depot B |
|---|---|---|
| Depot value | 120,368.01 (8 Sep 11:26) | 83,628.50 (8 Sep, cash only after knock-out) |
| Cash | 80,233.48 | 83,628.50 |
"""


class DepotValues(unittest.TestCase):
    def test_live_position_uses_depot_value(self):
        a, b = morning_card.depot_values(TEXT, live={"A": [("FG6GK5", "Brent", "long")], "B": [("X", "Brent", "short")]})
        self.assertEqual((a, b), (120368.01, 83628.50))

    def test_without_position_cash_counts(self):
        old = TEXT.replace("83,628.50 (8 Sep, cash only after knock-out)", "101,237.78 (9:01)")
        a, b = morning_card.depot_values(old, live={"A": [("FG6GK5", "Brent", "long")]})
        self.assertEqual(b, 83628.50)

    def test_order_size_keeps_20_percent(self):
        n, eur = morning_card.order_size(83628.50, 1.95)
        self.assertLessEqual(eur + morning_card.FEE, 0.20 * 83628.50)
        self.assertEqual(n, 8575)

    def test_bold_value(self):
        a, b = morning_card.depot_values("| Depot value | **232,469.59** (cash) | 81,846.60 (cash) |\n", live={"A": [1], "B": [1]})
        self.assertEqual((a, b), (232469.59, 81846.6))

    def test_empty(self):
        self.assertEqual(morning_card.depot_values("", live={}), (100000.0, 100000.0))


if __name__ == "__main__":
    unittest.main()

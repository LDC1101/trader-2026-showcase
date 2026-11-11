import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import watch  # noqa: E402

TEMPLATE = """# Positions

## Open positions

| Depot | WKN | Product | Underlying | Qty | Entry | Current | P/L % | Knock-out barrier |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

## Resting sell orders
"""

FILLED = """## Open positions

| Depot | WKN | Product | Underlying | Qty | Entry | Current | P/L % | Knock-out barrier |
|---|---|---|---|---|---|---|---|---|
| A | FG6QYM | BEST Turbo Call | Gold | 4,672 | 4.28 | 4.90 | +14.5 | 4,390.25 |
| B | FC8QP6 | BEST Turbo Put | Brent oil | 10,101 | 1.98 | 2.10 | +6.1 | 98.04 |
| | | | | | | | | |

## Resting sell orders

| Depot | WKN | Type | Price | Valid until |
|---|---|---|---|---|
| A | FG6QYM | Limit | 288.90 | 2026-09-14 |
"""

BROKEN = """## Open positions

| Depot | WKN | Product | Underlying | Qty | Entry | Current | P/L % | Knock-out barrier |
|---|---|---|---|---|---|---|---|---|
| A | FG6QYM | BEST Turbo Call | Gold | 4,672 | 4.28 | 4,390.25 |
| B | FC8QP6 | BEST Turbo Put | Brent | 10,101 | 1.98 | 2.10 | +6.1 | open |
| B | FC8QP7 | BEST Turbo Put | Copper | 10,101 | 1.98 | 2.10 | +6.1 | 98.04 |

## End
"""

GERMAN_NUMBERS = """## Open positions

| Depot | WKN | Product | Underlying | Qty | Entry | Current | P/L % | Knock-out barrier |
|---|---|---|---|---|---|---|---|---|
| A | FG6QYM | BEST Turbo Call | Gold | 4672 | 4,28 | 4,90 | +14,5 | 4.390,25 |
| B | FC8QP6 | BEST Turbo Put | Brent | 10101 | 1,98 | 2,10 | +6,1 | 98,04 |
"""


class PositionParser(unittest.TestCase):
    def setUp(self):
        self.logged = []
        self._log = watch.log
        watch.log = self.logged.append

    def tearDown(self):
        watch.log = self._log

    def test_template_is_empty(self):
        self.assertEqual(watch.open_positions(TEMPLATE), [])
        self.assertEqual(self.logged, [])

    def test_filled(self):
        p = watch.open_positions(FILLED)
        self.assertEqual(p, [("A", "FG6QYM", "Gold", "long", 4390.25),
                             ("B", "FC8QP6", "Brent", "short", 98.04)])
        self.assertEqual(self.logged, [])

    def test_sell_orders_are_not_read_as_positions(self):
        self.assertEqual(len(watch.open_positions(FILLED)), 2)

    def test_broken_rows_are_reported_not_swallowed(self):
        p = watch.open_positions(BROKEN)
        self.assertEqual(p, [])
        self.assertEqual(len(self.logged), 3)
        self.assertIn("9 columns", self.logged[0])
        self.assertIn("barrier", self.logged[1])
        self.assertIn("Copper", self.logged[2])

    def test_german_number_format_is_rejected(self):
        self.assertEqual(watch.open_positions(GERMAN_NUMBERS), [])
        self.assertEqual(len(self.logged), 2)
        self.assertTrue(all("barrier not readable" in m for m in self.logged))

    def test_number_parser(self):
        self.assertEqual(watch.parse_en_number("4,390.25"), 4390.25)
        self.assertEqual(watch.parse_en_number("**98.04**"), 98.04)
        self.assertEqual(watch.parse_en_number("1,234,567.5 USD"), 1234567.5)
        self.assertEqual(watch.parse_en_number("95"), 95.0)
        self.assertIsNone(watch.parse_en_number("98,04"))
        self.assertIsNone(watch.parse_en_number("4.390,25"))
        self.assertIsNone(watch.parse_en_number("open"))

    def test_file_missing(self):
        old = watch.REPO
        watch.REPO = "/nowhere"
        try:
            self.assertEqual(watch.open_positions(), [])
        finally:
            watch.REPO = old


if __name__ == "__main__":
    unittest.main()

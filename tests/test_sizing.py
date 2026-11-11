import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from sizing import limits, FEE_STOCK, FEE_DERIVATIVE  # noqa: E402


class RuleCalculator(unittest.TestCase):
    """Figures from the Monday plan, the project notes and the game rules."""

    def test_order_card_fc8qp6(self):
        # (20,000 - 3.90 fee) / ask 1.98 = 10,099 units. The platform counts the
        # fee towards the volume: on 7 Sep 2026, 4,040 x 4.95 = 19,998 was rejected.
        units, value, fee, _ = limits(100_000, 1.98, leveraged=True)
        self.assertEqual(units, 10_099)
        self.assertLessEqual(value + fee, 20_000)
        self.assertEqual(fee, FEE_DERIVATIVE)

    def test_absolute_cap_does_not_scale(self):
        # Depot 500k: 20% would be 100k, the EUR 20,000 cap stays
        units, value, _, _ = limits(500_000, 4.00, leveraged=True)
        self.assertEqual(units, 4_999)
        self.assertLessEqual(value + 3.90, 20_000)

    def test_small_depot_20_percent(self):
        units, value, _, _ = limits(50_000, 1.00, leveraged=True)
        self.assertEqual(units, 9_996)

    def test_platform_rejection_2026_09_07(self):
        # Measured: 4,040 x 4.95 = EUR 19,998 rejected ("20% exceeded"),
        # 4,000 x 4.95 accepted. The calculator must no longer return 4,040.
        units, value, fee, _ = limits(100_000, 4.95, leveraged=True)
        self.assertLess(units, 4_040)
        self.assertLessEqual(value + fee, 20_000)

    def test_unit_cap_limits_cheap_products(self):
        # At EUR 0.80 the 20,000-unit cap limits the order to EUR 16,000
        units, value, _, _ = limits(100_000, 0.80, leveraged=True)
        self.assertEqual(units, 20_000)
        self.assertAlmostEqual(value, 16_000)

    def test_existing_leverage_is_deducted(self):
        units, value, _, _ = limits(100_000, 2.00, leveraged=True, already_leveraged=15_000)
        self.assertEqual(units, 2_498)

    def test_leverage_budget_used_up(self):
        units, value, _, _ = limits(100_000, 2.00, leveraged=True, already_leveraged=20_000)
        self.assertEqual(units, 0)
        self.assertEqual(value, 0)

    def test_stock_20_percent_cumulative(self):
        units, value, fee, _ = limits(100_000, 50.0, leveraged=False)
        self.assertEqual(units, 399)   # 400 x 50 + EUR 10 fee would exceed 20,000
        self.assertEqual(fee, FEE_STOCK)
        units, _, _, _ = limits(100_000, 50.0, leveraged=False, already_position=15_000)
        self.assertEqual(units, 99)

    def test_stock_has_no_unit_cap(self):
        units, _, _, _ = limits(1_000_000, 5.0, leveraged=False)
        self.assertEqual(units, 39_998)

    def test_never_negative(self):
        units, value, _, _ = limits(100_000, 2.00, leveraged=False, already_position=30_000)
        self.assertEqual((units, value), (0, 0))


if __name__ == "__main__":
    unittest.main()

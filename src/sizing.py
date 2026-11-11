"""
Rule calculator for Trader 2026.

Run it before EVERY order. The game rules set four caps that apply at the same
time, and an order that breaks one is cut down automatically (section 5).
Doing the sums in your head ends with buying 20,001 units one day.

    20% rule          per security at most 20% of the depot value IN TOTAL,
                      cumulative over all purchases of the same security, not
                      per order. Holding 15% already leaves room for 5% more.
    20% leverage rule all leveraged derivatives together at most 20%
    EUR 20,000 rule   leveraged derivatives together at most EUR 20,000,
                      regardless of the depot value
    20,000 units      at most 20,000 units per leveraged derivative

All caps refer to the TIME OF PURCHASE and to the ASK price. A position that
later grows past 20% is within the rules; this is the whole mechanism by
which EUR 20,000 can turn into a million.

Usage:    python3 src/sizing.py 100000 --ask 2.50 --leveraged
          python3 src/sizing.py 340000 --ask 18.40
"""

import argparse

FEE_STOCK = 10.00
FEE_DERIVATIVE = 3.90
BUY_ORDERS_PER_DAY = 20
HOLDING_PERIOD_MIN = 5


def limits(depot_value, ask, leveraged, already_leveraged=0.0, already_position=0.0):
    """Maximum units and order value for one order.

    already_position  purchase value already held in THIS security.
                      The 20% rule applies "in total", so cumulatively.
    """
    max_position = 0.20 * depot_value - already_position   # 20% rule, cumulative
    caps = [("20% of depot value (cumul.)", max_position)]

    if leveraged:
        leverage_budget = min(0.20 * depot_value, 20_000.0) - already_leveraged
        caps.append(("20% in leveraged products", 0.20 * depot_value - already_leveraged))
        caps.append(("EUR 20,000 absolute", 20_000.0 - already_leveraged))
        max_position = min(max_position, max(leverage_budget, 0.0))

    # The platform counts the order fee towards the volume (7 Sep 2026: 4,040 x 4.95
    # = EUR 19,998 was rejected with "20% exceeded", 19,998 + 3.90 > 20,000).
    fee = FEE_DERIVATIVE if leveraged else FEE_STOCK
    max_position = max(max_position - fee, 0.0)
    units = int(max_position // ask)
    if leveraged:
        units = min(units, 20_000)                     # 20,000-unit rule
        caps.append(("20,000 units", 20_000 * ask))

    order_value = units * ask
    return units, order_value, fee, caps


def main():
    ap = argparse.ArgumentParser(description="Trader 2026 rule calculator")
    ap.add_argument("depot_value", type=float, help="current depot value in EUR")
    ap.add_argument("--ask", type=float, required=True, help="ask price of the product")
    ap.add_argument("--leveraged", action="store_true",
                    help="leveraged derivative (turbo/warrant/factor certificate)")
    ap.add_argument("--already", type=float, default=0.0,
                    help="already invested in leveraged products in total (EUR, purchase value)")
    ap.add_argument("--already-position", type=float, default=0.0,
                    help="already held in THIS security (EUR, purchase value)")
    a = ap.parse_args()

    units, order_value, fee, caps = limits(
        a.depot_value, a.ask, a.leveraged, a.already, a.already_position)

    kind = "leveraged deriv." if a.leveraged else "stock"
    print(f"\n  Depot value    {a.depot_value:>14,.2f} EUR")
    print(f"  Product        {kind:>14}   Ask {a.ask:,.4f} EUR")
    if a.leveraged and a.already:
        print(f"  Already lev.   {a.already:>14,.2f} EUR")
    if a.already_position:
        print(f"  of which in THIS security {a.already_position:>7,.2f} EUR")
    print(f"\n  Binding caps:")
    for name, value in sorted(caps, key=lambda x: x[1]):
        mark = " <-- binds" if abs(value - order_value) < a.ask else ""
        print(f"    {name:<28}{max(value, 0):>14,.2f} EUR{mark}")

    print(f"\n  MAXIMUM  {units:>10,} units  =  {order_value:>12,.2f} EUR")
    print(f"  Fee      {fee:>10,.2f} EUR   ({fee / max(order_value, 1e-9):.3%} of order value)")
    print(f"  Share of depot: {order_value / a.depot_value:.1%}")

    if a.leveraged:
        rest = 20_000.0 - a.already - order_value
        print(f"\n  Left for leveraged products afterwards: {max(rest, 0):,.2f} EUR")
    print(f"""
  Place these RIGHT AFTER THE PURCHASE. The exit is set at entry, not
  decided later:
    Limit sell at the target price, valid for 7 days
    Stop loss where it makes sense (no protection against gaps through the barrier)
    Both are order types of the platform itself, not an automated system.
    Validity is 7 calendar days, renew weekly.

  Reminder:
    Holding period of {HOLDING_PERIOD_MIN} minutes after each purchase. Sell orders
    can be placed at once but only become active after that.
    {BUY_ORDERS_PER_DAY} buy orders per depot and day. Sells are unlimited.
    Trading 8:00-22:00, Börse Stuttgart / EUWAX.
""")


if __name__ == "__main__":
    main()

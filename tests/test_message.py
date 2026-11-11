import datetime as dt
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import watch  # noqa: E402

NOW = dt.datetime(2026, 9, 7, 14, 30)

COUNCIL = """SIGNAL: strong long Brent (council of 5 members, 2 round(s), SPLIT, evidence S1/2xS2 yes)
WHAT: UKMTO reports an attack on a tanker, Reuters confirms.
DEPOTS: Depot A Brent call gains, the distance to the barrier grows. Depot B unchanged.
ABORT: no (S1/2xS2)
ACTION: none
EVIDENCED: yes
COUNCIL:
- Maritime: yes, strong long, abort no, none | ukmto.org S1
- Fact-checker: yes, strong long, abort no, none | reuters.com S2
DISSENT: Oil market: check, ..."""

ALERTS = ["BRENT 71.20 $: +3.1% since the last alert (69.05).",
          "HEADLINES\n• [Reuters|S2] Tanker attacked off Hormuz\n• [IRNA English|S3] Iran denies"]


class Message(unittest.TestCase):
    def test_depot_assessment_first_and_short(self):
        t = watch.for_player("", NOW, COUNCIL, ALERTS)
        parts = t.split("\n\n")
        self.assertEqual(parts[0], "7 Sep 14:30")
        self.assertTrue(parts[1].startswith("Depot 1 Brent call gains"))
        self.assertIn("To do: nothing.", t)
        self.assertIn("Why: UKMTO reports", t)
        for banned in ("SIGNAL", "COUNCIL:", "DISSENT", "S1/2xS2", "HEADLINES", "IRNA", "EVIDENCED", "Depot A", "Depot B"):
            self.assertNotIn(banned, t)
        self.assertLess(len(t), 900)

    def test_header_and_action(self):
        result = COUNCIL.replace("ACTION: none", "ACTION: close: Depot B, barrier at risk")
        t = watch.for_player("ALERT: ACT", NOW, result, ALERTS)
        self.assertTrue(t.startswith("ALERT: ACT 7 Sep 14:30"))
        self.assertIn("To do: close: Depot 2, barrier at risk", t)

    def test_watch_calls_to_action_stay(self):
        m = ALERTS + ["KNOCK-OUT Depot A DE000SX1 (Brent long): price 64.00, barrier 65.00. Per the thesis, re-enter at once; update depot/positions.md."]
        t = watch.for_player("", NOW, COUNCIL, m)
        self.assertIn("KNOCK-OUT Depot 1", t)
        self.assertNotIn("BRENT 71.20", t)

    def test_buy_card_stays_but_not_a_no_buy_card(self):
        buy = "REPLACEMENT ORDER DEPOT A\nDEPOT A: BUY Brent turbo LONG (Call)"
        none = "REPLACEMENT ORDER DEPOT A\nDEPOT A: no Brent call within 2 %, do not buy"
        t = watch.for_player("", NOW, COUNCIL, ALERTS + [buy, none])
        self.assertIn("BUY Brent turbo", t)
        self.assertNotIn("do not buy", t)

    def test_without_assessment_the_trigger_remains(self):
        t = watch.for_player("", NOW, None, ALERTS)
        self.assertIn("Assessment failed", t)
        self.assertIn("BRENT 71.20", t)
        self.assertLess(len(t), 400)


class ActionWords(unittest.TestCase):
    def test_label_itself_is_not_an_action(self):
        self.assertFalse(watch.wants_action("ACTION: none"))
        self.assertTrue(watch.wants_check("ACTION: check: UKMTO advisory"))
        self.assertFalse(watch.wants_action("ACTION: check: UKMTO advisory"))

    def test_buy_and_close(self):
        self.assertTrue(watch.wants_action("ACTION: buy: turbo call Brent, 1 % distance"))
        self.assertTrue(watch.wants_action("ACTION: close: Depot B"))
        self.assertTrue(watch.wants_action("ACTION: check (without council): buy: turbo call Brent"))
        self.assertFalse(watch.wants_action("ACTION: check: whether the strait closure holds"))


if __name__ == "__main__":
    unittest.main()

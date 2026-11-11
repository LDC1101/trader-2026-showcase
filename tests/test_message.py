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


class Triggers(unittest.TestCase):
    def test_whole_words_only(self):
        for title in ("Oil steady, according to traders watching Iran", "Iran to determine its quota",
                      "Iran oil dealer arrested", "Iran striker joins club"):
            self.assertIsNone(watch.ACTION_RE.search(title), title)

    def test_inflections_still_match(self):
        for title in ("Iran and US sign accord", "Tankers attacked near Hormuz", "Strait reopened",
                      "Mines found in the strait", "Peace talks resume", "US strikes Iranian site",
                      "Envoys meet in Muscat", "Negotiations stall", "End of the war in sight"):
            self.assertIsNotNone(watch.ACTION_RE.search(title), title)


class Headers(unittest.TestCase):
    ALERTS = ["BRENT 101.20 $: +4.1% since the last alert (97.20).",
              "HEADLINES\n• [IRNA English|S3] Strait reopened, deal signed"]

    def test_fallback_without_council_never_acts(self):
        # consult_or_assess rewrites buy/close to "check (without council)"
        result = ("SIGNAL: medium long Brent\nWHAT: x\nDEPOTS: A | B\nABORT: no (S1)\n"
                  "ACTION: check (without council): buy: turbo call Brent\nEVIDENCED: no (without council)")
        header, _ = watch.header_for(result, self.ALERTS)
        self.assertEqual(header, "WATCH")

    def test_council_buy_with_measurement_acts(self):
        result = "SIGNAL: strong long Brent\nACTION: buy: turbo call Brent, 1 % distance\nEVIDENCED: yes"
        self.assertEqual(watch.header_for(result, self.ALERTS)[0], "ALERT: ACT")

    def test_buy_on_state_media_alone_is_downgraded(self):
        result = "SIGNAL: weak long Brent\nACTION: buy: turbo call Brent\nEVIDENCED: no"
        header, text = watch.header_for(result, ["HEADLINES\n• [IRNA English|S3] Strait reopened"])
        self.assertEqual(header, "WATCH (source not yet confirmed)")
        self.assertIn("source unconfirmed", text)

    def test_failed_replacement_card_reaches_the_player(self):
        alerts = ["KNOCK-OUT A FG6MRT (Brent long): low since the last run 104.06, barrier 104.74, price now 105.70.",
                  "REPLACEMENT ORDER DEPOT A: could not be determined; run python3 src/morning_card.py --depot A --text-only"]
        t = watch.for_player("", NOW, "", alerts)
        self.assertIn("could not be determined", t)


class Memory(unittest.TestCase):
    def test_keeps_newest_not_alphabetically_last(self):
        fresh, memory = watch.remember(["zeta", "beta"], ["alpha", "beta", "gamma"], 3)
        self.assertEqual(fresh, ["alpha", "gamma"])
        self.assertEqual(memory, ["beta", "alpha", "gamma"])   # "zeta" was the oldest
        fresh, _ = watch.remember(memory, ["alpha"], 3)
        self.assertEqual(fresh, [])


class Cot(unittest.TestCase):
    @staticmethod
    def row(name, mm_long, mm_short, swap_long=900, swap_short=100):
        r = [f'"{name}"', "261103", "2026-11-03", "06765T", "NYME", "00", "067",
             "5000", "10", "20", str(swap_long), str(swap_short), "5", str(mm_long), str(mm_short)] + ["0"] * 10
        return ",".join(r)

    def test_managed_money_columns(self):
        txt = self.row("BRENT LAST DAY - NEW YORK MERCANTILE EXCHANGE", 700, 200)
        self.assertEqual(watch.parse_cot(txt)["Brent"], dict(date="2026-11-03", net=500))

    def test_micro_gold_does_not_overwrite_gold(self):
        txt = "\n".join([self.row("GOLD - COMMODITY EXCHANGE INC.", 300, 100),
                         self.row("MICRO GOLD - COMMODITY EXCHANGE INC.", 5, 9)])
        self.assertEqual(watch.parse_cot(txt)["Gold"]["net"], 200)


class Basis(unittest.TestCase):
    def test_futures_extremes_are_mapped_onto_spot(self):
        # 7 Sep 2026: gold future 4,444, spot 4,395
        f = watch.basis_factor(4395, 4444)
        self.assertLess(4455 * f, 4450)   # a futures high of 4,455 is no spot knock-out at 4,450

    def test_different_instrument_is_rejected(self):
        self.assertIsNone(watch.basis_factor(92.0, 104.0))
        self.assertEqual(watch.basis_factor(None, 104.0), 1.0)


if __name__ == "__main__":
    unittest.main()

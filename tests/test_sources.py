import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import sources  # noqa: E402


class Register(unittest.TestCase):
    def test_tiers_of_known_sources(self):
        self.assertEqual(sources.tier("UKMTO"), 1)
        self.assertEqual(sources.tier("@UK_MTO"), 1)
        self.assertEqual(sources.tier("CNBC"), 2)
        self.assertEqual(sources.tier("gCaptain"), 2)
        self.assertEqual(sources.tier("IRNA English"), 3)
        self.assertEqual(sources.tier("@IrnaEnglish"), 3)
        self.assertEqual(sources.tier("X search"), 4)
        self.assertEqual(sources.tier("@JavierBlas"), 4)
        self.assertEqual(sources.tier("Yahoo Finance"), 4)

    def test_domain_and_url(self):
        self.assertEqual(sources.tier("https://www.reuters.com/world/x"), 2)
        self.assertEqual(sources.tier("mehrnews.com"), 3)
        self.assertEqual(sources.tier("https://seekingalpha.com/article/1"), 4)

    def test_unknown_is_tier_4(self):
        self.assertEqual(sources.tier("unknown-site.example"), 4)
        self.assertEqual(sources.tier(""), 4)

    def test_tagged_name(self):
        self.assertEqual(sources.tier("CNBC|S2"), 2)
        self.assertEqual(sources.tag("[CNBC] Title"), "[CNBC|S2] Title")
        self.assertEqual(sources.tag("[CNBC|S2] Title"), "[CNBC|S2] Title")

    def test_feeds_are_in_the_register(self):
        from situation import FEEDS
        for name, _, _ in FEEDS:
            self.assertIn(name, sources.SOURCES)


class Gate(unittest.TestCase):
    def test_state_media_alone_does_not_trigger(self):
        m = ["HEADLINES\n• [IRNA English|S3] Strait of Hormuz reopened, deal signed"]
        self.assertFalse(sources.may_trigger(m))

    def test_social_alone_does_not_trigger(self):
        m = ["X SEARCH\n• [X search|S4] BREAKING deal signed", "R/GEOPOLITICS\n• [r/geopolitics|S4] Hormuz open"]
        self.assertFalse(sources.may_trigger(m))

    def test_one_wire_is_not_enough(self):
        m = ["HEADLINES\n• [CNBC|S2] Iran, US sign Hormuz accord"]
        self.assertFalse(sources.may_trigger(m))

    def test_two_wires_are_enough(self):
        m = ["HEADLINES\n• [CNBC|S2] Iran, US sign Hormuz accord\n• [gCaptain|S2] Hormuz accord signed, transits resume"]
        self.assertTrue(sources.may_trigger(m))

    def test_primary_source_is_enough_alone(self):
        m = ["UKMTO\n• [UKMTO|S1] Advisory 130-26: strait open to commercial traffic"]
        self.assertTrue(sources.may_trigger(m))

    def test_own_measurement_is_tier_1(self):
        # A knock-out and a Brent jump are data, not reports
        m = ["KNOCK-OUT A FG6GK5 (Brent long): price 95.80, barrier 95.86."]
        self.assertTrue(sources.may_trigger(m))
        m = ["BRENT 101.20 $: +4.1% since the last alert (97.20)."]
        self.assertTrue(sources.may_trigger(m))

    def test_state_media_plus_social_stays_closed(self):
        m = ["HEADLINES\n• [IRNA English|S3] deal", "X SEARCH\n• [X search|S4] deal", "R/GEOPOLITICS\n• [r/geopolitics|S4] deal"]
        self.assertFalse(sources.may_trigger(m))

    def test_allowed_domains_without_s3_s4(self):
        d = sources.allowed_domains()
        self.assertIn("reuters.com", d)
        self.assertIn("ukmto.org", d)
        self.assertNotIn("irna.ir", d)
        self.assertNotIn("seekingalpha.com", d)
        self.assertNotIn("x.com", d)


if __name__ == "__main__":
    unittest.main()

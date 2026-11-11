import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from situation import feed_entries, classify  # noqa: E402

RSS = """<?xml version="1.0"?><rss><channel><title>Channel</title>
<item><title><![CDATA[U.S. strikes 3 Iranian oil tankers]]></title><pubDate>Sat, 05 Sep 2026 15:07:21 +0000</pubDate></item>
<item><title>Fed &amp; rates</title><pubDate>Fri, 04 Sep 2026 10:00:00 GMT</pubDate></item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Ministry of Defence</title>
<entry><title type="text">UK forces join Arctic exercise</title><updated>2026-09-05T09:30:00+01:00</updated></entry>
<entry><title>Escort mission statement</title><published>2026-09-04T18:00:00Z</published></entry>
</feed>"""


class FeedParser(unittest.TestCase):
    def test_rss_with_cdata_and_entity(self):
        e = feed_entries(RSS)
        self.assertEqual(len(e), 2)
        self.assertEqual(e[0], ("U.S. strikes 3 Iranian oil tankers", "Sat, 05 Sep 2026"))
        self.assertEqual(e[1][0], "Fed & rates")

    def test_entity_inside_cdata_is_decoded(self):
        # CNBC, 11 Nov 2026: titles showed "Nvidia&apos;s" to the player
        rss = "<rss><item><title><![CDATA[Nvidia&apos;s Huang]]></title></item></rss>"
        self.assertEqual(feed_entries(rss)[0][0], "Nvidia's Huang")

    def test_atom_title_with_attribute_and_updated(self):
        e = feed_entries(ATOM)
        self.assertEqual(len(e), 2)
        self.assertEqual(e[0], ("UK forces join Arctic exercise", "2026-09-05T09:30"))
        self.assertEqual(e[1][1], "2026-09-04T18:00")

    def test_feed_title_is_not_an_entry(self):
        self.assertNotIn("Channel", [t for t, _ in feed_entries(RSS)])
        self.assertNotIn("Ministry of Defence", [t for t, _ in feed_entries(ATOM)])

    def test_limit(self):
        self.assertEqual(len(feed_entries(RSS, limit=1)), 1)


class Topics(unittest.TestCase):
    def test_word_start_matches_inflection(self):
        self.assertIn("Rates/Fed", classify("Trump turns up the heat as Fed rate hike looms"))
        self.assertIn("Rates/Fed", classify("Mortgage rates much higher week-over-week"))

    def test_word_start_does_not_match_inside_a_word(self):
        self.assertEqual(classify("Hegseth Welcomes Deputy PM, Commemorates Alliance"), [])
        self.assertEqual(classify("UK forces join trilateral Arctic exercise in strategic High North operation"), [])

    def test_irna_needs_a_second_word(self):
        self.assertEqual(classify("Iran Expo 2026 to bring together 1,500 foreign traders", "IRNA English"), [])
        self.assertIn("Oil/Hormuz", classify("IRGC attacks US vessel seeking access to Strait of Hormuz", "IRNA English"))
        self.assertIn("Oil/Hormuz", classify("Iran condemns US attacks on oil tankers", "IRNA English"))

    def test_iran_counts_for_other_sources(self):
        self.assertIn("Oil/Hormuz", classify("Iran warns of more painful response", "CNBC"))

    def test_several_topics(self):
        t = classify("U.S. Energy Secretary says Iran nuclear deal may never happen", "CNBC")
        self.assertIn("Oil/Hormuz", t)
        self.assertIn("AI energy", t)


if __name__ == "__main__":
    unittest.main()

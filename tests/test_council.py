import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import council  # noqa: E402


def v(role, action="none", abort="no", evidence=None, signal="weak", direction="neutral", confirmed=None):
    if confirmed is None:
        confirmed = "yes" if evidence else "unclear"
    return dict(role=role, confirmed=confirmed, signal=signal, direction=direction,
                evidence=evidence or [], abort=abort, action=action, reasoning=f"{role} says", reply="")


class Classes(unittest.TestCase):
    def test_action_classes(self):
        self.assertEqual(council._action_class("close: Depot A"), "close")
        self.assertEqual(council._action_class("Close: A"), "close")
        self.assertEqual(council._action_class("buy: Brent call"), "buy")
        self.assertEqual(council._action_class("check: UKMTO"), "check")
        self.assertEqual(council._action_class("none"), "none")
        self.assertEqual(council._action_class(None), "check")

    def test_abort_classes(self):
        self.assertEqual(council._abort_class("YES: agreement reported"), "YES")
        self.assertEqual(council._abort_class("no (only S3)"), "no")


class Agreement(unittest.TestCase):
    def test_agreed(self):
        self.assertTrue(council.agreed([v("A"), v("B"), v("C")]))

    def test_split_on_action(self):
        self.assertFalse(council.agreed([v("A"), v("B", "close: A")]))

    def test_none_and_check_count_as_agreed(self):
        self.assertTrue(council.agreed([v("A", "none"), v("B", "check: look it up")]))

    def test_evidence_against_the_alert_does_not_count(self):
        # straits.live (S1) refutes the alert -> confirmed=no -> not "evidenced"
        a = v("A", evidence=[dict(source="straits.live", url="https://straits.live/")], confirmed="no")
        self.assertFalse(council.evidenced([a]))

    def test_split_on_abort(self):
        self.assertFalse(council.agreed([v("A"), v("B", abort="YES: x")]))


class Evidence(unittest.TestCase):
    def test_state_media_is_not_enough(self):
        self.assertFalse(council.evidenced([v("A", evidence=[dict(source="IRNA English", url="https://en.irna.ir/x")])]))

    def test_primary_is_enough(self):
        self.assertTrue(council.evidenced([v("A", evidence=[dict(source="UKMTO", url="https://www.ukmto.org/recent-incidents")])]))

    def test_two_wires_across_members(self):
        a = v("A", evidence=[dict(source="Reuters", url="https://www.reuters.com/a")])
        b = v("B", evidence=[dict(source="CNBC", url="https://www.cnbc.com/b")])
        self.assertTrue(council.evidenced([a, b]))

    def test_one_wire_twice_is_not_enough(self):
        a = v("A", evidence=[dict(source="Reuters", url="https://www.reuters.com/a")])
        b = v("B", evidence=[dict(source="Reuters", url="https://www.reuters.com/a")])
        self.assertFalse(council.evidenced([a, b]))


class Summary(unittest.TestCase):
    def test_split_takes_the_cautious_class(self):
        verdicts = [v("Maritime", "close: A", "YES: agreement"), v("Fact-checker", "check: wording"), v("Depot", "none")]
        t = council.summarize(verdicts, 3, "m")
        self.assertTrue(t.startswith("SIGNAL:"))
        self.assertIn("SPLIT", t)
        self.assertIn("ACTION: none", t)
        self.assertIn("ABORT: no", t)
        self.assertIn("EVIDENCED: no", t)
        self.assertIn("DISSENT:", t)
        self.assertIn("WHAT: Fact-checker says", t)

    def test_agreed_with_evidence(self):
        b = [dict(source="UKMTO", url="https://www.ukmto.org/x")]
        verdicts = [v("Maritime", "close: Depot A", "YES: agreement", b, "strong", "short"),
                    v("Depot", "close: Depot A", "YES: agreement", [], "strong", "short")]
        t = council.summarize(verdicts, 1, "m")
        self.assertIn("agreed", t)
        self.assertIn("ACTION: close: Depot A", t)
        self.assertIn("EVIDENCED: yes", t)
        self.assertNotIn("DISSENT", t)

    def test_summary_has_no_em_dash(self):
        t = council.summarize([v("Maritime"), v("Depot")], 1, "m")
        self.assertNotIn("\u2014", t)


class PromptSections(unittest.TestCase):
    """The prompts quote sections of the strategy docs by heading. A renamed
    heading would silently feed the whole file (or nothing) to the model."""

    def test_markers_exist_in_the_docs(self):
        import watch
        for rel, marker in [("strategy/00-thesis.md", "## Abort conditions"),
                            ("strategy/40-themes.md", "**Triggers for immediate action:**"),
                            ("strategy/40-themes.md", "## 2."),
                            ("strategy/70-hormuz-dossier.md", "## Summary"),
                            ("strategy/70-hormuz-dossier.md", "## Chronology"),
                            ("strategy/70-hormuz-dossier.md", "## What prices said"),
                            ("strategy/70-hormuz-dossier.md", "## Actors"),
                            ("depot/positions.md", "## Open positions"),
                            ("depot/positions.md", "## Resting sell orders"),
                            ("depot/positions.md", "## Log")]:
            path = os.path.join(watch.REPO, rel)
            if not os.path.exists(path):
                self.skipTest(f"{rel} not present")
            with open(path, encoding="utf-8") as f:
                self.assertIn(marker.lower(), f.read().lower(), f"{marker!r} missing in {rel}")


class Roles(unittest.TestCase):
    def test_five_roles_and_summary_roles_exist(self):
        self.assertEqual(len(council.ROLES), 5)
        self.assertIn("Fact-checker", council.ROLES)
        self.assertIn("Depot", council.ROLES)


if __name__ == "__main__":
    unittest.main()

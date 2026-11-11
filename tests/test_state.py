import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from situation import load_json, write_json  # noqa: E402


class StateFiles(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.p = os.path.join(self.d, "sub", "state.json")

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_round_trip_and_no_tmp_left(self):
        write_json(self.p, {"a": 1, "u": "é"}, indent=1)
        self.assertEqual(load_json(self.p), {"a": 1, "u": "é"})
        self.assertFalse(os.path.exists(self.p + ".tmp"))

    def test_missing(self):
        self.assertEqual(load_json(self.p), {})
        self.assertEqual(load_json(self.p, default=[]), [])

    def test_corrupt_file_is_moved_aside(self):
        os.makedirs(os.path.dirname(self.p))
        with open(self.p, "w") as f:
            f.write('{"offset": 12')  # interrupted write
        self.assertEqual(load_json(self.p), {})
        self.assertFalse(os.path.exists(self.p))
        self.assertTrue(os.path.exists(self.p + ".corrupt"))

    def test_overwrite(self):
        write_json(self.p, {"n": 1})
        write_json(self.p, {"n": 2})
        self.assertEqual(load_json(self.p)["n"], 2)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

import verify


class TestNormalizeText(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(verify.normalize_text("a   b\n c"), "a b c")

    def test_smart_quotes_become_straight(self):
        self.assertEqual(verify.normalize_text("“hello”"), '"hello"')


class TestVerifyQuote(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.source = Path(self.tmpdir.name) / "interview_1_Test.txt"
        self.source.write_text(
            'PAIN POINTS\n- "We just don’t deliver well and the hierarchy slows us down"\n',
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_exact_match_passes(self):
        quote = "We just don’t deliver well and the hierarchy slows us down"
        self.assertTrue(verify.verify_quote(quote, self.source))

    def test_smart_quote_only_difference_passes(self):
        # Source has a curly apostrophe; this quote uses a straight one.
        quote = "We just don't deliver well and the hierarchy slows us down"
        self.assertTrue(verify.verify_quote(quote, self.source))

    def test_single_word_alteration_fails(self):
        quote = "We just don’t deliver poorly and the hierarchy slows us down"
        self.assertFalse(verify.verify_quote(quote, self.source))


if __name__ == "__main__":
    unittest.main()

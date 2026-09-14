import tempfile
import unittest
from pathlib import Path

import extract


class TestExtractQuotes(unittest.TestCase):
    def setUp(self):
        self.themes = [
            extract.Theme(
                name="Decisions bottleneck at the top",
                description="test",
                keywords=["hierarchy", "approval"],
            )
        ]
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmpdir.cleanup()

    def _write(self, name: str, content: str) -> Path:
        path = Path(self.tmpdir.name) / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_quoted_bullet_matching_keyword_is_extracted(self):
        path = self._write(
            "interview_1_Test_Role.txt",
            "GNP FOUNDATION — INTERVIEW NOTES (1 of 5) | Test Role\n\n"
            "PAIN POINTS\n"
            '- "The hierarchy causes leadership to struggle with approvals"\n',
        )
        matches = extract.extract_quotes_from_file(path, self.themes)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].quote, "The hierarchy causes leadership to struggle with approvals")
        self.assertEqual(matches[0].speaker, "Test Role")
        self.assertIn("Decisions bottleneck at the top", matches[0].themes)

    def test_quoted_bullet_with_no_keyword_hit_is_excluded(self):
        path = self._write(
            "interview_2_Test_Role.txt",
            "GNP FOUNDATION — INTERVIEW NOTES (2 of 5) | Test Role\n\n"
            "STRENGTHS\n"
            '- "We have a lot of passionate, mission-driven people"\n',
        )
        matches = extract.extract_quotes_from_file(path, self.themes)
        self.assertEqual(matches, [])

    def test_unquoted_bullet_is_never_extracted_even_with_keyword(self):
        path = self._write(
            "interview_3_Test_Role.txt",
            "GNP FOUNDATION — INTERVIEW NOTES (3 of 5) | Test Role\n\n"
            "PAIN POINTS\n"
            "- The hierarchy and approval chain is too slow, no quotes here\n",
        )
        matches = extract.extract_quotes_from_file(path, self.themes)
        self.assertEqual(matches, [])

    def test_all_caps_headers_and_blank_lines_are_skipped(self):
        path = self._write(
            "interview_4_Test_Role.txt",
            "GNP FOUNDATION — INTERVIEW NOTES (4 of 5) | Test Role\n\n"
            "PAIN POINTS\n\n"
            '- "The hierarchy is a real approval bottleneck"\n',
        )
        matches = extract.extract_quotes_from_file(path, self.themes)
        self.assertEqual(len(matches), 1)


if __name__ == "__main__":
    unittest.main()

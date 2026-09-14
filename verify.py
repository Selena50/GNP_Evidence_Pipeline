"""Pure string-matching verification of extracted quotes.

Every quote that extract.py pulls out is, by construction, a literal
substring of its source file. This module doesn't trust that promise: it
re-opens the cited file and re-checks the quote against it, independently.

Normalization only smooths over formatting noise (smart quotes, repeated
whitespace) -- it never does fuzzy/approximate matching. After
normalization the check is exact substring containment, nothing softer.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_SMART_QUOTES = {
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
}


def normalize_text(text: str) -> str:
    for smart, straight in _SMART_QUOTES.items():
        text = text.replace(smart, straight)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


@dataclass
class VerificationResult:
    quote: str
    speaker: str
    source_file: str
    themes: list[str]
    passed: bool


def verify_quote(quote_text: str, source_path: Path) -> bool:
    content = source_path.read_text(encoding="utf-8")
    return normalize_text(quote_text) in normalize_text(content)


def verify_all(matches, interviews_dir: str | Path) -> list[VerificationResult]:
    interviews_dir = Path(interviews_dir)
    results = []
    for match in matches:
        source_path = interviews_dir / match.source_file
        passed = verify_quote(match.quote, source_path)
        results.append(
            VerificationResult(
                quote=match.quote,
                speaker=match.speaker,
                source_file=match.source_file,
                themes=list(match.themes),
                passed=passed,
            )
        )
    return results

"""Deterministic, keyword-driven quote extraction from interview transcripts.

No LLM calls anywhere here: theme matching is a case-insensitive substring
check against the keyword lists in themes.json. A "quote" only ever comes
from text that was already wrapped in quotation marks in the source file.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# Matches a straight-quoted or curly-quoted span within a single line.
# Straight quotes: "..."   Curly quotes: “...”
QUOTE_PATTERN = re.compile(r'"([^"]+)"|“([^”]+)”')

HEADER_SPEAKER_PATTERN = re.compile(r'\|\s*(.+?)\s*$')


@dataclass
class Theme:
    name: str
    description: str
    keywords: list[str]


@dataclass
class QuoteMatch:
    quote: str
    speaker: str
    source_file: str
    themes: list[str] = field(default_factory=list)


def load_themes(themes_path: str | Path) -> list[Theme]:
    data = json.loads(Path(themes_path).read_text(encoding="utf-8"))
    return [
        Theme(name=t["name"], description=t.get("description", ""), keywords=t.get("keywords", []))
        for t in data.get("themes", [])
    ]


def is_bullet_line(line: str) -> bool:
    """Only lines that are actually bulleted count as content lines.

    This is what lets us "skip all-caps section headers and blank lines"
    without special-casing them: headers and the title line never start
    with a bullet marker in these transcripts.
    """
    return line.strip().startswith(("-", "*", "•"))


def derive_speaker(file_path: str | Path, lines: list[str]) -> str:
    """Prefer a header line like '... | President & CEO'; fall back to the filename."""
    for line in lines[:5]:
        if "|" in line:
            match = HEADER_SPEAKER_PATTERN.search(line)
            if match:
                return match.group(1).strip()

    stem = Path(file_path).stem
    parts = stem.split("_")
    # Drop the leading "interview" and its number, e.g. ["interview", "1", "President", "and", "CEO"]
    parts = [p for p in parts[2:]] if len(parts) > 2 else parts
    return " ".join(parts).replace(" and ", " & ")


def find_matching_themes(context_line: str, themes: list[Theme]) -> list[str]:
    lowered = context_line.lower()
    matched = []
    for theme in themes:
        for keyword in theme.keywords:
            if keyword.lower() in lowered:
                matched.append(theme.name)
                break
    return matched


def extract_quotes_from_file(file_path: str | Path, themes: list[Theme]) -> list[QuoteMatch]:
    file_path = Path(file_path)
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    speaker = derive_speaker(file_path, lines)

    matches: list[QuoteMatch] = []
    for line in lines:
        if not line.strip() or not is_bullet_line(line):
            continue
        for m in QUOTE_PATTERN.finditer(line):
            quote_text = m.group(1) if m.group(1) is not None else m.group(2)
            matched_themes = find_matching_themes(line, themes)
            if matched_themes:
                matches.append(
                    QuoteMatch(
                        quote=quote_text,
                        speaker=speaker,
                        source_file=file_path.name,
                        themes=matched_themes,
                    )
                )
    return matches


def extract_all(interviews_dir: str | Path, themes: list[Theme]) -> list[QuoteMatch]:
    interviews_dir = Path(interviews_dir)
    all_matches: list[QuoteMatch] = []
    for file_path in sorted(interviews_dir.glob("*.txt")):
        all_matches.extend(extract_quotes_from_file(file_path, themes))
    return all_matches

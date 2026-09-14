#!/usr/bin/env python3
"""CLI entry point: run the full GNP Evidence Pipeline end-to-end.

    python main.py

Reads interviews/*.txt and themes.json, extracts quoted evidence,
verifies every quote word-for-word against its source file, and writes
docs/ (the publishable static site) and output/ (a plain-text report).
No network access, no API keys, standard library only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import extract
import render
import verify


def run(interviews_dir: str, themes_path: str, docs_dir: str, output_dir: str) -> None:
    themes = extract.load_themes(themes_path)
    if not themes:
        print(f"warning: no themes found in {themes_path}", file=sys.stderr)

    matches = extract.extract_all(interviews_dir, themes)
    results = verify.verify_all(matches, interviews_dir)
    render.render_all(themes, results, docs_dir, output_dir)

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    print(f"{total} quotes extracted · {passed} verified word-for-word · {failed} failures")
    print(f"Wrote {docs_dir}/index.html, {docs_dir}/verification.html, {docs_dir}/quotes.json, {docs_dir}/search.js")
    print(f"Wrote {output_dir}/verification_report.txt")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the GNP Evidence Pipeline end-to-end.")
    parser.add_argument("--interviews", default="interviews", help="Directory of interview .txt files")
    parser.add_argument("--themes", default="themes.json", help="Path to the theme/keyword config")
    parser.add_argument("--docs", default="docs", help="Output directory for the static site")
    parser.add_argument("--output", default="output", help="Output directory for plain-text reports")
    args = parser.parse_args()

    run(args.interviews, args.themes, args.docs, args.output)


if __name__ == "__main__":
    main()

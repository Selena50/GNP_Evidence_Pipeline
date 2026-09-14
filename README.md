# GNP Evidence Pipeline

A small, offline pipeline that turns five interview transcripts into a themed
evidence matrix, a verbatim-verification report, and a keyword-based Q&A
search — all static output, no external API calls, no dependencies beyond
the Python standard library.

## Run it

```
python main.py
```

This reads `interviews/*.txt` and `themes.json`, extracts every quoted
substring from the transcripts, checks each one against every theme's
keyword list, independently re-verifies every extracted quote word-for-word
against its cited source file, and regenerates `docs/` and `output/` from
scratch.

## How it works

- **`extract.py`** — splits each transcript into bullet lines, pulls out
  text already wrapped in quotation marks (straight or curly), and matches
  each quote against the keyword lists in `themes.json`. Theme identification
  is pure keyword matching — no LLM is called anywhere in this pipeline.
- **`verify.py`** — independently re-checks every extracted quote against its
  source file: normalize smart quotes and whitespace on both sides, then
  require exact substring containment. No fuzzy matching.
- **`render.py`** — writes `docs/index.html` (evidence matrix + Q&A search),
  `docs/verification.html`, `docs/quotes.json`, `docs/search.js`, and
  `output/verification_report.txt`, using only quotes that passed
  verification.
- **`main.py`** — CLI entry point that runs the full pipeline end-to-end.

## Tuning themes

Edit `themes.json` — it ships with two placeholder themes so the pipeline
runs out of the box. Each theme has a `name`, `description`, and a list of
`keywords` (case-insensitive substrings). Re-run `python main.py` after
editing; nothing about the themes is hardcoded in the Python code.

## Tests

```
python -m unittest discover -s tests -t .
```

## Publishing

Enable GitHub Pages on this repo pointed at `/docs`, then the evidence
matrix, verification report, and Q&A search are all live at
`https://<username>.github.io/<repo>/` — no API key or setup needed to view
or use the hosted page. To regenerate from scratch, edit `themes.json` and
run `python main.py` — no dependencies to install, no credentials to
configure.

Note: the Q&A search box fetches `quotes.json` via `fetch()`, which most
browsers block under a bare `file://` origin. It works as intended on
GitHub Pages (or any real http/https origin); to check it locally, serve
the `docs/` folder instead of opening the file directly, e.g.
`python -m http.server --directory docs`.

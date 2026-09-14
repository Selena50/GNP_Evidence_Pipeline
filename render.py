"""Renders verified evidence into docs/ (static site) and output/ (plain text)."""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

from extract import Theme
from verify import VerificationResult

SEARCH_JS = r"""// Client-side keyword search over verified quotes. No API calls, no libraries.
// This is deliberately simple keyword/token-overlap scoring, not a language model.

const STOPWORDS = new Set([
  "a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "be", "been",
  "to", "of", "in", "on", "at", "for", "with", "about", "as", "by", "that", "this",
  "it", "we", "our", "you", "your", "do", "does", "did", "how", "what", "who",
  "why", "not", "have", "has", "had", "can", "could", "would", "should", "will",
  "there", "their", "them", "they", "i", "us", "so"
]);

function tokenize(text) {
  return (text.toLowerCase().match(/[a-z0-9']+/g) || []).filter(
    (t) => t.length > 1 && !STOPWORDS.has(t)
  );
}

let QUOTES = [];

async function loadQuotes() {
  const res = await fetch("quotes.json");
  QUOTES = await res.json();
}

function scoreQuote(queryTokens, quote) {
  const quoteTokens = tokenize(quote.quote + " " + quote.themes.join(" "));
  const quoteSet = new Set(quoteTokens);
  let overlap = 0;
  for (const t of queryTokens) {
    if (quoteSet.has(t)) overlap += 1;
  }
  return overlap;
}

function renderResults(results) {
  const container = document.getElementById("qa-results");
  container.innerHTML = "";
  if (results.length === 0) {
    const p = document.createElement("p");
    p.className = "qa-empty";
    p.textContent = "Not in the interviews.";
    container.appendChild(p);
    return;
  }
  for (const { quote, score } of results) {
    const div = document.createElement("div");
    div.className = "qa-result";
    const q = document.createElement("blockquote");
    q.textContent = `"${quote.quote}"`;
    const meta = document.createElement("div");
    meta.className = "qa-meta";
    meta.textContent = `${quote.speaker} — ${quote.source_file} — themes: ${quote.themes.join(", ")} (score ${score})`;
    div.appendChild(q);
    div.appendChild(meta);
    container.appendChild(div);
  }
}

const RELEVANCE_THRESHOLD = 1;
const MAX_RESULTS = 3;

function handleSearch(event) {
  event.preventDefault();
  const input = document.getElementById("qa-input");
  const query = input.value.trim();
  if (!query) return;

  const queryTokens = tokenize(query);
  const scored = QUOTES.map((quote) => ({ quote, score: scoreQuote(queryTokens, quote) }))
    .filter((r) => r.score >= RELEVANCE_THRESHOLD)
    .sort((a, b) => b.score - a.score)
    .slice(0, MAX_RESULTS);

  renderResults(scored);
}

document.addEventListener("DOMContentLoaded", () => {
  loadQuotes();
  const form = document.getElementById("qa-form");
  form.addEventListener("submit", handleSearch);
});
"""

CSS = """
:root {
  color-scheme: light dark;
  --bg: #ffffff;
  --fg: #1a1a1a;
  --muted: #5a5a5a;
  --border: #ddd;
  --accent: #2b5797;
  --pass: #1a7f37;
  --fail: #cf222e;
  --card-bg: #f7f7f8;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #16181c;
    --fg: #e8e8e8;
    --muted: #a0a0a0;
    --border: #3a3d42;
    --accent: #7fb1ff;
    --pass: #4fbf67;
    --fail: #ff6b6b;
    --card-bg: #1f2227;
  }
}
* { box-sizing: border-box; }
body {
  background: var(--bg);
  color: var(--fg);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  margin: 0;
  padding: 0 16px 48px;
  line-height: 1.5;
}
.wrap { max-width: 860px; margin: 0 auto; }
h1 { font-size: 1.6rem; margin-top: 2rem; }
h2 { font-size: 1.3rem; border-bottom: 1px solid var(--border); padding-bottom: 0.3rem; margin-top: 2.5rem; }
h3 { font-size: 1.05rem; margin-bottom: 0.2rem; }
.subtitle { color: var(--muted); margin-top: -0.5rem; }
nav.top-links a { margin-right: 1rem; }
.theme-card {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin: 1.25rem 0;
  background: var(--card-bg);
}
.theme-desc { color: var(--muted); }
.sources-touched { font-size: 0.9rem; color: var(--muted); margin: 0.5rem 0 1rem; }
blockquote {
  margin: 0.5rem 0;
  padding: 0.5rem 0.9rem;
  border-left: 3px solid var(--accent);
  background: var(--bg);
}
.quote-meta { font-size: 0.85rem; color: var(--muted); margin: 0 0 0.75rem; }
.tally {
  font-size: 1.05rem;
  font-weight: 600;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: var(--card-bg);
  display: inline-block;
}
table { border-collapse: collapse; width: 100%; margin-top: 1rem; font-size: 0.9rem; }
th, td { border: 1px solid var(--border); padding: 0.5rem 0.6rem; text-align: left; vertical-align: top; }
th { background: var(--card-bg); }
.status-pass { color: var(--pass); font-weight: 600; }
.status-fail { color: var(--fail); font-weight: 600; }
#qa-form { display: flex; gap: 0.5rem; margin: 1rem 0 0.25rem; flex-wrap: wrap; }
#qa-input { flex: 1 1 280px; padding: 0.5rem 0.7rem; border: 1px solid var(--border); border-radius: 6px; background: var(--bg); color: var(--fg); }
#qa-form button { padding: 0.5rem 1rem; border: 1px solid var(--accent); border-radius: 6px; background: var(--accent); color: #fff; cursor: pointer; }
.qa-caption { font-size: 0.85rem; color: var(--muted); margin-top: 0; }
.qa-empty { color: var(--muted); font-style: italic; }
.qa-result { margin-bottom: 1rem; }
.qa-meta { font-size: 0.85rem; color: var(--muted); }
footer { color: var(--muted); font-size: 0.8rem; margin-top: 3rem; }
code { background: var(--card-bg); padding: 0.1rem 0.3rem; border-radius: 4px; }
"""


def _theme_sources(theme_name: str, results: list[VerificationResult]) -> list[str]:
    sources = sorted({r.source_file for r in results if theme_name in r.themes})
    return sources


def render_index_html(themes: list[Theme], verified: list[VerificationResult]) -> str:
    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>GNP Evidence Pipeline</title>",
        f"<style>{CSS}</style>",
        "</head>",
        "<body>",
        '<div class="wrap">',
        "<h1>GNP Evidence Pipeline</h1>",
        '<p class="subtitle">Themed evidence matrix, built from verbatim bullet lines pulled directly out of the interview transcripts. No LLM was used to identify themes: matching is a deterministic keyword lookup against <code>themes.json</code>.</p>',
        '<nav class="top-links"><a href="verification.html">Verification report</a> · <a href="quotes.json">quotes.json</a></nav>',
    ]

    for theme in themes:
        theme_quotes = [r for r in verified if theme.name in r.themes]
        sources = _theme_sources(theme.name, verified)
        parts.append('<div class="theme-card">')
        parts.append(f"<h2>{escape(theme.name)}</h2>")
        parts.append(f'<p class="theme-desc">{escape(theme.description)}</p>')
        if sources:
            parts.append(
                f'<p class="sources-touched">Interviews touching this theme ({len(sources)}): {escape(", ".join(sources))}</p>'
            )
        else:
            parts.append('<p class="sources-touched">No verified quotes matched this theme yet.</p>')
        for r in theme_quotes:
            parts.append(f'<blockquote>&ldquo;{escape(r.quote)}&rdquo;</blockquote>')
            other_themes = [t for t in r.themes if t != theme.name]
            other_note = f" (also: {escape(', '.join(other_themes))})" if other_themes else ""
            parts.append(
                f'<p class="quote-meta">&mdash; {escape(r.speaker)}, <code>{escape(r.source_file)}</code>{other_note}</p>'
            )
        parts.append("</div>")

    parts.append("<h2>Ask a question</h2>")
    parts.append(
        '<p class="qa-caption">This is keyword-based retrieval over the verified quotes below &mdash; not a language model. It scores shared words between your question and each quote, and shows the best match(es), or says so when nothing clears the bar.</p>'
    )
    parts.append(
        '<form id="qa-form"><input id="qa-input" type="text" placeholder="e.g. Why are decisions slow?" autocomplete="off"><button type="submit">Search</button></form>'
    )
    parts.append('<div id="qa-results"></div>')
    parts.append('<script src="search.js"></script>')

    parts.append("<footer>Generated by <code>python main.py</code> from <code>interviews/</code> and <code>themes.json</code>. See <code>verification.html</code> for the pass/fail proof behind every quote above.</footer>")
    parts.append("</div></body></html>")
    return "\n".join(parts)


def render_verification_html(all_results: list[VerificationResult]) -> str:
    total = len(all_results)
    passed = sum(1 for r in all_results if r.passed)
    failed = total - passed
    tally = f"{total} quotes extracted · {passed} verified word-for-word · {failed} failures"

    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Verification Report</title>",
        f"<style>{CSS}</style>",
        "</head>",
        "<body>",
        '<div class="wrap">',
        "<h1>Verbatim Verification Report</h1>",
        '<nav class="top-links"><a href="index.html">&larr; Evidence matrix</a></nav>',
        '<p>Every quote extracted from the interviews is re-checked here, independently of the extraction step, by looking it up as a literal substring of its cited source file (after normalizing smart quotes and whitespace &mdash; no fuzzy matching).</p>',
        f'<p class="tally">{tally}</p>',
    ]

    if failed:
        parts.append("<h2>Failures</h2>")
        parts.append("<p>These quotes did not verify and were excluded from the evidence matrix.</p>")
        parts.append("<table><tr><th>Quote</th><th>Speaker</th><th>Source</th><th>Status</th></tr>")
        for r in all_results:
            if not r.passed:
                parts.append(
                    f'<tr><td>&ldquo;{escape(r.quote)}&rdquo;</td><td>{escape(r.speaker)}</td>'
                    f'<td>{escape(r.source_file)}</td><td class="status-fail">FAIL</td></tr>'
                )
        parts.append("</table>")

    parts.append("<h2>All results</h2>")
    parts.append("<table><tr><th>Quote</th><th>Speaker</th><th>Source</th><th>Themes</th><th>Status</th></tr>")
    for r in all_results:
        status_cls = "status-pass" if r.passed else "status-fail"
        status_text = "PASS" if r.passed else "FAIL"
        parts.append(
            f'<tr><td>&ldquo;{escape(r.quote)}&rdquo;</td><td>{escape(r.speaker)}</td>'
            f'<td>{escape(r.source_file)}</td><td>{escape(", ".join(r.themes))}</td>'
            f'<td class="{status_cls}">{status_text}</td></tr>'
        )
    parts.append("</table>")
    parts.append("</div></body></html>")
    return "\n".join(parts)


def render_verification_txt(all_results: list[VerificationResult]) -> str:
    total = len(all_results)
    passed = sum(1 for r in all_results if r.passed)
    failed = total - passed
    tally = f"{total} quotes extracted · {passed} verified word-for-word · {failed} failures"

    lines = ["GNP Evidence Pipeline — Verbatim Verification Report", "=" * 55, "", tally, ""]
    if failed:
        lines.append("FAILURES")
        lines.append("-" * 8)
        for r in all_results:
            if not r.passed:
                lines.append(f'FAIL: "{r.quote}"  [{r.speaker} — {r.source_file}]')
        lines.append("")

    lines.append("ALL RESULTS")
    lines.append("-" * 11)
    for r in all_results:
        status = "PASS" if r.passed else "FAIL"
        themes = ", ".join(r.themes)
        lines.append(f'{status}: "{r.quote}"  [{r.speaker} — {r.source_file}] themes: {themes}')

    return "\n".join(lines) + "\n"


def render_quotes_json(verified: list[VerificationResult]) -> str:
    data = [
        {
            "quote": r.quote,
            "speaker": r.speaker,
            "source_file": r.source_file,
            "themes": r.themes,
        }
        for r in verified
    ]
    return json.dumps(data, indent=2, ensure_ascii=False)


def render_all(
    themes: list[Theme],
    all_results: list[VerificationResult],
    docs_dir: str | Path,
    output_dir: str | Path,
) -> None:
    docs_dir = Path(docs_dir)
    output_dir = Path(output_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    verified = [r for r in all_results if r.passed]

    (docs_dir / "index.html").write_text(render_index_html(themes, verified), encoding="utf-8")
    (docs_dir / "verification.html").write_text(render_verification_html(all_results), encoding="utf-8")
    (docs_dir / "quotes.json").write_text(render_quotes_json(verified), encoding="utf-8")
    (docs_dir / "search.js").write_text(SEARCH_JS, encoding="utf-8")
    (output_dir / "verification_report.txt").write_text(render_verification_txt(all_results), encoding="utf-8")

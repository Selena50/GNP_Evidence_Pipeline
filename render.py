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
  --ink: #222222;        /* Mine Shaft — default text color everywhere */
  --ink-soft: rgba(34, 34, 34, 0.62);
  --accent: #1D9ACC;      /* Curious Blue — links, focus states, labels, small highlights */
  --tint: #8ED1FC;        /* Malibu — background tints and hover states only, never text */
  --tint-soft: rgba(142, 209, 252, 0.35);
  --bg: #FFFFFF;
  --hairline: rgba(34, 34, 34, 0.12);
}
* { box-sizing: border-box; }
html { color-scheme: light; }
body {
  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  margin: 0;
  padding: 0 24px 64px;
  line-height: 1.6;
  font-size: 16px;
}
.wrap { max-width: 720px; margin: 0 auto; }

a { color: var(--accent); }
a:hover { color: var(--accent); text-decoration-thickness: 2px; }

.site-header { margin-top: 3rem; padding-bottom: 2rem; }
h1 { font-size: 2rem; font-weight: 700; margin: 0; }
.subtitle { color: var(--ink-soft); margin-top: 0.75rem; font-size: 1rem; }

nav.top-links { margin-bottom: 2.5rem; font-size: 1rem; }
nav.top-links a { margin-right: 1.5rem; text-decoration: none; }
nav.top-links a:hover { text-decoration: underline; }

.kicker {
  display: block;
  color: var(--accent);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.theme { margin: 4rem 0; }
nav.top-links + .theme { margin-top: 0; }
h2 { font-size: 1.25rem; font-weight: 700; margin: 0 0 0.6rem; }
.theme-desc { color: var(--ink-soft); font-size: 1rem; margin: 0 0 1rem; }
.sources-touched { font-size: 1rem; margin: 0 0 1.75rem; }
.sources-touched .count { color: var(--accent); font-weight: 700; }

details.theme { margin: 3rem 0; }
details.theme > summary {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  cursor: pointer;
  list-style: none;
}
details.theme > summary::-webkit-details-marker { display: none; }
details.theme > summary::marker { content: ""; }
details.theme > summary:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 4px;
  border-radius: 4px;
}
details.theme .theme-summary-text h2 { margin: 0 0 0.4rem; }
details.theme .theme-summary-text .theme-desc { margin: 0; }
details.theme .chevron {
  flex: 0 0 auto;
  color: var(--accent);
  font-size: 1.1rem;
  line-height: 1.6;
  margin-top: 0.1rem;
  transition: transform 0.15s ease;
}
details.theme[open] .chevron { transform: rotate(180deg); }
details.theme .theme-body { margin-top: 1.5rem; }

.quote-block {
  background: var(--tint);
  border-radius: 6px;
  padding: 1rem 1.25rem;
  margin: 0 0 1.75rem;
}
.quote-block blockquote {
  margin: 0 0 0.6rem;
  padding: 0;
  font-size: 1rem;
  color: var(--ink);
}
.quote-meta { font-size: 0.9rem; color: var(--ink-soft); margin: 0; }
.quote-meta .tag {
  color: var(--accent);
  font-weight: 600;
}

.tally {
  font-size: 1.1rem;
  padding: 1rem 1.25rem;
  border-radius: 6px;
  background: var(--tint);
  display: inline-block;
  margin: 1.5rem 0 2.5rem;
}
.tally .num { color: var(--accent); font-weight: 700; }

.table-wrap { overflow-x: auto; margin: 1rem 0 3rem; }
table { border-collapse: collapse; width: 100%; font-size: 0.95rem; }
th, td { padding: 0.6rem 0.7rem; text-align: left; vertical-align: top; border-bottom: 1px solid var(--hairline); }
td.src { overflow-wrap: anywhere; }
th {
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.status-pass { color: var(--accent); font-weight: 700; }
.status-fail { color: var(--ink); font-weight: 700; background: var(--tint); border-radius: 4px; padding: 0.15rem 0.5rem; }

#qa-form { display: flex; gap: 0.75rem; margin: 1.5rem 0 0.5rem; flex-wrap: wrap; }
#qa-input {
  flex: 1 1 280px;
  padding: 0.6rem 0.8rem;
  border: 1.5px solid var(--hairline);
  border-radius: 6px;
  background: var(--bg);
  color: var(--ink);
  font-size: 1rem;
}
#qa-input:focus { outline: 2px solid var(--accent); outline-offset: 1px; border-color: var(--accent); }
#qa-form button {
  padding: 0.6rem 1.25rem;
  border: 1.5px solid var(--accent);
  border-radius: 6px;
  background: var(--bg);
  color: var(--accent);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}
#qa-form button:hover { background: var(--tint-soft); }
#qa-form button:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.qa-caption { font-size: 0.9rem; color: var(--ink-soft); margin: 0.5rem 0 0; }
.qa-empty { color: var(--ink-soft); font-style: italic; }
.qa-result {
  background: var(--tint);
  border-radius: 6px;
  padding: 1rem 1.25rem;
  margin: 1rem 0;
}
.qa-result blockquote { margin: 0 0 0.6rem; padding: 0; }
.qa-meta { font-size: 0.9rem; color: var(--ink-soft); }

footer { color: var(--ink-soft); font-size: 0.9rem; margin-top: 4rem; }
.quotes-link { display: block; color: var(--bg); text-decoration: none; margin-top: 1rem; font-size: 0.75rem; }
code { background: var(--tint-soft); padding: 0.1rem 0.35rem; border-radius: 4px; font-size: 0.9em; }
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
        '<header class="site-header">',
        "<h1>GNP Evidence Pipeline</h1>",
        '<p class="subtitle">Themed evidence matrix, built from verbatim bullet lines pulled directly out of the interview transcripts. No LLM was used to identify themes: matching is a deterministic keyword lookup against <code>themes.json</code>.</p>',
        "</header>",
        '<nav class="top-links"><a href="verification.html">Verification report</a></nav>',
    ]

    parts.append('<section class="theme qa-section">')
    parts.append('<span class="kicker">Ask a question</span>')
    parts.append("<h2>Search the verified quotes</h2>")
    parts.append(
        '<p class="qa-caption">This is keyword-based retrieval over the verified quotes below &mdash; not a language model. It scores shared words between your question and each quote, and shows the best match(es), or says so when nothing clears the bar.</p>'
    )
    parts.append(
        '<form id="qa-form"><input id="qa-input" type="text" placeholder="e.g. Why are decisions slow?" autocomplete="off"><button type="submit">Search</button></form>'
    )
    parts.append('<div id="qa-results"></div>')
    parts.append('<script src="search.js"></script>')
    parts.append("</section>")

    for i, theme in enumerate(themes, start=1):
        theme_quotes = [r for r in verified if theme.name in r.themes]
        sources = _theme_sources(theme.name, verified)
        parts.append('<details class="theme">')
        parts.append('<summary>')
        parts.append('<span class="theme-summary-text">')
        parts.append(f'<span class="kicker">Theme {i}</span>')
        parts.append(f"<h2>{escape(theme.name)}</h2>")
        parts.append(f'<p class="theme-desc">{escape(theme.description)}</p>')
        parts.append("</span>")
        parts.append('<span class="chevron" aria-hidden="true">&#9662;</span>')
        parts.append("</summary>")
        parts.append('<div class="theme-body">')
        if sources:
            parts.append(
                f'<p class="sources-touched">Interviews touching this theme: '
                f'<span class="count">{len(sources)}</span> &mdash; {escape(", ".join(sources))}</p>'
            )
        else:
            parts.append('<p class="sources-touched">No verified quotes matched this theme yet.</p>')
        for r in theme_quotes:
            parts.append('<div class="quote-block">')
            parts.append(f'<blockquote>&ldquo;{escape(r.quote)}&rdquo;</blockquote>')
            other_themes = [t for t in r.themes if t != theme.name]
            other_note = f' <span class="tag">also: {escape(", ".join(other_themes))}</span>' if other_themes else ""
            parts.append(
                f'<p class="quote-meta">&mdash; {escape(r.speaker)}, <code>{escape(r.source_file)}</code>{other_note}</p>'
            )
            parts.append("</div>")
        parts.append("</div>")
        parts.append("</details>")

    parts.append("<footer>Generated by <code>python main.py</code> from <code>interviews/</code> and <code>themes.json</code>. See <code>verification.html</code> for the pass/fail proof behind every quote above.</footer>")
    parts.append('<a href="quotes.json" class="quotes-link">quotes.json</a>')
    parts.append("</div></body></html>")
    return "\n".join(parts)


def render_verification_html(all_results: list[VerificationResult]) -> str:
    total = len(all_results)
    passed = sum(1 for r in all_results if r.passed)
    failed = total - passed
    tally = (
        f'<span class="num">{total}</span> quotes extracted &middot; '
        f'<span class="num">{passed}</span> verified word-for-word &middot; '
        f'<span class="num">{failed}</span> failures'
    )

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
        '<header class="site-header">',
        "<h1>Verbatim Verification Report</h1>",
        '<p class="subtitle">Every quote extracted from the interviews is re-checked here, independently of the extraction step, by looking it up as a literal substring of its cited source file (after normalizing smart quotes and whitespace &mdash; no fuzzy matching).</p>',
        "</header>",
        '<nav class="top-links"><a href="index.html">&larr; Evidence matrix</a></nav>',
        f'<p class="tally">{tally}</p>',
    ]

    if failed:
        parts.append('<section class="theme">')
        parts.append('<span class="kicker">Failures</span>')
        parts.append("<h2>Excluded from the evidence matrix</h2>")
        parts.append(
            '<div class="table-wrap"><table>'
            '<colgroup><col style="width:46%"><col style="width:18%"><col style="width:26%"><col style="width:10%"></colgroup>'
            '<tr><th>Quote</th><th>Speaker</th><th>Source</th><th>Status</th></tr>'
        )
        for r in all_results:
            if not r.passed:
                parts.append(
                    f'<tr><td>&ldquo;{escape(r.quote)}&rdquo;</td><td>{escape(r.speaker)}</td>'
                    f'<td class="src">{escape(r.source_file)}</td><td class="status-fail">FAIL</td></tr>'
                )
        parts.append("</table></div>")
        parts.append("</section>")

    parts.append('<section class="theme">')
    parts.append('<span class="kicker">All results</span>')
    parts.append("<h2>Every extracted quote</h2>")
    parts.append(
        '<div class="table-wrap"><table>'
        '<colgroup><col style="width:34%"><col style="width:14%"><col style="width:19%"><col style="width:23%"><col style="width:10%"></colgroup>'
        '<tr><th>Quote</th><th>Speaker</th><th>Source</th><th>Themes</th><th>Status</th></tr>'
    )
    for r in all_results:
        status_cls = "status-pass" if r.passed else "status-fail"
        status_text = "PASS" if r.passed else "FAIL"
        parts.append(
            f'<tr><td>&ldquo;{escape(r.quote)}&rdquo;</td><td>{escape(r.speaker)}</td>'
            f'<td class="src">{escape(r.source_file)}</td><td>{escape(", ".join(r.themes))}</td>'
            f'<td class="{status_cls}">{status_text}</td></tr>'
        )
    parts.append("</table></div>")
    parts.append("</section>")
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

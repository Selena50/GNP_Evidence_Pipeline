// Client-side keyword search over verified quotes. No API calls, no libraries.
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

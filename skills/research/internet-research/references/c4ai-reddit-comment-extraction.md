# C4AI Reddit Comment Extraction

Full working example from a real session. Adapt the regex patterns and HTML parsing for your specific subreddit and thread.

## Full Resilience Chain

When ALL search tools are down (no Firecrawl, no XAI credits, no Brave/SearXNG):

1. `mcp_c4ai_md(url=..., filter=fit)` — quick check if markdown suffices
2. `mcp_c4ai_crawl(urls=[...])` — full HTML crawl (content saved to `/tmp/hermes-results/call_xxx.txt`)
3. `execute_code` with regex extraction from the double-JSON-wrapped HTML

## Working Script (Extract Comments from Login-Walled Thread)

```python
import re, json
from hermes_tools import mcp_c4ai_crawl, read_file, mcp_c4ai_md

# === OPTION A: Thread listing page (no login wall) ===
result = mcp_c4ai_md(
    url="https://old.reddit.com/r/subreddit/comments/?sort=new&t=month"
)
# Returns post titles, authors, scores in markdown

# === OPTION B: Get thread content (login-walled on browser) ===
result = mcp_c4ai_crawl(
    urls=["https://old.reddit.com/r/subreddit/comments/thread_id/?sort=top"]
)
# The result path is logged by the tool — use read_file to access it

# === OPTION C: Extract comments from the persisted HTML ===
raw = read_file(path="/tmp/hermes-results/call_xxx.txt", limit=10)
outer = json.loads(raw["content"])
inner = json.loads(outer["result"])
html = inner["results"][0]["html"]

# Find all usertext-body divs (= Reddit comment bodies)
usertexts = list(re.finditer(
    r'<div class="usertext-body may-blank-within md-container ">', html
))

for i, m in enumerate(usertexts):
    start = m.end()
    md_start = html.find('<div class="md">', start)
    if md_start != -1 and md_start < start + 800:
        md_end = html.find('</div>', md_start)
        if md_end != -1:
            # Author (look backwards from current position)
            before = html[max(0, m.start()-1200):m.start()]
            author_match = re.search(
                r'<a[^>]*class="author"[^>]*>([^<]+)</a>', before
            )
            author = author_match.group(1) if author_match else "unknown"

            # Score
            score_match = re.search(
                r'<span[^>]*class="score[^"]*"[^>]*>([^<]+)</span>', before
            )
            score = score_match.group(1) if score_match else "?"

            # Clean the comment text
            content = html[md_start:md_end+6]
            text = re.sub(r'<[^>]+>', '', content)
            text = text.replace('&#x200B;', '').replace('&amp;', '&')
            text = text.replace('&lt;', '<').replace('&gt;', '>')
            text = re.sub(r'\s+', ' ', text).strip()

            if text and len(text) > 5:
                print(f"--- {author} ({score}) ---")
                print(text)
                print()
```

## Key Details

- **Double-JSON wrapper**: C4AI crawl wraps HTML as `{"result": "{\"success\": true, \"results\": [{\"html\": \"...\"}]}"}`. Must parse twice.
- **First div.usertext-body** is the subreddit sidebar — skip this in threaded view.
- **Author/score regex** looks backwards from the usertext div for the `<a class="author">` and `<span class="score...">` tags.
- **old.reddit.com** is critical — new Reddit blocks with Cloudflare even on C4AI crawl.
- **C4AI `md` filter=fit** on thread pages shows sidebar only (because comments require login). Use `crawl` for full HTML instead.

## When This Works vs When It Doesn't

| Works | Doesn't work |
|-------|--------------|
| Old Reddit (old.reddit.com) | New Reddit (www.reddit.com) |
| Pages behind login walls (comments) | Sites behind Cloudflare/anti-bot |
| Static forum HTML | JS-rendered content |
| Medium, Wikipedia, static blogs | Twitter/X, YouTube |
| GitHub raw markdown | CAPTCHA-gated pages |

#!/usr/bin/env python3
"""Build index.html for The AI Brief from Google News RSS.

Free, no API key required. Pulls a handful of topical searches, tags each
result by bucket, and renders the cards into template.html.

Usage:
    python build.py            # live fetch from Google News
    python build.py --sample   # render from built-in sample data (offline)

Run automatically every day by .github/workflows/refresh.yml.
"""
import sys
import re
import html
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "template.html"
OUTPUT = ROOT / "index.html"

TAG_LABELS = {
    "deals": "Big 4 deals",
    "regulatory": "Regulatory",
    "workflow": "Workflow tools",
    "competitive": "Competitive",
    "models": "Model releases",
}

# (bucket, Google News query). `when:14d` limits results to the last two weeks.
QUERIES = [
    ("deals",
     '("Big Four" OR EY OR Deloitte OR PwC OR KPMG) (Anthropic OR OpenAI OR "AI alliance" OR "AI partnership" OR "AI deal") when:14d'),
    ("regulatory",
     '("AI Act" OR PCAOB OR SEC OR "AI regulation" OR "AI governance") (audit OR tax OR accounting OR "professional services") when:14d'),
    ("workflow",
     '(agentic OR "AI agent" OR "AI tool" OR copilot) (tax OR audit OR accounting) (EY OR Deloitte OR PwC OR KPMG OR "Thomson Reuters") when:14d'),
    ("competitive",
     '("Big Four" OR "Big 4") AI (jobs OR hiring OR layoffs OR consulting OR restructuring) when:14d'),
    ("models",
     '(Anthropic OR OpenAI OR Claude OR "GPT-5") (enterprise OR launch OR model OR release) (consulting OR "professional services" OR tax OR audit) when:14d'),
]

PER_BUCKET = 2      # max cards taken from each query bucket
TOTAL_CAP = 9       # max cards rendered on the page
MAX_AGE_DAYS = 14   # drop anything older than this
UA = "Mozilla/5.0 (compatible; AIBriefBot/1.0)"


def fetch(query):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def parse_date(s):
    if not s:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            dt = datetime.datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def clean_text(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def norm(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def parse_items(xml_bytes, bucket):
    root = ET.fromstring(xml_bytes)
    out = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        src_el = item.find("source")
        source = src_el.text.strip() if (src_el is not None and src_el.text) else ""
        desc = clean_text(item.findtext("description"))
        if source and title.endswith(" - " + source):
            title = title[:-(len(source) + 3)].strip()
        elif " - " in title:
            head, tail = title.rsplit(" - ", 1)
            if not source:
                source = tail.strip()
            title = head.strip()
        if not title or not link:
            continue
        out.append({
            "bucket": bucket,
            "tag_label": TAG_LABELS[bucket],
            "title": title,
            "link": link,
            "source": source or "News",
            "date": parse_date(item.findtext("pubDate")),
            "summary": desc,
        })
    return out


def gather_live():
    items = []
    now = datetime.datetime.now(datetime.timezone.utc)
    for bucket, q in QUERIES:
        try:
            got = parse_items(fetch(q), bucket)
        except Exception as e:  # noqa: BLE001 - never let one bucket break the run
            print(f"[warn] {bucket}: {e}", file=sys.stderr)
            got = []
        kept = []
        for it in got:
            d = it["date"]
            if d is not None and (now - d).days > MAX_AGE_DAYS:
                continue
            kept.append(it)
            if len(kept) >= PER_BUCKET:
                break
        items.extend(kept)
        print(f"[info] {bucket}: {len(kept)} kept")
    return items


def dedupe_sort_cap(items):
    seen, out = set(), []
    for it in items:
        k = norm(it["title"])
        if k and k not in seen:
            seen.add(k)
            out.append(it)
    floor = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    out.sort(key=lambda x: x["date"] or floor, reverse=True)
    return out[:TOTAL_CAP]


def fmt_date(dt):
    if not dt:
        return ""
    try:
        return dt.strftime("%-d %b")
    except ValueError:
        return dt.strftime("%d %b").lstrip("0")


def render_card(it):
    b = it["bucket"]
    summary = it["summary"]
    if len(summary) < 50 or norm(summary).startswith(norm(it["title"])[:40]):
        summary = f"Reported by {it['source']}. Open the source for the full story."
    lines = [
        f'    <article class="story {b}" data-tag="{b}">',
        '      <div class="story-meta">',
        f'        <span class="tag {b}">{html.escape(it["tag_label"])}</span>',
        f'        <span class="source">{html.escape(it["source"])}</span>',
    ]
    d = fmt_date(it["date"])
    if d:
        lines += ['        <span class="dot">&middot;</span>', f'        <span>{d}</span>']
    lines += [
        '      </div>',
        f'      <h2>{html.escape(it["title"])}</h2>',
        f'      <p>{html.escape(summary)}</p>',
        f'      <a class="read" href="{html.escape(it["link"])}" target="_blank" rel="noopener">Read source <span class="arr">&rarr;</span></a>',
        '    </article>',
    ]
    return "\n".join(lines)


def _dt(days_ago):
    return datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_ago)


SAMPLE = [
    {"bucket": "deals", "tag_label": "Big 4 deals",
     "title": "KPMG and Anthropic sign a global AI alliance for 276,000 staff",
     "link": "https://example.com/kpmg-anthropic", "source": "International Tax Review",
     "date": _dt(2), "summary": "KPMG is embedding Claude into its Digital Gateway platform, with the rollout aimed first at tax clients and private equity."},
    {"bucket": "deals", "tag_label": "Big 4 deals",
     "title": "PwC deepens its Anthropic alliance, will certify 30,000 staff on Claude",
     "link": "https://example.com/pwc-anthropic", "source": "PwC",
     "date": _dt(7), "summary": "PwC is rolling out Claude Code and Cowork from US teams toward a global workforce and standing up a joint Center of Excellence."},
    {"bucket": "regulatory", "tag_label": "Regulatory",
     "title": "EU agrees a 'Digital Omnibus' pushing high-risk AI Act duties to 2027",
     "link": "https://example.com/eu-ai-act", "source": "European Council",
     "date": _dt(14), "summary": "The first amendments to the AI Act since 2024 move high-risk obligations from August 2026 to December 2027."},
    {"bucket": "competitive", "tag_label": "Competitive",
     "title": "Big Four now post more job ads for AI specialists than for auditors",
     "link": "https://example.com/big4-ai-jobs", "source": "The Irish Times",
     "date": _dt(2), "summary": "AI-skilled roles made up almost 7% of Big Four job postings last year, more than triple the 2022 share."},
    {"bucket": "regulatory", "tag_label": "Regulatory",
     "title": "Audit regulator pressed to redesign oversight as AI tops PCAOB letters",
     "link": "https://example.com/pcaob-ai", "source": "Bloomberg Tax",
     "date": _dt(2), "summary": "Comment letters urge the PCAOB to issue consistent guidance on AI-assisted audit evidence; a strategy is expected by June."},
    {"bucket": "workflow", "tag_label": "Workflow tools",
     "title": "EY rolls out up to 150 agentic-AI agents to 80,000 tax professionals",
     "link": "https://example.com/ey-agents", "source": "Bloomberg Tax",
     "date": _dt(5), "summary": "Each purpose-built agent owns a narrow task such as statutory research or compliance-document analysis."},
]


def main():
    items = SAMPLE if "--sample" in sys.argv else gather_live()
    items = dedupe_sort_cap(items)
    if not items:
        print("[error] no items gathered; leaving existing index.html untouched", file=sys.stderr)
        return 1
    cards = "\n\n".join(render_card(it) for it in items)
    stamp = fmt_date(datetime.datetime.now(datetime.timezone.utc))
    year = datetime.datetime.now(datetime.timezone.utc).year
    note = f"Auto-refreshed {stamp} {year} &middot; sources via Google News &middot; {len(items)} stories."
    out = (TEMPLATE.read_text(encoding="utf-8")
           .replace("<!--CARDS-->", cards)
           .replace("<!--UPDATED-->", note))
    OUTPUT.write_text(out, encoding="utf-8")
    print(f"[ok] wrote {OUTPUT} with {len(items)} cards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

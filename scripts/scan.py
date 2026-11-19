#!/usr/bin/env python3
"""phd-hunter scanner: sweep European academic job boards for PhD positions and prefilter them.

    python3 scripts/scan.py                 # all sources, all queries
    python3 scripts/scan.py --source euraxess --query "agentic AI"
    python3 scripts/scan.py --rescore       # reapply config/search.json weights, no network

Standard library only. Pages are fetched with curl, read-only. Results are
merged into data/postings.json; nothing is ever applied to or sent.
The prefilter score (0-100) is a keyword heuristic that decides what is worth
a proper evaluation. It is not the fit score: /evaluate and /rank produce that.
"""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import html
import json
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "search.json"
STORE = ROOT / "data" / "postings.json"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
TODAY = dt.date.today()
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


# ---------- helpers ----------

def fetch(url, timeout=30, retries=1):
    """GET a page with curl. Retries once after a pause when the body comes back empty."""
    for attempt in range(retries + 1):
        try:
            out = subprocess.run(
                ["curl", "-sL", "--compressed", "-m", str(timeout), "-A", UA, url],
                capture_output=True, timeout=timeout + 5)
            body = out.stdout.decode("utf-8", "ignore")
        except Exception as exc:  # network trouble must not kill the whole scan
            print(f"  ! fetch failed: {url[:80]} ({exc})", file=sys.stderr)
            body = ""
        if len(body) > 2000 or attempt == retries:
            time.sleep(0.4)  # stay polite between requests
            return body
        time.sleep(3)
    return ""


def text(fragment):
    fragment = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", fragment or "", flags=re.S)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip()


def parse_date(raw):
    """Best-effort date parser for the formats the boards use. Returns ISO or ''."""
    if not raw:
        return ""
    raw = raw.strip()
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if m:
        return m.group(0)
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", raw)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3})[a-z]*\.?\s*[’']?(\d{2,4})?", raw)
    if m and m.group(2).lower() in MONTHS:
        day, month = int(m.group(1)), MONTHS[m.group(2).lower()]
        if m.group(3):
            year = int(m.group(3))
            year += 2000 if year < 100 else 0
        else:  # no year given: assume the next occurrence of that date
            year = TODAY.year
            if dt.date(year, month, min(day, 28)) < TODAY - dt.timedelta(days=60):
                year += 1
        try:
            return dt.date(year, month, day).isoformat()
        except ValueError:
            return ""
    return ""


def make_id(source, url):
    return f"{source}-{hashlib.sha1(url.encode()).hexdigest()[:8]}"


def posting(source, url, title, org="", country="", city="", deadline="", posted="",
            summary="", field="", funding=""):
    return {
        "id": make_id(source, url), "source": source, "url": url,
        "title": title.strip(), "org": org.strip(), "country": country.strip(),
        "city": city.strip(), "deadline": deadline, "posted": posted,
        "summary": summary.strip()[:600], "field": field.strip(), "funding": funding.strip(),
    }


# ---------- sources ----------

_euraxess_cache = None


def src_euraxess(query, pages, facets=None):
    """EURAXESS ignores keywords on GET, so walk the newest R1 offers per research-field facet."""
    global _euraxess_cache
    if query != "__all__":
        return []
    if _euraxess_cache is not None:
        return _euraxess_cache
    out = []
    for label, facet in (facets or {"Computer science": "job_research_field%3A78"}).items():
        for page in range(pages):
            url = ("https://euraxess.ec.europa.eu/jobs/search?f%5B0%5D=job_research_profile%3A447"
                   f"&f%5B1%5D={facet}&page={page}")
            cards = fetch(url).split('id="job-teaser-content"')[1:]
            for card in cards:
                m = re.search(r'href="(/jobs/\d+)"[^>]*>(.*?)</a>', card, flags=re.S)
                if not m:
                    continue
                labels = [text(x) for x in re.findall(r'<span\s+class="ecl-label[^"]*"[^>]*>(.*?)</span>', card, flags=re.S)]
                country = next((l for l in labels if l and l.upper() != "JOB"), "")
                org = re.search(r'primary-meta-item">\s*(?:<a[^>]*>)?(.*?)(?:</a>)?\s*</li>', card, flags=re.S)
                posted = re.search(r"Posted on:\s*([^<]+)", card)
                deadline = re.search(r'id-Application-Deadline.*?<time datetime="([^"]+)"', card, flags=re.S)
                field = re.search(r'id-Research-Field.*?ecl-u-flex-column">(.*?)<div class="id-', card, flags=re.S)
                funding = re.search(r'id-Funding-Programme.*?ecl-u-flex-column">(.*?)</div>', card, flags=re.S)
                summary = re.search(r'ecl-content-block__description">(.*?)</div>', card, flags=re.S)
                out.append(posting(
                    "euraxess", "https://euraxess.ec.europa.eu" + m.group(1), text(m.group(2)),
                    org=text(org.group(1)) if org else "", country=country,
                    deadline=parse_date(deadline.group(1)) if deadline else "",
                    posted=parse_date(posted.group(1)) if posted else "",
                    summary=text(summary.group(1)) if summary else "",
                    field=text(field.group(1)) if field else "",
                    funding=text(funding.group(1)) if funding else ""))
            if len(cards) < 10:
                break
    _euraxess_cache = out
    return out


def src_academictransfer(query, pages):
    out = []
    for page in range(1, pages + 1):
        url = f"https://www.academictransfer.com/en/jobs/?q={urllib.parse.quote_plus('phd ' + query)}&page={page}"
        cards = re.findall(r"<article\b.*?</article>", fetch(url), flags=re.S)
        for card in cards:
            m = re.search(r'href="(/en/jobs/\d+/[^"]+)"', card)
            title = re.search(r"<h3[^>]*>(.*?)</h3>", card, flags=re.S)
            if not (m and title):
                continue
            summary = re.search(r"<p[^>]*>(.*?)</p>", card, flags=re.S)
            flat = text(card)
            deadline = re.search(r"Deadline\s+(\d{1,2}\s+\w{3}\s*[’']\d{2})", flat)
            published = re.search(r"Published\s+(\d{1,2}\s+\w{3}\s*[’']\d{2})", flat)
            tail = flat.split(published.group(1))[-1].strip() if published else ""
            # tail looks like "Eindhoven Eindhoven University of Technology (TU/e)"
            pieces = [text(x) for x in re.findall(r">([^<>]{2,})<", card.split("Published")[-1])] if "Published" in card else []
            pieces = [p for p in pieces if p and not re.match(r"^\d{1,2}\s+\w{3}", p) and len(p) < 120]
            city = pieces[0] if len(pieces) > 1 else ""
            org = pieces[-1] if pieces else tail
            out.append(posting(
                "academictransfer", "https://www.academictransfer.com" + m.group(1), text(title.group(1)),
                org=org, country="Netherlands", city=city,
                deadline=parse_date(deadline.group(1)) if deadline else "",
                posted=parse_date(published.group(1)) if published else "",
                summary=text(summary.group(1)) if summary else ""))
        if len(cards) < 10:
            break
    return out


def src_jobsacuk(query, pages):
    out = []
    for page in range(pages):
        url = (f"https://www.jobs.ac.uk/search/?keywords={urllib.parse.quote_plus(query)}"
               f"&jobTypeFacet%5B%5D=phds&startIndex={page * 25 + 1}&pageSize=25")
        cards = fetch(url).split('class="j-search-result__result')[1:]
        for card in cards:
            m = re.search(r'<a href="(/job/[^"]+)"[^>]*>(.*?)</a>', card, flags=re.S)
            if not m:
                continue
            org = re.search(r'j-search-result__employer">(.*?)</div>', card, flags=re.S)
            dept = re.search(r'j-search-result__department">(.*?)</div>', card, flags=re.S)
            loc = re.search(r"Location:\s*([^<]+)", card)
            closes = re.search(r"Closes</span>\s*<span[^>]*>(.*?)</span>", card, flags=re.S)
            placed = re.search(r"Date Placed:\s*</strong>\s*([^<]+)", card)
            info = re.search(r'j-search-result__info">(.*?)</div>', card, flags=re.S)
            out.append(posting(
                "jobsacuk", "https://www.jobs.ac.uk" + m.group(1), text(m.group(2)),
                org=text(org.group(1)) if org else "", country="United Kingdom",
                city=text(loc.group(1)) if loc else "",
                deadline=parse_date(text(closes.group(1))) if closes else "",
                posted=parse_date(placed.group(1)) if placed else "",
                summary=text(info.group(1)) if info else "",
                field=text(dept.group(1)) if dept else ""))
        if len(cards) < 25:
            break
    return out


_jobbnorge_cache = None


def src_jobbnorge(query, pages):
    """The public API ignores free-text search, so pull the feed once and filter locally."""
    global _jobbnorge_cache
    if _jobbnorge_cache is None:
        _jobbnorge_cache, seen = [], set()
        for page in range(1, pages + 1):
            try:
                jobs = json.loads(fetch(f"https://publicapi.jobbnorge.no/v3/Jobs?page={page}") or "{}").get("jobs", [])
            except json.JSONDecodeError:
                jobs = []
            fresh = [j for j in jobs if j.get("id") not in seen]
            if not fresh:
                break
            for j in fresh:
                seen.add(j["id"])
                blob = f"{j.get('title', '')} {(j.get('jobType') or {}).get('name', '')}".lower()
                if not re.search(r"phd|ph\.d|stipendiat|doctoral|doktorgrad", blob):
                    continue
                loc = (j.get("locations") or [{}])[0]
                _jobbnorge_cache.append(posting(
                    "jobbnorge", j.get("link", ""), j.get("title", ""),
                    org=j.get("employer", ""), country="Norway", city=loc.get("area") or "",
                    deadline=parse_date(j.get("deadline", "")), posted=parse_date(j.get("publicationDate", "")),
                    summary=j.get("summary") or "", field=j.get("department") or ""))
    return _jobbnorge_cache if query == "__all__" else []


def src_academics(query, pages):
    out = []
    for page in range(1, pages + 1):
        url = f"https://www.academics.com/jobs?q={urllib.parse.quote_plus('phd ' + query)}&page={page}"
        cards = re.findall(r'<li id="job-teaser-\d+-container">.*?</li>', fetch(url), flags=re.S)
        for card in cards:
            m = re.search(r'href="(/jobs/[^"]+)"\s+title="([^"]+)"', card)
            if not m:
                continue
            org = re.search(r'alt="([^"]+?) - Logo"', card)
            flat = text(card)
            country = next((c for c in ("Germany", "Austria", "Switzerland", "Deutschland", "Österreich", "Schweiz")
                            if c in flat), "Germany")
            country = {"Deutschland": "Germany", "Österreich": "Austria", "Schweiz": "Switzerland"}.get(country, country)
            out.append(posting(
                "academics", "https://www.academics.com" + m.group(1), html.unescape(m.group(2)),
                org=html.unescape(org.group(1)) if org else "", country=country, summary=flat[:400]))
        if len(cards) < 10:
            break
    return out

DOCTORAL = re.compile(r"phd|ph\.d|doctoral|doctorate|doktorand|promotionsstelle|promovier|dissertation", re.I)
_feed_cache = {}


def _feed(name, build):
    """University portals list every vacancy on a page or two: fetch once, keep doctoral posts."""
    if name not in _feed_cache:
        _feed_cache[name] = [p for p in build() if DOCTORAL.search(p["title"] + " " + p["summary"])
                             and not re.search(r"post-?doc", p["title"], re.I)]
    return _feed_cache[name]


def src_ethz(query, pages):
    def build():
        out = []
        for item in fetch("https://jobs.ethz.ch/site/index").split('class="job-ad__item__wrapper"')[1:]:
            m = re.search(r'href="(/job/view/[^"]+)"', item)
            title = re.search(r'job-ad__item__title">(.*?)</h3>', item, flags=re.S)
            if not (m and title):
                continue
            details = re.search(r'job-ad__item__details">(.*?)</div>', item, flags=re.S)
            company = re.search(r'job-ad__item__company">(.*?)</div>', item, flags=re.S)
            details, company = text(details.group(1)) if details else "", text(company.group(1)) if company else ""
            city = details.split(",")[1].strip() if details.count(",") else ""
            out.append(posting("ethz", "https://jobs.ethz.ch" + m.group(1), text(title.group(1)), org="ETH Zürich",
                               country="Switzerland", city=city, posted=parse_date(company),
                               field=company.split("|")[-1].strip(), summary=details))
        return out
    return _feed("ethz", build) if query == "__all__" else []


def src_kth(query, pages):
    def build():
        out = []
        for row in re.findall(r"<tr>\s*<td class=\"job-title\".*?</tr>", fetch("https://www.kth.se/lediga-jobb?l=en"), flags=re.S):
            m = re.search(r'<a href="(/lediga-jobb/\d+[^"]*)">(.*?)</a>', row, flags=re.S)
            if not m:
                continue
            cells = [text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.S)]
            out.append(posting("kth", "https://www.kth.se" + html.unescape(m.group(1)), text(m.group(2)),
                               org="KTH Royal Institute of Technology", country="Sweden",
                               city=cells[1] if len(cells) > 1 else "", field=cells[2] if len(cells) > 2 else "",
                               deadline=parse_date(cells[-1]) if cells else ""))
        return out
    return _feed("kth", build) if query == "__all__" else []


def src_tum(query, pages):
    def build():
        out, base = [], "https://portal.mytum.de/jobs/wissenschaftler/"
        for date, href, title, blurb in re.findall(
                r"<h5>([\d.]+)</h5>\s*<h6>\s*<a href=\"(NewsArticle_[^\"]+)\">(.*?)</a>\s*</h6>(.*?)<a href=\"NewsArticle_",
                fetch(base), flags=re.S):
            out.append(posting("tum", base + href, text(title), org="Technical University of Munich", country="Germany",
                               city="Munich", posted=parse_date(date), summary=text(blurb)))
        return out
    return _feed("tum", build) if query == "__all__" else []


def src_aalto(query, pages):
    def build():
        out = []
        for page in range(pages):
            items = fetch(f"https://www.aalto.fi/en/open-positions?page={page}").split('class="aalto-listing__item-title"')[1:]
            for item in items:
                m = re.search(r'href="(/en/open-positions/[^"]+)">(.*?)</a>', item, flags=re.S)
                closes = re.search(r'Closes on:\s*<time datetime="([^"]+)"', item)
                if m:
                    out.append(posting("aalto", "https://www.aalto.fi" + m.group(1), text(m.group(2)), org="Aalto University",
                                       country="Finland", city="Espoo", deadline=parse_date(closes.group(1)) if closes else ""))
            if len(items) < 10:
                break
        return out
    return _feed("aalto", build) if query == "__all__" else []



SOURCES = {
    "euraxess": src_euraxess,
    "academictransfer": src_academictransfer,
    "jobsacuk": src_jobsacuk,
    "jobbnorge": src_jobbnorge,
    "academics": src_academics,
    "ethz": src_ethz,
    "kth": src_kth,
    "tum": src_tum,
    "aalto": src_aalto,
}
# Sources that are walked once as a whole feed instead of once per query.
FEEDS = {"jobbnorge", "euraxess", "ethz", "kth", "tum", "aalto"}


# ---------- scoring ----------

def prefilter(p, cfg):
    """Keyword score 0-100 plus flags. Cheap triage only."""
    title = p["title"].lower()
    blob = " ".join([p["title"], p["summary"], p["field"]]).lower()
    advert = p.get("ad_digest", "").lower()  # full advert text, read by scripts/enrich.py
    flags, hits = [], []

    is_role = any(re.search(rx, title, flags=re.I) for rx in cfg["role_include"])
    if p["source"] in ("jobsacuk", "jobbnorge", "ethz", "kth", "tum", "aalto", "academicpositions"):
        is_role = True  # these feeds are already limited to doctoral-level offers
    if any(re.search(rx, title, flags=re.I) for rx in cfg["role_exclude"]) and not re.search(r"phd|doctoral", title):
        flags.append("not-phd-role")
    elif not is_role:
        flags.append("role-unclear")

    score = 0
    for tier, spec in cfg["weights"].items():
        seen = 0
        for term in spec["terms"]:
            if term in blob:
                bonus = spec["points"] * (1.5 if term in title and spec["points"] > 0 else 1)
            elif term in advert:
                bonus = spec["points"] * 0.5  # found only in the body: counts half
            else:
                continue
            seen += 1
            if seen <= 4:  # diminishing returns per tier
                score += bonus
                hits.append(term.strip())
    score += cfg["country_bonus"].get(p["country"], 0)

    funding = p.get("funding", "")
    if re.search(r"MSCA|Marie", funding + " " + blob, flags=re.I):
        flags.append("msca")
        if p["country"] in cfg.get("msca_blocked_countries", []):
            flags.append("msca-mobility-rule-blocks")
            score -= 40

    if p["deadline"]:
        days = (dt.date.fromisoformat(p["deadline"]) - TODAY).days
        if days < 0:
            flags.append("expired")
        elif days <= cfg.get("urgent_days", 10):
            flags.append(f"urgent-{days}d")
    else:
        flags.append("no-deadline-listed")

    # Signals read from the full advert by scripts/enrich.py
    signals = p.get("signals", [])
    spoken = {l.lower() for l in cfg.get("candidate_languages", ["English"])}
    if spoken & {"swedish", "norwegian", "danish"}:
        spoken.add("scandinavian")
    for sig in signals:
        if sig.startswith("lang-required:"):
            lang = sig.split(":")[1].lower()
            if lang in spoken:
                continue  # the candidate works in this language: not a gate
            flags.append("gate-language-" + lang)
            score -= 30
        elif sig == "maybe-self-funded":
            flags.append("check-funding")
            score -= 10
    if "msca" in signals and "msca" not in flags:
        flags.append("msca")
        if p["country"] in cfg.get("msca_blocked_countries", []):
            flags.append("msca-mobility-rule-blocks")
            score -= 40

    if "not-phd-role" in flags:
        score = min(score, 5)
    p["prefilter"] = max(0, min(100, round(score)))
    p["flags"] = flags
    p["hits"] = hits[:10]
    return p


def dedup_key(p):
    """Same advert on two boards -> same key. Boards label the employer differently
    ("X University via Board"), so a specific title is compared on its own; a short,
    generic one ("PhD position") also needs the same country and deadline."""
    key = re.sub(r"[^a-z0-9]+", "", p["title"].lower())[:90]
    if len(key) < 40:
        key += "|" + p.get("country", "").lower() + "|" + p.get("deadline", "")
    return key


# ---------- main ----------

def health_check(counts):
    """Warn when a board that used to return results returns none: its page layout probably changed."""
    log_path = ROOT / "data" / "scan_log.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else []
    previous = log[-1]["counts"] if log else {}
    for name, n in counts.items():
        if n == 0:
            was = previous.get(name)
            note = f"returned {was} last time; its parser in scripts/scan.py likely needs fixing" if was else "returned nothing"
            print(f"  ! WARNING {name}: 0 results ({note})", file=sys.stderr)
    log.append({"date": TODAY.isoformat(), "counts": counts})
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(log[-60:], indent=1))


def prune(store, keep_days=30):
    """Drop what will never be looked at again, so the store stays small and fast:
    untouched postings that are not doctoral roles, or whose deadline passed a month ago.
    Anything scored, tracked or dismissed is kept as history."""
    cutoff = (TODAY - dt.timedelta(days=keep_days)).isoformat()
    gone = [pid for pid, p in store.items()
            if p.get("status") in ("new", "seen", "expired") and not p.get("fit")
            and ("not-phd-role" in p.get("flags", []) or (p.get("deadline") and p["deadline"] < cutoff))]
    for pid in gone:
        del store[pid]
    return len(gone)


def load_config():
    """Read config/search.json, or stop with a plain instruction when it is not set up yet."""
    if not CONFIG.exists():
        sys.exit("config/search.json is missing. Run /phd-hunter setup, or copy "
                 "templates/search.example.json to config/search.json and edit it.")
    try:
        return json.loads(CONFIG.read_text())
    except json.JSONDecodeError as exc:
        sys.exit(f"config/search.json is not valid JSON ({exc}). Fix it or copy templates/search.example.json again.")


def load_store():
    if STORE.exists():
        return json.loads(STORE.read_text())
    return {}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", action="append", help="limit to a source (repeatable)")
    ap.add_argument("--query", action="append", help="override the config queries (repeatable)")
    ap.add_argument("--rescore", action="store_true", help="rescore stored postings, no network")
    ap.add_argument("--top", type=int, default=25, help="how many new postings to print")
    args = ap.parse_args()

    cfg = load_config()
    store = load_store()
    found = []

    counts = {}
    if not args.rescore:
        queries = args.query or cfg["queries"]

        def run_source(name):
            spec = cfg["sources"].get(name, {})
            got_all = []
            for q in (["__all__"] if name in FEEDS else queries):
                try:
                    extra = {"facets": spec["facets"]} if name == "euraxess" and spec.get("facets") else {}
                    got = SOURCES[name](q, spec.get("pages", 1), **extra)
                except Exception as exc:  # a broken parser must not stop other sources
                    print(f"  ! {name} / {q}: {exc}", file=sys.stderr)
                    got = []
                for p in got:
                    p["query"] = q
                got_all.extend(got)
            return name, got_all

        wanted = [n for n in SOURCES
                  if (n in args.source if args.source else cfg["sources"].get(n, {}).get("enabled", True))]
        # One thread per board: requests to the same site stay sequential and paced.
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(wanted) or 1) as pool:
            for name, got in pool.map(run_source, wanted):
                counts[name] = len(got)
                found.extend(got)
                print(f"{name:18s} {len(got):4d} raw results", file=sys.stderr)
        health_check(counts)

    seen_keys = {dedup_key(p): pid for pid, p in store.items()}
    new_ids = []
    for p in found:
        key = dedup_key(p)
        if p["id"] in store or key in seen_keys:
            old = store.get(p["id"]) or store[seen_keys[key]]
            for k in ("deadline", "summary", "field", "funding", "org", "country", "city"):
                if p.get(k) and not old.get(k):
                    old[k] = p[k]
            if p["url"] != old["url"] and p["url"] not in old.setdefault("also_on", []):
                old["also_on"].append(p["url"])
            continue
        prefilter(p, cfg)
        if "not-phd-role" in p["flags"] or "expired" in p["flags"]:
            continue  # never worth keeping: postdocs, chairs, closed calls
        p["first_seen"] = TODAY.isoformat()
        p["status"] = "new"
        store[p["id"]] = p
        seen_keys[key] = p["id"]
        new_ids.append(p["id"])

    for p in store.values():
        prefilter(p, cfg)
        if "expired" in p["flags"] and p.get("status") in ("new", "seen"):
            p["status"] = "expired"
    removed = prune(store)

    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(store, indent=1, ensure_ascii=False))

    floor = cfg.get("min_score_to_keep", 15)
    fresh = sorted((store[i] for i in new_ids), key=lambda p: -p["prefilter"])
    keep = [p for p in fresh if p["prefilter"] >= floor and p["status"] == "new"]
    print(f"\n{len(found)} results, {len(new_ids)} new, {len(keep)} above prefilter {floor}. "
          f"Store now holds {len(store)} postings" + (f" ({removed} stale ones removed)" if removed else "") + ".\n")
    pool = keep if not args.rescore else sorted(
        (p for p in store.values() if p["status"] == "new" and p["prefilter"] >= floor), key=lambda p: -p["prefilter"])
    for p in pool[:args.top]:
        flags = " ".join(f"[{f}]" for f in p["flags"])
        print(f"{p['prefilter']:3d}  {p['id']}  {p['title'][:78]}")
        print(f"     {p['org'][:50]} | {p['country']} | deadline {p['deadline'] or '?'} {flags}")
        print(f"     {p['url']}")
    if len(pool) > args.top:
        print(f"\n... {len(pool) - args.top} more: python3 scripts/ops.py postings")


if __name__ == "__main__":
    main()

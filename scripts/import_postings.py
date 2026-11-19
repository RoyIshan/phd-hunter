#!/usr/bin/env python3
"""Import postings collected in the browser pane into data/postings.json.

    python3 scripts/import_postings.py data/inbox/academicpositions.txt

For job boards that block scripts (Academic Positions). The input is the text
returned by scripts/browser/academicpositions.js, one advert per line:

    url-or-path|title|institution|city|country|deadline(YYYY-MM-DD)|summary

A JSON file with a "postings" list of objects using the same field names also
works. Imported postings get the same prefilter score and duplicate check as
scanned ones.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scan  # noqa: E402

BASES = {"academicpositions": "https://academicpositions.com/ad/"}
COUNTRY_FIX = {"The Netherlands": "Netherlands", "UK": "United Kingdom"}


def read(path, source):
    raw = Path(path).read_text(encoding="utf-8").strip()
    if raw.startswith("{") or raw.startswith("["):
        data = json.loads(raw)
        return data["postings"] if isinstance(data, dict) else data
    rows = []
    for line in raw.splitlines():
        parts = [p.strip() for p in line.strip().strip('"').split("|")]
        if len(parts) < 6 or not parts[0]:
            continue
        url = parts[0] if parts[0].startswith("http") else BASES[source] + parts[0]
        rows.append({"url": url, "title": parts[1], "org": parts[2], "city": parts[3],
                     "country": parts[4], "deadline": parts[5], "summary": "|".join(parts[6:])})
    return rows


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    source = sys.argv[2] if len(sys.argv) > 2 else "academicpositions"
    cfg = scan.load_config()
    store = scan.load_store()
    keys = {scan.dedup_key(p): pid for pid, p in store.items()}
    added = merged = 0
    for row in read(sys.argv[1], source):
        p = scan.posting(source, row["url"], row.get("title", ""), org=row.get("org", ""),
                         country=COUNTRY_FIX.get(row.get("country", ""), row.get("country", "")),
                         city=row.get("city", ""), deadline=scan.parse_date(row.get("deadline", "")),
                         summary=row.get("summary", ""), field=row.get("field", ""))
        key = scan.dedup_key(p)
        if p["id"] in store or key in keys:
            old = store.get(p["id"]) or store[keys[key]]
            old.setdefault("also_on", [])
            if p["url"] != old["url"] and p["url"] not in old["also_on"]:
                old["also_on"].append(p["url"])
            for k in ("deadline", "summary", "org", "country", "city"):
                if p.get(k) and not old.get(k):
                    old[k] = p[k]
            merged += 1
            continue
        p["first_seen"], p["status"], p["query"] = scan.TODAY.isoformat(), "new", "browser"
        store[p["id"]] = p
        keys[key] = p["id"]
        added += 1
    for p in store.values():
        scan.prefilter(p, cfg)
    scan.STORE.write_text(json.dumps(store, indent=1, ensure_ascii=False))
    print(f"{added} new, {merged} already known (links merged). Store holds {len(store)} postings.")
    fresh = sorted((p for p in store.values() if p["source"] == source and p["status"] == "new"),
                   key=lambda p: -p["prefilter"])
    for p in fresh[:25]:
        print(f"{p['prefilter']:3d}  {p['id']}  {p['title'][:74]}")
        print(f"     {p['org'][:44]} | {p['country']} | deadline {p['deadline'] or '?'} {' '.join(p['flags'])}")


if __name__ == "__main__":
    main()

# Adding a board

A board is one function in `scripts/scan.py` that returns a list of postings.

## 1. Check that it may be read

Open the listing page with `curl`. If you get a bot check, a login wall or an
empty shell that needs JavaScript, stop: phd-hunter does not work around those.
(A site that loads in a normal browser can get a browser collector instead;
see `scripts/browser/academicpositions.js` and `scripts/collector.py`.)

## 2. Write the source function

```python
def src_myboard(query, pages):
    out = []
    for page in range(1, pages + 1):
        html_text = fetch(f"https://example.org/jobs?q={urllib.parse.quote_plus(query)}&page={page}")
        cards = re.findall(r'<article class="job">.*?</article>', html_text, flags=re.S)
        for card in cards:
            m = re.search(r'href="(/jobs/\d+)"[^>]*>(.*?)</a>', card, flags=re.S)
            if not m:
                continue
            out.append(posting(
                "myboard", "https://example.org" + m.group(1), text(m.group(2)),
                org="...", country="...", city="...",
                deadline=parse_date("..."), posted=parse_date("..."), summary="..."))
        if len(cards) < 10:
            break
    return out
```

Helpers already there: `fetch(url)` (curl, paced, one retry), `text(html)`
(strip tags), `parse_date(str)` (most European formats to ISO),
`posting(...)` (builds the record and its id).

Two shapes:

- **Search board** (takes a query): called once per query in
  `config/search.json`. Return whatever the board returns for that query.
- **Feed** (a portal that lists everything on a page or two): wrap it in
  `_feed("name", build)` like `src_ethz`, return results only for
  `query == "__all__"`, and add the name to `FEEDS`. `_feed` keeps doctoral
  posts only.

## 3. Register it

- Add it to `SOURCES` (and `FEEDS` if it is a feed).
- Add an entry to `templates/search.example.json` under `sources` with
  `enabled`, `pages` and a one-line `note`.
- If every result is a doctoral post, add the name to the tuple in
  `prefilter()` that marks sources as already role-filtered.
- Add a row to the Boards table in `README.md`.

## 4. Test it

```bash
python3 scripts/scan.py --source myboard --top 10
```

Check on a handful of results that title, institution, country, deadline and
URL are right, and that the URL opens the advert. Then:

```bash
python3 scripts/doctor.py --online
```

## Notes

- Regex over HTML is deliberate: no dependencies, and a parser that breaks
  fails loudly (zero results, and the scan warns) instead of silently.
- Keep requests few. Listing pages only; `enrich.py` reads individual adverts
  later, and only for postings that pass the prefilter.
- Country names must match the keys used in `country_bonus` ("Netherlands",
  "United Kingdom", ...).

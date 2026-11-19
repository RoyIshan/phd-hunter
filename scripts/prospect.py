#!/usr/bin/env python3
"""Find people and projects before an advert exists.

  scholars "QUERY" [--countries NL,DE,..] [--since 2023] [--top 20]
      Who in Europe publishes on a topic. Ranks authors by recent matching
      papers (last-author papers count extra: that is usually the group lead).
      Source: OpenAlex.

  author "NAME" [--inst "University"] [--works 12]
      Recent papers of one person, with venue, year, citations and DOI link.
      Use it to check a supervisor's record before /evaluate or /outreach.
      Source: OpenAlex.

  projects "QUERY" [--since YYYY-MM-DD] [--top 20]
      EU-funded projects on a topic that started recently or start soon.
      New grants hire PhD candidates in their first year, often before the
      positions reach the job boards. Flags doctoral networks and ERC grants.
      Source: CORDIS.

Add --save to write the result to reports/prospects-<slug>.md.
Read-only public APIs. Names and papers found here are leads: open the
person's own page before putting anything in a draft.
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = dt.date.today()
EUROPE = ("NL,BE,LU,DE,AT,CH,DK,SE,NO,FI,FR,IE,GB,IT,ES,PT,EE,LV,LT,PL,CZ,SI,GR,IS,HU,SK,HR,RO,BG,CY,MT,LI")


def get_json(url):
    out = subprocess.run(["curl", "-sL", "--compressed", "-m", "40", "-A", "phd-hunter/1.0 (local research tool)", url],
                         capture_output=True).stdout.decode("utf-8", "ignore")
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        sys.exit(f"No usable answer from {url.split('?')[0]}. Try again in a minute.")


def emit(lines, args, slug):
    text = "\n".join(lines)
    print(text)
    if args.save:
        path = ROOT / "reports" / f"prospects-{re.sub(r'[^a-z0-9]+', '-', slug.lower()).strip('-')[:50]}.md"
        path.parent.mkdir(exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
        print(f"\nSaved to {path.relative_to(ROOT)}")


def cmd_scholars(a):
    countries = a.countries.upper().replace(",", "|")
    flt = f"from_publication_date:{a.since}-01-01,authorships.institutions.country_code:{countries},type:article|preprint|book-chapter"
    url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(a.query) + "&filter=" + urllib.parse.quote(flt, safe=":,|")
           + "&per-page=200&select=id,title,publication_year,cited_by_count,authorships,primary_location")
    data = get_json(url)
    works = data.get("results", [])
    wanted = set(a.countries.upper().split(","))
    people = defaultdict(lambda: {"n": 0, "last": 0, "cites": 0, "titles": [], "inst": "", "cc": "", "id": ""})
    for rank, w in enumerate(works):
        auths = w.get("authorships", [])
        for au in auths:
            inst = next((i for i in au.get("institutions", []) if i.get("country_code") in wanted), None)
            if not inst or not (au.get("author") or {}).get("id"):
                continue
            p = people[au["author"]["id"]]
            p["name"], p["id"] = au["author"]["display_name"], au["author"]["id"].rsplit("/", 1)[-1]
            p["inst"], p["cc"] = inst["display_name"], inst["country_code"]
            p["n"] += 1
            p["cites"] += w.get("cited_by_count", 0)
            if au.get("author_position") == "last" and len(auths) > 1:
                p["last"] += 1
            if len(p["titles"]) < 2:
                p["titles"].append(f"{w.get('title') or ''} ({w.get('publication_year')})")
    ranked = sorted(people.values(), key=lambda p: (-(p["n"] + 0.7 * p["last"]), -p["cites"]))
    ranked = [p for p in ranked if p["n"] >= (2 if len(ranked) > a.top else 1)][:a.top]
    lines = [f"# Who publishes on \"{a.query}\" in Europe since {a.since}", "",
             f"{data.get('meta', {}).get('count', 0)} matching works in OpenAlex; ranked from the {len(works)} most relevant. "
             "Papers = matching papers; lead = of those, as last author.", "",
             "| Person | Institution | Country | Papers | Lead | Citations | Examples |", "|---|---|---|---|---|---|---|"]
    for p in ranked:
        ex = "; ".join(t[:90] for t in p["titles"]).replace("|", "/")
        lines.append(f"| {p['name']} (`{p['id']}`) | {p['inst']} | {p['cc']} | {p['n']} | {p['last']} | {p['cites']} | {ex} |")
    lines += ["", "Next: `python3 scripts/prospect.py author \"Name\"` for a person's record, then `/outreach Name`."]
    emit(lines, a, "scholars-" + a.query)


def cmd_author(a):
    data = get_json("https://api.openalex.org/authors?search=" + urllib.parse.quote(a.name) + "&per-page=10")
    cands = data.get("results", [])
    if a.inst:
        narrowed = [c for c in cands if any(a.inst.lower() in (i.get("institution", {}).get("display_name", "")).lower()
                                            for i in c.get("affiliations", []))]
        cands = narrowed or cands
    if not cands:
        sys.exit("No author found. Check the spelling or add --inst.")
    c = max(cands[:5], key=lambda c: c.get("works_count", 0)) if not a.inst else cands[0]
    aid = c["id"].rsplit("/", 1)[-1]
    inst = (c.get("last_known_institutions") or [{}])[0]
    works = get_json(f"https://api.openalex.org/works?filter=author.id:{aid}&sort=publication_date:desc&per-page={a.works}"
                     "&select=title,publication_year,cited_by_count,doi,primary_location,authorships,type").get("results", [])
    topics = ", ".join(t["display_name"] for t in (c.get("topics") or [])[:6])
    lines = [f"# {c['display_name']}", "",
             f"- Institution (last known): {inst.get('display_name', '?')} ({inst.get('country_code', '?')})",
             f"- Works: {c.get('works_count')} · citations: {c.get('cited_by_count')} · h-index: {c.get('summary_stats', {}).get('h_index')}",
             f"- Topics: {topics}", f"- ORCID: {c.get('orcid') or 'not listed'} · OpenAlex: https://openalex.org/{aid}", ""]
    if len(cands) > 1 and not a.inst:
        others = "; ".join(f"{x['display_name']} ({(x.get('last_known_institutions') or [{}])[0].get('display_name', '?')})" for x in cands[:5])
        lines += [f"Several people match this name: {others}. Add --inst if this is the wrong one.", ""]
    lines += [f"## Latest {len(works)} works", "", "| Year | Title | Venue | Cites | Position | Link |", "|---|---|---|---|---|---|"]
    for w in works:
        venue = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or w.get("type", "")
        pos = next((x.get("author_position", "") for x in w.get("authorships", []) if ((x.get("author") or {}).get("id") or "").endswith(aid)), "")
        lines.append(f"| {w.get('publication_year')} | {(w.get('title') or '').replace('|', '/')[:110]} | {venue[:40]} | "
                     f"{w.get('cited_by_count')} | {pos} | {w.get('doi') or ''} |")
    lines += ["", "OpenAlex merges and splits authors imperfectly: confirm on the person's own page before citing."]
    emit(lines, a, "author-" + a.name)


def as_list(x):
    return x if isinstance(x, list) else ([x] if x else [])


def cmd_projects(a):
    since = a.since or (TODAY - dt.timedelta(days=400)).isoformat()
    terms = " AND ".join(f"'{t.strip()}'" for t in a.query.split(" AND "))
    q = f"contenttype='project' AND {terms} AND startDate>={since}"
    url = ("https://cordis.europa.eu/search/en?q=" + urllib.parse.quote(q) + f"&p=1&num={min(a.top * 2, 100)}"
           "&srt=/project/startDate:decreasing&format=json")
    data = get_json(url)
    hits = as_list(data.get("hits", {}).get("hit"))
    lines = [f"# EU-funded projects on \"{a.query}\" starting on or after {since}", "",
             f"{data.get('result', {}).get('header', {}).get('totalHits', len(hits))} projects in CORDIS. "
             "DN = MSCA Doctoral Network (hires 10-15 PhD candidates; mobility rule applies). ERC = single-PI grant, usually with PhD positions.", "",
             "| Start | Acronym | Title | Type | Coordinator | Country | EU funding | Link |", "|---|---|---|---|---|---|---|---|"]
    shown = 0
    for h in hits:
        p = h.get("project", {})
        rel = (p.get("relations") or {}).get("associations") or {}
        orgs = as_list(rel.get("organization"))
        coord = next((o for o in orgs if (o.get("@attributes") or {}).get("type") == "coordinator"), {}) or (orgs[0] if orgs else {})
        blob = json.dumps(rel.get("call", "")) + json.dumps(rel.get("programme", "")) + str(p.get("title", ""))
        kind = ("DN" if re.search(r"MSCA[^\"]{0,30}DN|Doctoral Network", blob) else
                "ERC" if re.search(r"\bERC\b", blob) else
                "MSCA" if "MSCA" in blob else "")
        money = p.get("ecMaxContribution") or ""
        try:
            money = f"€{float(money) / 1e6:.1f}M"
        except ValueError:
            pass
        lines.append(f"| {p.get('startDate', '')} | {p.get('acronym', '')} | {str(p.get('title', '')).replace('|', '/')[:90]} | {kind} | "
                     f"{str(coord.get('legalName', '')).title()[:42]} | {(coord.get('address') or {}).get('country', '')} | {money} | "
                     f"https://cordis.europa.eu/project/id/{p.get('id', '')} |")
        shown += 1
        if shown >= a.top:
            break
    lines += ["", "Next: open the project page, find the university partners and the work package leads, then `/outreach` to ask "
              "whether PhD positions are planned. Many projects list vacancies on their own site first."]
    emit(lines, a, "projects-" + a.query)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scholars"); s.add_argument("query"); s.add_argument("--countries", default=EUROPE)
    s.add_argument("--since", type=int, default=TODAY.year - 3); s.add_argument("--top", type=int, default=20)
    s.add_argument("--save", action="store_true"); s.set_defaults(fn=cmd_scholars)
    s = sub.add_parser("author"); s.add_argument("name"); s.add_argument("--inst", default="")
    s.add_argument("--works", type=int, default=12); s.add_argument("--save", action="store_true"); s.set_defaults(fn=cmd_author)
    s = sub.add_parser("projects"); s.add_argument("query"); s.add_argument("--since", default="")
    s.add_argument("--top", type=int, default=20); s.add_argument("--save", action="store_true"); s.set_defaults(fn=cmd_projects)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

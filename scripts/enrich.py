#!/usr/bin/env python3
"""Read the full advert behind promising postings and extract what decides an application.

    python3 scripts/enrich.py                # every open posting with prefilter >= 18, not yet read
    python3 scripts/enrich.py --min 25 --limit 40
    python3 scripts/enrich.py --id euraxess-f62e72f3 --force

For each advert it saves the text to data/ads/<id>.txt and records signals:

    lang-required:<Language>   a language other than English is demanded (counts as a gate)
    lang-plus:<Language>       that language is an advantage only
    needs-proposal             research proposal, project outline or research statement requested
    needs-english-test         IELTS / TOEFL / Cambridge asked for
    gmat-gre                   GMAT or GRE mentioned
    wants-publications         publication record expected
    maybe-self-funded          self-funded or tuition wording found: check the funding
    msca                       Marie Skłodowska-Curie funding (mobility rule applies)
    suspicious-text            wording aimed at an AI reader; read the advert yourself before trusting it

plus the salary line, duration, contact emails and the sentence stating the degree
requirement. Scores are then recomputed with the advert text included. Signals are
regex heuristics over untrusted page text: they point at what to verify in /evaluate,
they are not verdicts.
"""
import argparse
import concurrent.futures
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scan  # noqa: E402

ADS = scan.ROOT / "data" / "ads"
LANGS = ["Dutch", "German", "French", "Swedish", "Norwegian", "Danish", "Finnish", "Italian", "Spanish",
         "Portuguese", "Scandinavian", "Luxembourgish", "Czech", "Polish", "Estonian"]
PRE = r"fluen\w*|proficien\w*|command (?:of|in)|knowledge of|mastery of|speak\w*|spoken|written|native|\b[ABC][12]\b|communicat\w+ in|interviews? in|teach\w* in|skills in|competen\w+ in"
POST = r"(?:language )?(?:skills|proficiency|is required|is a must|is essential|is necessary|required|fluen\w*|\(?[ABC][12]\b|speaker|speaking)"
SOFT = r"\bplus\b|advantage|asset|not required|not necessary|no .{0,15}(?:required|needed)|strength|preferr|willing|desirab|bonus|nice to have|optional|course|training|learn|merit|beneficial|welcome|helpful|encourag"
START = r"job description|offer description|about the position|your role|the position|project description|what you will do|your tasks"


def page_text(raw):
    body = re.sub(r"<(script|style|svg|noscript|nav|footer|header)\b.*?</\1>", " ", raw, flags=re.S)
    body = re.sub(r"<(br|/p|/div|/li|/h\d|/tr)\b[^>]*>", "\n", body, flags=re.I)
    body = html.unescape(re.sub(r"<[^>]+>", " ", body))
    body = re.sub(r"[ \t\xa0]+", " ", body)
    # EURAXESS ships a hidden "STATUS: EXPIRED" label on every offer page, open or not. It is not a verdict.
    body = re.sub(r"(?m)^\s*STATUS:\s*EXPIRED\s*$\n?", "", body)
    return re.sub(r"\n\s*\n+", "\n", body).strip()


def analyse(txt):
    signals, info = [], {}
    sentences = re.split(r"(?<=[.!?;])\s+|\n", txt)
    for lang in LANGS:
        verdicts = set()
        near = rf"(?:{PRE})[^.;:]{{0,45}}\b{lang}\b|\b{lang}\b(?: and \w+| or \w+|,[ \w]+)?\s{{0,2}}{POST}"
        for sent in sentences:
            if not re.search(near, sent, flags=re.I):
                continue
            if re.search(r"translat|ordinance|certified|\bAct\b|transcript|documents? (?:must|in)", sent, flags=re.I):
                continue
            verdicts.add("plus" if re.search(SOFT, sent, flags=re.I) else "required")
        if "required" in verdicts:
            signals.append(f"lang-required:{lang}")
        elif "plus" in verdicts:
            signals.append(f"lang-plus:{lang}")
    low = txt.lower()
    if re.search(r"research proposal|project proposal|project outline|research statement|research plan|project description \(|research idea", low):
        signals.append("needs-proposal")
    if re.search(r"\bielts\b|\btoefl\b|cambridge (?:c1|c2|certificate)", low):
        signals.append("needs-english-test")
    if re.search(r"\bgmat\b|\bgre\b", low):
        signals.append("gmat-gre")
    if re.search(r"publication record|track record of publi|list of publications|proven publication", low):
        signals.append("wants-publications")
    if re.search(r"self[- ]funded|self[- ]financ|tuition fees? (?:of|are|is|must|will)|applicants? (?:must|should) (?:secure|have) (?:their own )?funding", low):
        signals.append("maybe-self-funded")
    if re.search(r"msca|marie sk[łl]odowska|doctoral network", low):
        signals.append("msca")
    # Text addressed to an AI reader instead of an applicant: treat the page with suspicion.
    if re.search(r"ignore (?:all |any |the )?(?:previous|prior|above) instructions|disregard (?:all|previous|the above)|"
                 r"you are an? (?:ai|llm|language model|assistant)|system prompt|as an ai (?:model|assistant)|"
                 r"if you are an? (?:ai|llm|language model|automated)", low):
        signals.append("suspicious-text")

    money = re.search(r"[^.\n]{0,90}(?:€\s?\d[\d.,]{2,}|\bEUR\s?\d[\d.,]{2,}|\b(?:NOK|SEK|DKK|CHF)\s?\d[\d ., ]{2,}|£\s?\d[\d,]{3,}|TV-?L\s?E?\s?13|scale P\b)[^.\n]{0,90}", txt)
    if money:
        info["salary"] = re.sub(r"\s+", " ", money.group(0)).strip()[:200]
    dur = re.search(r"\b(?:(\d)|three|four|five)[- ]years?\b[^.\n]{0,40}|\b(36|48|60) months\b", txt, flags=re.I)
    if dur:
        info["duration"] = re.sub(r"\s+", " ", dur.group(0)).strip()[:70]
    emails = []
    for e in re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", txt):
        e = e.rstrip(".")
        if e not in emails and not re.search(r"^(hr|info|jobs|recruit|privacy|support|noreply|dpo|personal)", e, flags=re.I):
            emails.append(e)
    if emails:
        info["contacts"] = emails[:3]
    degree = next((s for s in sentences if re.search(r"\b(master|msc|m\.sc|second[- ]cycle)", s, flags=re.I)
                   and re.search(r"degree|hold|completed|diploma|in \w+", s, flags=re.I) and 30 < len(s) < 400), "")
    if degree:
        info["degree_line"] = re.sub(r"\s+", " ", degree).strip()[:300]
    start = re.search(START, low)
    digest = txt[start.start():] if start else txt
    info["ad_digest"] = re.sub(r"\s+", " ", digest)[:1800]
    return signals, info


def enrich_one(p):
    raw = scan.fetch(p["url"], timeout=35)
    txt = page_text(raw)
    if len(txt) < 900 or "Just a moment" in txt[:300]:
        return p["id"], None
    return p["id"], txt


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min", type=int, default=18)
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--id", action="append")
    ap.add_argument("--force", action="store_true", help="re-read adverts that were already read")
    a = ap.parse_args()

    cfg = scan.load_config()
    store = scan.load_store()
    if a.id:
        todo = [p for k, p in store.items() if any(k == i or k.endswith(i) for i in a.id)]
    else:
        todo = [p for p in store.values()
                if p.get("status") in ("new", "seen", "evaluated", "tracked") and p.get("prefilter", 0) >= a.min
                and "expired" not in p.get("flags", []) and (a.force or "enriched" not in p)]
        todo.sort(key=lambda p: -p.get("prefilter", 0))
        todo = todo[:a.limit]
    if not todo:
        sys.exit("Nothing to read. Lower --min, or use --force.")

    ADS.mkdir(parents=True, exist_ok=True)
    # Group by source so each site is read sequentially; sites run side by side.
    by_source = {}
    for p in todo:
        by_source.setdefault(p["source"], []).append(p)

    def run(group):
        return [enrich_one(p) for p in group]

    done = unreadable = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(by_source)) as pool:
        for results in pool.map(run, by_source.values()):
            for pid, txt in results:
                p = store[pid]
                if txt is None:
                    p["enriched"] = "unreadable"
                    unreadable += 1
                    continue
                (ADS / f"{pid}.txt").write_text(f"URL: {p['url']}\n---\n{txt}", encoding="utf-8")
                signals, info = analyse(txt)
                p["signals"], p["enriched"] = signals, scan.TODAY.isoformat()
                for k in ("salary", "duration", "contacts", "degree_line", "ad_digest"):
                    if info.get(k):
                        p[k] = info[k]
                    elif k in p and k != "ad_digest":
                        del p[k]
                done += 1

    for p in store.values():
        before = p.get("prefilter", 0)
        scan.prefilter(p, cfg)
        p["_delta"] = p["prefilter"] - before
    shown = sorted((store[p["id"]] for p in todo), key=lambda p: -p["prefilter"])
    print(f"Read {done} adverts ({unreadable} could not be read by script: open those in the browser pane).\n")
    for p in shown:
        if p.get("enriched") == "unreadable":
            continue
        delta = f"{p['_delta']:+d}" if p["_delta"] else "  "
        print(f"{p['prefilter']:3d} {delta:>4s}  {p['id']}  {p['title'][:66]}")
        bits = [s for s in p.get("signals", [])]
        if p.get("salary"):
            bits.append("pay: " + p["salary"][:70])
        print(f"          {p.get('org', '')[:36]} | {p['country']} | {p.get('deadline') or 'no deadline'} | {'; '.join(bits) or 'no signals'}")
    for p in store.values():
        p.pop("_delta", None)
    scan.STORE.write_text(json.dumps(store, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

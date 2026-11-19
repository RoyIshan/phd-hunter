#!/usr/bin/env python3
"""Check a draft against the master CV before it goes anywhere.

    python3 scripts/verify.py output/A008-example/cv.md
    python3 scripts/verify.py output/A008-example/           # every .md in the pack
    python3 scripts/verify.py letter.md --also reports/example-university.md data/ads/<id>.txt

Flags anything in the draft that cannot be traced to profile/cv.md (or to the
files given with --also, for facts about the position and the people):

  numbers      every figure, year, grade, percentage and amount
  names        capitalised names and acronyms (people, tools, methods, places)
  languages    any language and level
  claims       phrases a CV must back up (published, first author, fluent, award ...)

A flag is a question, not a verdict: the item may be phrased differently in
the CV, or belong to the position. But nothing flagged should be sent before a
human has looked at it. Exit code 1 when there are flags.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ("english|dutch|german|french|spanish|italian|portuguese|swedish|norwegian|danish|finnish|polish|czech|greek|"
         "turkish|arabic|hindi|bengali|urdu|mandarin|chinese|japanese|korean|russian|ukrainian|persian|hebrew")
CLAIMS = (r"publish\w*|peer[- ]reviewed|first[- ]author|co[- ]author\w*|journal article|conference paper|"
          r"award\w*|prize|scholarship|fellowship|cum laude|distinction|top \d+ ?%|ranked|fluent|native|certified|patent\w*")
COMMON = set("""I The A An In At On For With And Or But My We Our This That These Those It He She They You Your As By
From To Of If When While After Before During Since Because Although However Therefore Also Then There Here Dear Kind
Regards Sincerely Yours Thank Thanks Best Please Why What How Who Where Which January February March April May June
July August September October November December Monday Tuesday Wednesday Thursday Friday Saturday Sunday PhD MSc BSc
BA MA BTech MPhil CV Professor Prof Dr Mr Ms Mrs University Department Faculty School Institute Centre Center Group
Committee Selection Members Application Position Research Researcher Doctoral Candidate Programme Program Project
Summary Education Experience Skills Languages References Publications Projects Certifications Thesis Supervisor
Supervisors Europe European EU Not No Yes One Two Three Four Five Six Seven Eight Nine Ten First Second Third
Subject Re Attached Enclosed Motivation Letter Cover Personal Statement Proposal Outline Introduction Method Methods
Plan Contribution Background Problem Question Questions Design Relevance Fit Year Phase Section""".split())


def norm(s):
    return re.sub(r"\s+", " ", s.lower())


def numbers(text):
    """Figures as written, plus a digits-only form so 21 million / 21,000,000 / €40.4M compare loosely."""
    found = set()
    for m in re.finditer(r"(?<![\w.])(\d[\d.,]*\d|\d)(?![\w])", text):
        raw = m.group(1).strip(".,")
        if raw:
            found.add(raw)
    return found


def names(text):
    out = set()
    for m in re.finditer(r"\b(?:[A-Z][\w'’-]+|[A-Z]{2,}[\w-]*)(?:[ -](?:[A-Z][\w'’-]+|[A-Z]{2,}[\w-]*|of|for|and|de|van|von|der))*", text):
        phrase = re.sub(r"(?:[ -](?:of|for|and|de|van|von|der))+$", "", m.group(0).strip())
        words = [w for w in re.split(r"[ -]", phrase) if w not in ("of", "for", "and", "de", "van", "von", "der")]
        if not words or all(w in COMMON for w in words):
            continue
        out.add(phrase)
    return out


def check(draft, sources):
    text = draft.read_text(encoding="utf-8")
    body = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith(">"))  # quoted notes are not claims
    src = "\n".join(sources.values())
    src_norm, src_digits = norm(src), re.sub(r"[^\d]", " ", src)
    src_numbers = numbers(src)
    flags = []

    def where(needle):
        for i, line in enumerate(body.splitlines(), 1):
            if needle in line:
                return i, line.strip()[:110]
        return 0, ""

    for n in sorted(numbers(body)):
        if n in src_numbers or n.replace(",", "") in src_digits.split() or n.replace(".", "").replace(",", "") in src_digits.split():
            continue
        if re.fullmatch(r"[1-9]|1\d|2\d|3[01]", n):  # small counts and day-of-month: too noisy to flag
            continue
        line, ctx = where(n)
        flags.append(("number", n, line, ctx))

    for name in sorted(names(body), key=len, reverse=True):
        if norm(name) in src_norm:
            continue
        parts = [w for w in re.split(r"[ -]", name) if w not in COMMON and len(w) > 2 and w[0].isupper()]
        missing = [w for w in parts if norm(w) not in src_norm]
        if not missing:
            continue
        line, ctx = where(name)
        if line and not any(f[1] in name or name in f[1] for f in flags if f[0] == "name"):
            flags.append(("name", name, line, ctx))

    for m in re.finditer(rf"\b({LANGS})\b(?:\s*\(([^)]{{1,25}})\))?", body, flags=re.I):
        lang, level = m.group(1), (m.group(2) or "").strip()
        if lang.lower() not in src_norm:
            line, ctx = where(m.group(0))
            flags.append(("language", m.group(0), line, ctx))
        elif level and not re.search(rf"{lang}\W{{0,3}}\(?[^)\n]{{0,40}}{re.escape(level.lower())}", src_norm, flags=re.I):
            line, ctx = where(m.group(0))
            flags.append(("language level", m.group(0), line, ctx))

    for m in re.finditer(rf"\b({CLAIMS})\b", body, flags=re.I):
        word = m.group(1).lower()
        stem = re.sub(r"(ed|ing|s|ations?)$", "", word)[:7]
        if stem not in src_norm:
            line, ctx = where(m.group(0))
            flags.append(("claim", m.group(0), line, ctx))
    # A CV that says there are no publications makes any publication wording a red flag.
    if re.search(r"publications?\W{0,60}none|publications:\s*0\b", src_norm):
        for m in re.finditer(r"\b(published|publication record|co-?authored|(?:my|our|a|two|three|several) (?:\w+ )?(?:papers?|articles?)|papers? (?:at|in) [A-Z])", body, flags=re.I):
            line, ctx = where(m.group(0))
            flags.append(("publication", m.group(0), line, ctx))
    seen, unique = set(), []
    for f in flags:
        if (f[0], f[1]) not in seen:
            seen.add((f[0], f[1]))
            unique.append(f)
    return unique


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft", help="a Markdown draft, or a pack folder")
    ap.add_argument("--also", nargs="*", default=[], help="extra sources of truth for this draft: the report, the saved advert")
    ap.add_argument("--cv", default=str(ROOT / "profile" / "cv.md"))
    a = ap.parse_args()

    cv = Path(a.cv)
    if not cv.exists():
        sys.exit(f"{cv} not found. Run setup first.")
    sources = {"cv": cv.read_text(encoding="utf-8")}
    profile = cv.parent / "profile.yml"
    if profile.exists():
        sources["profile"] = profile.read_text(encoding="utf-8")
    for extra in a.also:
        sources[extra] = Path(extra).read_text(encoding="utf-8", errors="ignore")

    target = Path(a.draft)
    skip = ("checklist.md", "interview-prep.md", "referee-note.md")
    drafts = sorted(p for p in target.glob("*.md") if p.name not in skip) if target.is_dir() else [target]
    if not drafts:
        sys.exit("No drafts found.")
    total = 0
    for draft in drafts:
        flags = check(draft, sources)
        total += len(flags)
        print(f"\n{draft}: {len(flags)} item(s) not found in {', '.join(sources)}")
        for kind, item, line, ctx in sorted(flags, key=lambda f: f[2]):
            print(f"  line {line:3d}  {kind:14s} {item[:40]:40s} | {ctx}")
    if total:
        print(f"\n{total} item(s) to check. For each: fix the draft, add the fact to profile/cv.md if it is true, "
              "or pass the report and advert with --also if it is about the position.")
    else:
        print("\nEvery number, name, language and claim traces back to the sources.")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()

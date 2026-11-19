#!/usr/bin/env python3
"""Check that phd-hunter is set up and working.

    python3 scripts/doctor.py            # local checks only
    python3 scripts/doctor.py --online   # also fetch one page from every board

Exit code 0 when nothing is broken (warnings allowed), 1 otherwise.
"""
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

OK, WARN, BAD = "ok  ", "warn", "FAIL"
results = []


def note(level, what, hint=""):
    results.append(level)
    print(f"[{level}] {what}" + (f"\n       {hint}" if hint and level != OK else ""))


def main():
    online = "--online" in sys.argv

    # --- tools
    note(OK if sys.version_info >= (3, 9) else BAD, f"Python {sys.version.split()[0]}", "Python 3.9 or newer is needed.")
    note(OK if shutil.which("curl") else BAD, "curl available", "Install curl: every page is fetched with it.")
    for mod, why in (("pypdf", "reading PDF documents during setup"), ("docx", "exporting drafts to .docx (pip install python-docx)")):
        found = importlib.util.find_spec(mod) is not None
        note(OK if found else WARN, f"optional package {mod}", "" if found else f"Only needed for {why}.")

    # --- profile
    profile = ROOT / "profile"
    for name in ("profile.yml", "cv.md", "voice.md"):
        path = profile / name
        if not path.exists():
            note(BAD, f"profile/{name} missing", "Run /phd-hunter setup in Claude Code, or copy templates/ and fill them in.")
            continue
        text = path.read_text(encoding="utf-8")
        todo = len(re.findall(r"\bCONFIRM\b|\bTODO\b", text))
        if "Alex Example" in text:
            note(BAD, f"profile/{name} is still the example", "Replace it with your own details (/phd-hunter setup).")
        elif todo:
            note(WARN, f"profile/{name}: {todo} field(s) marked CONFIRM or TODO", "Eligibility verdicts depend on these. Fill them in.")
        else:
            note(OK, f"profile/{name}")

    # --- search config
    cfg_path = ROOT / "config" / "search.json"
    cfg = None
    if not cfg_path.exists():
        note(BAD, "config/search.json missing", "Run /phd-hunter setup, or copy templates/search.example.json there and edit it.")
    else:
        try:
            cfg = json.loads(cfg_path.read_text())
        except json.JSONDecodeError as exc:
            note(BAD, "config/search.json is not valid JSON", str(exc))
    if cfg:
        problems = []
        if len(cfg.get("queries", [])) < 3:
            problems.append("fewer than 3 queries")
        for tier in ("strong", "medium", "weak", "negative"):
            if not cfg.get("weights", {}).get(tier, {}).get("terms"):
                problems.append(f"no '{tier}' keywords")
        if not cfg.get("candidate_languages"):
            problems.append("candidate_languages not set (language gates assume English only)")
        if not (cfg.get("sources", {}).get("euraxess", {}).get("facets")):
            problems.append("no EURAXESS research fields chosen (see reference/euraxess-fields.json)")
        for rx in cfg.get("role_include", []) + cfg.get("role_exclude", []):
            try:
                re.compile(rx)
            except re.error:
                problems.append(f"bad pattern: {rx}")
        note(WARN if problems else OK, "config/search.json" + (": " + "; ".join(problems) if problems else ""))

    # --- data
    store = ROOT / "data" / "postings.json"
    if store.exists():
        n = len(json.loads(store.read_text()))
        note(OK, f"data/postings.json holds {n} postings")
    else:
        note(WARN, "No scan yet", "Run /phd-hunter scan (or python3 scripts/scan.py).")
    log = ROOT / "data" / "scan_log.json"
    if log.exists():
        last = json.loads(log.read_text())[-1]
        dead = [k for k, v in last["counts"].items() if v == 0]
        note(WARN if dead else OK, f"last scan {last['date']}" + (f": no results from {', '.join(dead)}" if dead else ": every board returned results"),
             "A board with 0 results usually changed its page layout: its parser in scripts/scan.py needs a look." if dead else "")

    # --- privacy
    gitignore = ROOT / ".gitignore"
    needed = ["profile/", "data/", "reports/", "output/", "documents/", "config/search.json"]
    missing = [n for n in needed if not gitignore.exists() or n not in gitignore.read_text()]
    note(BAD if missing else OK, ".gitignore protects personal folders" + (f" (missing: {', '.join(missing)})" if missing else ""),
         "Your CV, tracker and drafts must never be committed." if missing else "")

    # --- boards
    if online and cfg:
        import scan
        for name, fn in scan.SOURCES.items():
            spec = cfg["sources"].get(name, {})
            if not spec.get("enabled", True):
                continue
            try:
                query = "__all__" if name in scan.FEEDS else (cfg["queries"][0] if cfg.get("queries") else "phd")
                extra = {"facets": dict(list(spec["facets"].items())[:1])} if name == "euraxess" and spec.get("facets") else {}
                got = fn(query, 1, **extra)
            except Exception as exc:
                got, err = [], str(exc)[:80]
            else:
                err = ""
            note(OK if got else BAD, f"board {name}: {len(got)} results" + (f" ({err})" if err else ""),
                 "" if got else "Parser may be out of date. See docs/ADDING_A_BOARD.md.")

    bad, warn = results.count(BAD), results.count(WARN)
    print(f"\n{bad} problem(s), {warn} warning(s).")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

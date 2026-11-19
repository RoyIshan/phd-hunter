#!/usr/bin/env python3
"""Print a ready-to-run browser collector for a board that blocks scripts.

    python3 scripts/collector.py academicpositions

Fills scripts/browser/<board>.js with the fields and theme keywords from
config/search.json. Run the printed JavaScript in a browser tab that is open
on the board, then import what it returns with scripts/import_postings.py.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    board = sys.argv[1] if len(sys.argv) > 1 else "academicpositions"
    template = ROOT / "scripts" / "browser" / f"{board}.js"
    if not template.exists():
        sys.exit(f"No collector for '{board}'. Available: " + ", ".join(p.stem for p in template.parent.glob("*.js")))
    cfg = json.loads((ROOT / "config" / "search.json").read_text())
    spec = cfg.get("sources", {}).get(board, {})
    fields = spec.get("fields") or []
    if not fields:
        sys.exit(f"config/search.json has no sources.{board}.fields. Add the field slugs you browse on the site.")
    terms = cfg["weights"]["strong"]["terms"] + cfg["weights"]["medium"]["terms"] + cfg.get("queries", [])
    terms = sorted({re.escape(t.strip().lower()) for t in terms if len(t.strip()) > 2})
    keep = "/" + "|".join(terms).replace("/", r"\/") + "/i" if terms else "null"
    js = template.read_text()
    js = js.replace("/*FIELDS*/[]", json.dumps(fields))
    js = js.replace("/*MAX_PAGES*/15", str(int(spec.get("max_pages", 15))))
    js = js.replace("/*KEEP*/null", keep)
    # Drop the header comment: the browser only needs the code.
    print(js[js.index("const FIELDS"):])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Are the positions you care about still open?

    python3 scripts/alive.py              # tracked applications in progress + scored postings (fit >= 3.5)
    python3 scripts/alive.py --min-fit 3.0

Re-fetches each advert and reports: open, closed (page gone or says so),
deadline passed, or unreadable (the site needs a browser).
Run it before spending an evening on an application. Read-only; it changes
nothing except marking postings whose page is clearly gone as expired.
"""
import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import enrich  # noqa: E402
import scan  # noqa: E402

CLOSED = (r"no longer (?:available|accepting|open)|position (?:has been|is) filled|vacancy (?:is|has been|has) (?:closed|expired|filled)|"
          r"this (?:job|vacancy|position|advert\w*) (?:has expired|is closed|has closed|is no longer)|applications? (?:are|is) (?:now )?closed|"
          r"deadline has passed|job not found|page not found|404 not found|ad has expired|offer (?:has )?expired")


def judge(raw, known_deadline):
    txt = enrich.page_text(raw)
    if len(txt) < 900 or re.search(r"just a moment|security verification|enable javascript|laster\.\.\.", txt[:400], flags=re.I):
        return "unreadable", "open it in a browser"
    if re.search(CLOSED, txt[:6000], flags=re.I):
        return "CLOSED", re.search(CLOSED, txt[:6000], flags=re.I).group(0)
    deadline = known_deadline
    if not deadline:  # only guess from the page when nothing is on record
        m = re.search(r"(?:application deadline|deadline|closing date|closes on|apply by)\W{0,5}([^\n]{0,40})", txt, flags=re.I)
        deadline = scan.parse_date(m.group(1)) if m else ""
    if deadline and deadline < scan.TODAY.isoformat():
        return "DEADLINE PASSED", deadline
    days = (dt.date.fromisoformat(deadline) - scan.TODAY).days if deadline else None
    return "open", f"{days} days left" if days is not None else "no deadline found"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-fit", type=float, default=3.5)
    a = ap.parse_args()

    store = scan.load_store()
    items = {}
    tracker = scan.ROOT / "data" / "tracker.csv"
    if tracker.exists():
        with tracker.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["status"] in ("discovered", "evaluated", "shortlisted", "contacted", "drafting") and r.get("url"):
                    items[r["url"]] = (r["tid"], f"{r['institution']}: {r['position']}", r.get("deadline", ""), None)
    for pid, p in store.items():
        if (p.get("fit") or 0) >= a.min_fit and p.get("status") in ("evaluated", "tracked") and p["url"] not in items:
            items[p["url"]] = (pid, f"{p.get('org', '')}: {p['title']}", p.get("deadline", ""), pid)
    if not items:
        sys.exit("Nothing to check yet: track or score some positions first.")

    changed = False
    for url, (label, name, deadline, pid) in items.items():
        verdict, detail = judge(scan.fetch(url, timeout=35), deadline)
        print(f"{verdict:16s} {label:28s} {name[:60]}\n{'':16s} {detail}")
        if verdict == "CLOSED" and pid:
            store[pid]["status"], changed = "expired", True
    if changed:
        scan.STORE.write_text(json.dumps(store, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

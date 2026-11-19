#!/usr/bin/env python3
"""Terminal dashboard for the pipeline.

    python3 scripts/tui.py            # interactive (needs a real terminal)
    python3 scripts/tui.py --plain    # print the three views and exit

Views: 1 Positions (scanned and scored) · 2 Applications (tracker) · 3 Due (deadlines, actions, follow-ups)

Keys
  up/down, j/k   move                 PgUp/PgDn   page
  1 2 3, Tab     switch view          Enter       details on/off
  /              filter by text       Esc         clear filter
  s              change sort          g           hide or show gate-blocked positions
  o              open the advert in your browser
  t              track the position   d           dismiss it
  r              reload from disk     q           quit

Standard library only (curses). Tracking and dismissing go through the same
code as scripts/ops.py; nothing here sends or submits anything.
"""
import argparse
import csv
import datetime as dt
import json
import sys
import textwrap
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "data" / "postings.json"
TRACKER = ROOT / "data" / "tracker.csv"
CONTACTS = ROOT / "data" / "contacts.csv"
TODAY = dt.date.today()
T_FIELDS = ["tid", "added", "institution", "country", "position", "url", "deadline", "status",
            "fit", "supervisor", "report", "next_action", "next_date", "notes"]
OPEN = {"discovered", "evaluated", "shortlisted", "contacted", "drafting"}
SORTS = ["fit", "prefilter", "deadline"]


# ---------- data (no curses below this line until `run`) ----------

def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def days_left(iso):
    try:
        return (dt.date.fromisoformat(iso) - TODAY).days
    except (ValueError, TypeError):
        return None


def due_text(iso):
    d = days_left(iso)
    if d is None:
        return "no deadline"
    return f"{iso} ({'closed' if d < 0 else str(d) + 'd'})"


def gated(p):
    return any(f.startswith("gate-") or f.endswith("-blocks") for f in p.get("flags", []))


def load():
    store = json.loads(STORE.read_text()) if STORE.exists() else {}
    return store, read_csv(TRACKER), read_csv(CONTACTS)


def positions(store, query="", sort="fit", hide_gated=False, floor=15):
    rows = [p for p in store.values()
            if p.get("status") in ("new", "seen", "evaluated", "tracked")
            and (p.get("prefilter", 0) >= floor or p.get("fit"))
            and not (hide_gated and gated(p))
            and (not query or query.lower() in " ".join(
                [p.get("title", ""), p.get("org", ""), p.get("country", ""), p.get("summary", ""), " ".join(p.get("flags", []))]).lower())]
    keys = {
        "fit": lambda p: (-(p.get("fit") or 0), -p.get("prefilter", 0)),
        "prefilter": lambda p: (-p.get("prefilter", 0), -(p.get("fit") or 0)),
        "deadline": lambda p: (p.get("deadline") or "9999", -p.get("prefilter", 0)),
    }
    return sorted(rows, key=keys[sort])


def applications(tracker, query=""):
    rows = [r for r in tracker if not query or query.lower() in " ".join(r.values()).lower()]
    return sorted(rows, key=lambda r: (r["status"] not in OPEN, r.get("deadline") or "9999"))


def due_items(tracker, contacts, store, horizon=30):
    items = []
    for r in tracker:
        d = days_left(r.get("deadline"))
        if r["status"] in OPEN and d is not None and -1 <= d <= horizon:
            items.append((d, "DEADLINE", f"{r['tid']} {r['institution']}", r["position"], r.get("url", "")))
        n = days_left(r.get("next_date"))
        if r.get("next_action") and n is not None and n <= horizon:
            items.append((n, "ACTION", f"{r['tid']} {r['institution']}", r["next_action"], r.get("url", "")))
    for c in contacts:
        sent = days_left(c.get("date"))
        if c.get("status") == "sent" and sent is not None and sent <= -10:
            items.append((0, "FOLLOW-UP", c["name"], f"{c['institution']}: sent {-sent} days ago, no reply logged", ""))
    tracked = {r.get("url") for r in tracker}
    for p in store.values():
        d = days_left(p.get("deadline"))
        if (p.get("fit") or 0) >= 3.8 and p["url"] not in tracked and d is not None and 0 <= d <= horizon:
            items.append((d, "UNTRACKED", f"fit {p['fit']} {p.get('org', '')}", p["title"], p["url"]))
    return sorted(items)


def position_line(p, width):
    fit = f"{p['fit']:.1f}" if p.get("fit") else " - "
    d = days_left(p.get("deadline"))
    dl = "  --" if d is None else ("shut" if d < 0 else f"{d:3d}d")
    mark = "!" if gated(p) else ("*" if p.get("status") == "tracked" else " ")
    head = f"{mark}{fit:>4} {p.get('prefilter', 0):3d} {dl} {p.get('country', '')[:11]:11s} "
    return (head + f"{p.get('title', '')}  ·  {p.get('org', '')}")[:width]


def application_line(r, width):
    d = days_left(r.get("deadline"))
    dl = "  --" if d is None else ("shut" if d < 0 else f"{d:3d}d")
    head = f" {r['tid']:5s}{r['status'][:11]:11s} {r.get('fit') or '-':>4} {dl} "
    return (head + f"{r['institution']}  ·  {r['position']}")[:width]


def due_line(item, width):
    d, kind, who, what, _ = item
    return f" {d:4d}d  {kind:10s} {who}  ·  {what}"[:width]


def position_detail(p):
    out = [p.get("title", ""), f"{p.get('org', '')}, {p.get('country', '')} {p.get('city', '')}".strip(),
           f"Deadline: {due_text(p.get('deadline'))}   Source: {p.get('source')}   Id: {p['id']}",
           f"Fit: {p.get('fit') or 'not scored'}   Prefilter: {p.get('prefilter', 0)}   {p.get('verdict', '')}"]
    if p.get("flags"):
        out.append("Flags: " + ", ".join(p["flags"]))
    if p.get("signals"):
        out.append("Advert says: " + ", ".join(p["signals"]))
    for key, label in (("salary", "Pay"), ("duration", "Duration"), ("degree_line", "Degree"), ("report", "Report")):
        if p.get(key):
            out.append(f"{label}: {p[key]}")
    if p.get("contacts"):
        out.append("Contacts: " + ", ".join(p["contacts"]))
    out += ["", p.get("summary") or p.get("ad_digest", "")[:600], "", p.get("url", "")]
    return out


def application_detail(r):
    out = [r["position"], f"{r['institution']}, {r.get('country', '')}",
           f"Status: {r['status']}   Fit: {r.get('fit') or '-'}   Deadline: {due_text(r.get('deadline'))}"]
    for key, label in (("supervisor", "Supervisor"), ("report", "Report"), ("next_action", "Next"), ("next_date", "By"), ("notes", "Notes")):
        if r.get(key):
            out.append(f"{label}: {r[key]}")
    out += ["", r.get("url", "")]
    return out


def track(store, tracker, p):
    """Same effect as `ops.py track`."""
    if any(r["url"] == p["url"] for r in tracker):
        return "Already tracked."
    nums = [int(r["tid"][1:]) for r in tracker if r.get("tid", "").startswith("A") and r["tid"][1:].isdigit()]
    tid = f"A{max(nums, default=0) + 1:03d}"
    tracker.append({"tid": tid, "added": TODAY.isoformat(), "institution": p.get("org", ""), "country": p.get("country", ""),
                    "position": p["title"], "url": p["url"], "deadline": p.get("deadline", ""), "status": "shortlisted",
                    "fit": p.get("fit", ""), "report": p.get("report", "")})
    with TRACKER.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=T_FIELDS)
        w.writeheader()
        for r in tracker:
            w.writerow({f: r.get(f, "") for f in T_FIELDS})
    p["status"], p["tid"] = "tracked", tid
    STORE.write_text(json.dumps(store, indent=1, ensure_ascii=False))
    return f"Tracked as {tid}."


def dismiss(store, p):
    p["status"], p["dismiss_reason"] = "dismissed", "dismissed in the terminal dashboard"
    STORE.write_text(json.dumps(store, indent=1, ensure_ascii=False))
    return "Dismissed."


def plain(width=118):
    store, tracker, contacts = load()
    pos = positions(store)
    print(f"POSITIONS ({len(pos)})   ! gate-blocked   * tracked\n  fit pre  due country     title · institution")
    for p in pos[:25]:
        print(position_line(p, width))
    print(f"\nAPPLICATIONS ({len(tracker)})")
    for r in applications(tracker):
        print(application_line(r, width))
    items = due_items(tracker, contacts, store)
    print(f"\nDUE IN 30 DAYS ({len(items)})")
    for item in items:
        print(due_line(item, width))


# ---------- interactive ----------

def run(stdscr):
    import curses
    curses.curs_set(0)
    curses.use_default_colors()
    for i, colour in enumerate((curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_RED), 1):
        curses.init_pair(i, colour, -1)
    store, tracker, contacts = load()
    view, sel, top, query, sort, hide, detail, msg = 0, 0, 0, "", 0, False, False, "? for keys"
    names = ["1 Positions", "2 Applications", "3 Due"]

    while True:
        if view == 0:
            rows = positions(store, query, SORTS[sort], hide)
        elif view == 1:
            rows = applications(tracker, query)
        else:
            rows = [i for i in due_items(tracker, contacts, store) if not query or query.lower() in " ".join(map(str, i)).lower()]
        sel = max(0, min(sel, len(rows) - 1))
        h, w = stdscr.getmaxyx()
        detail_h = min(14, max(6, h // 3)) if detail and rows and view < 2 else 0
        body = max(1, h - 4 - detail_h)
        top = min(top, sel)
        if sel >= top + body:
            top = sel - body + 1

        stdscr.erase()
        tabs = "  ".join(f"[{n}]" if i == view else f" {n} " for i, n in enumerate(names))
        stdscr.addnstr(0, 0, f" phd-hunter   {tabs}", w - 1, curses.color_pair(1) | curses.A_BOLD)
        info = f" {len(rows)} rows"
        if view == 0:
            info += f" · sort: {SORTS[sort]} · gate-blocked: {'hidden' if hide else 'shown'}"
        if query:
            info += f" · filter: {query}"
        stdscr.addnstr(1, 0, info, w - 1, curses.A_DIM)
        header = ["  fit pre  due country     title · institution", " id   status       fit  due institution · position", "  days  what       who · detail"][view]
        stdscr.addnstr(2, 0, header, w - 1, curses.A_UNDERLINE)
        for i, row in enumerate(rows[top:top + body]):
            line = [position_line, application_line, due_line][view](row, w - 1)
            attr = curses.A_REVERSE if top + i == sel else 0
            if view == 0 and gated(row):
                attr |= curses.color_pair(4)
            elif view == 0 and (row.get("fit") or 0) >= 3.8:
                attr |= curses.color_pair(2)
            elif view == 2 and row[0] <= 7:
                attr |= curses.color_pair(3)
            stdscr.addnstr(3 + i, 0, line.ljust(w - 1), w - 1, attr)
        if detail_h:
            lines = position_detail(rows[sel]) if view == 0 else application_detail(rows[sel])
            wrapped = [seg for line in lines for seg in (textwrap.wrap(line, w - 3) or [""])]
            y0 = h - 1 - detail_h
            stdscr.addnstr(y0, 0, "─" * (w - 1), w - 1, curses.A_DIM)
            for i, line in enumerate(wrapped[:detail_h - 1]):
                stdscr.addnstr(y0 + 1 + i, 1, line, w - 2)
        stdscr.addnstr(h - 1, 0, f" {msg}".ljust(w - 1), w - 1, curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        msg = ""
        if key in (ord("q"), 3):
            break
        elif key in (curses.KEY_DOWN, ord("j")):
            sel += 1
        elif key in (curses.KEY_UP, ord("k")):
            sel -= 1
        elif key == curses.KEY_NPAGE:
            sel += body
        elif key == curses.KEY_PPAGE:
            sel -= body
        elif key in (ord("1"), ord("2"), ord("3")):
            view, sel, top = key - ord("1"), 0, 0
        elif key == 9:
            view, sel, top = (view + 1) % 3, 0, 0
        elif key in (10, 13, curses.KEY_ENTER):
            detail = not detail
        elif key == ord("s"):
            sort = (sort + 1) % len(SORTS)
        elif key == ord("g"):
            hide = not hide
        elif key == 27:
            query = ""
        elif key == ord("r"):
            store, tracker, contacts = load()
            msg = "Reloaded."
        elif key == ord("?"):
            msg = "j/k move · 1-3 view · Enter details · / filter · s sort · g gates · o open · t track · d dismiss · r reload · q quit"
        elif key == ord("/"):
            curses.echo()
            curses.curs_set(1)
            stdscr.addnstr(h - 1, 0, " filter: ".ljust(w - 1), w - 1)
            query = stdscr.getstr(h - 1, 9, 60).decode("utf-8", "ignore").strip()
            curses.noecho()
            curses.curs_set(0)
            sel = top = 0
        elif rows and key == ord("o"):
            url = rows[sel][4] if view == 2 else rows[sel].get("url", "")
            msg = "Opened in your browser." if url and webbrowser.open(url) else "No link for this row."
        elif rows and view == 0 and key == ord("t"):
            msg = track(store, tracker, rows[sel])
        elif rows and view == 0 and key == ord("d"):
            msg = dismiss(store, rows[sel])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plain", action="store_true", help="print the views and exit (also used when there is no terminal)")
    a = ap.parse_args()
    if a.plain or not sys.stdout.isatty():
        plain()
        return
    import curses
    curses.wrapper(run)


if __name__ == "__main__":
    main()

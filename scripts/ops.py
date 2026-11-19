#!/usr/bin/env python3
"""Pipeline bookkeeping: scanned postings, the application tracker, contacts.

  postings [--all] [--min N] [--country C]      list scanned postings by prefilter score
  show ID                                       full record for one posting
  score ID FIT [--report PATH] [--verdict V]    store an evaluated fit score (1.0-5.0)
  dismiss ID [reason]                           hide a posting from future lists
  track ID [--status S]                         copy a posting into the tracker
  add --inst I --position P [--url U ...]       add a tracker row by hand
  set TID field=value [field=value ...]         update a tracker row
  list [--status S]                             show the tracker
  due [--days N]                                deadlines and next actions coming up
  contact --name N --inst I [--role R --email E --tid T --status S --notes X]
  contacts                                      list outreach contacts
  stats                                         funnel, answer rates, patterns by country and fit
  ics [--min-fit 3.8]                           write data/deadlines.ics for your calendar app

Standard library only. Nothing here sends or submits anything.
"""
import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "data" / "postings.json"
TRACKER = ROOT / "data" / "tracker.csv"
CONTACTS = ROOT / "data" / "contacts.csv"
TODAY = dt.date.today()

T_FIELDS = ["tid", "added", "institution", "country", "position", "url", "deadline", "status",
            "fit", "supervisor", "report", "next_action", "next_date", "notes"]
C_FIELDS = ["name", "role", "institution", "email", "tid", "channel", "status", "date", "notes"]
STATUSES = ["discovered", "evaluated", "shortlisted", "contacted", "drafting", "applied",
            "interview", "offer", "accepted", "rejected", "withdrawn", "expired", "skipped", "unverified"]


def load_store():
    return json.loads(STORE.read_text()) if STORE.exists() else {}


def save_store(store):
    STORE.write_text(json.dumps(store, indent=1, ensure_ascii=False))


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({f: r.get(f, "") for f in fields})


def next_tid(rows):
    nums = [int(r["tid"][1:]) for r in rows if r.get("tid", "").startswith("A") and r["tid"][1:].isdigit()]
    return f"A{max(nums, default=0) + 1:03d}"


def days_left(iso):
    try:
        return (dt.date.fromisoformat(iso) - TODAY).days
    except (ValueError, TypeError):
        return None


def upcoming(iso):
    """True for today or later (a deadline today still counts)."""
    d = days_left(iso)
    return d is not None and d >= 0


def find(store, pid):
    if pid in store:
        return store[pid]
    matches = [p for k, p in store.items() if k.endswith(pid) or pid in k]
    if len(matches) == 1:
        return matches[0]
    sys.exit(f"No unique posting for '{pid}' ({len(matches)} matches).")


def cmd_postings(a):
    store = load_store()
    rows = [p for p in store.values()
            if (a.all or p.get("status") in ("new", "seen", "evaluated"))
            and p.get("prefilter", 0) >= a.min
            and (not a.country or a.country.lower() in p.get("country", "").lower())]
    rows.sort(key=lambda p: (-(p.get("fit") or 0), -p.get("prefilter", 0)))
    for p in rows[:a.limit]:
        fit = f"fit {p['fit']:.1f}" if p.get("fit") else "      "
        d = days_left(p.get("deadline"))
        dl = f"{p['deadline']} ({d}d)" if d is not None else "no deadline"
        print(f"{p.get('prefilter', 0):3d} {fit:8s} {p['id']:26s} {p['title'][:70]}")
        print(f"     {p.get('org', '')[:44]} | {p.get('country', '')} | {dl} | {p.get('status')} {' '.join(p.get('flags', []))}")
        extra = [x for x in p.get("signals", []) if not x.startswith("lang-required")]
        if p.get("salary"):
            extra.append("pay: " + p["salary"][:60])
        if extra:
            print(f"     {'; '.join(extra)}")
    print(f"\n{len(rows)} postings match ({len(store)} stored).")


def cmd_show(a):
    print(json.dumps(find(load_store(), a.id), indent=2, ensure_ascii=False))


def cmd_score(a):
    store = load_store()
    p = find(store, a.id)
    if not 1.0 <= a.fit <= 5.0:
        sys.exit("Fit must be between 1.0 and 5.0.")
    p["fit"], p["status"] = round(a.fit, 1), "evaluated"
    if a.report:
        p["report"] = a.report
    if a.verdict:
        p["verdict"] = a.verdict
    save_store(store)
    print(f"{p['id']}: fit {p['fit']} recorded.")


def cmd_dismiss(a):
    store = load_store()
    p = find(store, a.id)
    p["status"], p["dismiss_reason"] = "dismissed", " ".join(a.reason)
    save_store(store)
    print(f"{p['id']} dismissed.")


def cmd_track(a):
    store = load_store()
    p = find(store, a.id)
    rows = read_csv(TRACKER)
    if any(r["url"] == p["url"] for r in rows):
        sys.exit("Already in the tracker.")
    tid = next_tid(rows)
    rows.append({"tid": tid, "added": TODAY.isoformat(), "institution": p.get("org", ""),
                 "country": p.get("country", ""), "position": p["title"], "url": p["url"],
                 "deadline": p.get("deadline", ""), "status": a.status,
                 "fit": p.get("fit", ""), "report": p.get("report", "")})
    write_csv(TRACKER, T_FIELDS, rows)
    p["status"], p["tid"] = "tracked", tid
    save_store(store)
    print(f"Tracked as {tid}.")


def cmd_add(a):
    rows = read_csv(TRACKER)
    tid = next_tid(rows)
    rows.append({"tid": tid, "added": TODAY.isoformat(), "institution": a.inst, "country": a.country,
                 "position": a.position, "url": a.url, "deadline": a.deadline, "status": a.status,
                 "supervisor": a.supervisor, "notes": a.notes})
    write_csv(TRACKER, T_FIELDS, rows)
    print(f"Added {tid}.")


def cmd_set(a):
    rows = read_csv(TRACKER)
    row = next((r for r in rows if r["tid"].lower() == a.tid.lower()), None)
    if not row:
        sys.exit(f"No tracker row {a.tid}.")
    for pair in a.pairs:
        key, _, value = pair.partition("=")
        if key not in T_FIELDS or key == "tid":
            sys.exit(f"Unknown field '{key}'. Fields: {', '.join(T_FIELDS[1:])}")
        if key == "status" and value not in STATUSES:
            sys.exit(f"Unknown status '{value}'. Use one of: {', '.join(STATUSES)}")
        row[key] = value
    write_csv(TRACKER, T_FIELDS, rows)
    print(f"{row['tid']} updated.")


def cmd_list(a):
    rows = [r for r in read_csv(TRACKER) if not a.status or r["status"] == a.status]
    for r in rows:
        d = days_left(r.get("deadline"))
        dl = f"{r['deadline']} ({d}d)" if d is not None else "-"
        print(f"{r['tid']}  {r['status']:11s} fit {r.get('fit') or '-':4s} {r['institution'][:30]:30s} {r['position'][:46]:46s} {dl}")
        if r.get("next_action"):
            print(f"      next: {r['next_action']} {r.get('next_date', '')}")
    print(f"\n{len(rows)} rows.")


def cmd_due(a):
    open_states = {"discovered", "evaluated", "shortlisted", "contacted", "drafting"}
    items = []
    for r in read_csv(TRACKER):
        d = days_left(r.get("deadline"))
        if r["status"] in open_states and d is not None and -1 <= d <= a.days:
            items.append((d, f"DEADLINE  {r['tid']} {r['institution'][:28]} - {r['position'][:44]} ({r['status']})"))
        n = days_left(r.get("next_date"))
        if r.get("next_action") and n is not None and n <= a.days:
            items.append((n, f"ACTION    {r['tid']} {r['next_action']} ({r['institution'][:28]})"))
    for c in read_csv(CONTACTS):
        sent = days_left(c.get("date"))
        if c.get("status") == "sent" and sent is not None and sent <= -10:
            items.append((0, f"FOLLOW-UP {c['name']} ({c['institution']}), sent {-sent} days ago, no reply logged"))
    for d, line in sorted(items):
        print(f"{d:4d}d  {line}")
    if not items:
        print(f"Nothing due in the next {a.days} days.")


def cmd_ics(a):
    """Write data/deadlines.ics: import it into any calendar app, or subscribe to the file."""
    def event(uid, day, title, note, alarm_days):
        d = dt.date.fromisoformat(day)
        return ["BEGIN:VEVENT", f"UID:{uid}@phd-hunter", f"DTSTAMP:{TODAY.strftime('%Y%m%d')}T000000Z",
                f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}", f"DTEND;VALUE=DATE:{(d + dt.timedelta(days=1)).strftime('%Y%m%d')}",
                "SUMMARY:" + title.replace(",", "\\,")[:120], "DESCRIPTION:" + note.replace(",", "\\,").replace("\n", " ")[:400],
                "BEGIN:VALARM", "ACTION:DISPLAY", f"TRIGGER:-P{alarm_days}D", "DESCRIPTION:" + title[:80], "END:VALARM", "END:VEVENT"]
    lines, n = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//phd-hunter//EN", "X-WR-CALNAME:PhD deadlines"], 0
    open_states = {"discovered", "evaluated", "shortlisted", "contacted", "drafting"}
    tracked_urls = set()
    for r in read_csv(TRACKER):
        tracked_urls.add(r.get("url"))
        if r["status"] in open_states and upcoming(r.get("deadline")):
            lines += event(r["tid"], r["deadline"], f"PhD deadline: {r['institution']} ({r['tid']})",
                           f"{r['position']} | fit {r.get('fit') or '-'} | {r.get('url', '')}", 3)
            n += 1
        if r.get("next_action") and upcoming(r.get("next_date")):
            lines += event(r["tid"] + "-next", r["next_date"], f"{r['tid']}: {r['next_action']}", r["institution"], 1)
            n += 1
    for pid, p in load_store().items():
        if (p.get("fit") or 0) >= a.min_fit and p["url"] not in tracked_urls and upcoming(p.get("deadline")):
            lines += event(pid, p["deadline"], f"PhD deadline (not tracked, fit {p['fit']}): {p.get('org', '')}",
                           f"{p['title']} | {p['url']}", 5)
            n += 1
    lines.append("END:VCALENDAR")
    out = ROOT / "data" / "deadlines.ics"
    out.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)} with {n} events.")


def cmd_stats(a):
    """Funnel and patterns: where applications stop, and what the outcomes have in common."""
    rows = read_csv(TRACKER)
    if not rows:
        sys.exit("The tracker is empty.")
    order = ["discovered", "evaluated", "shortlisted", "contacted", "drafting", "applied", "interview", "offer", "accepted",
             "rejected", "withdrawn", "expired", "skipped", "unverified"]
    by = {s: [r for r in rows if r["status"] == s] for s in order}
    print("Funnel")
    for s in order:
        if by[s]:
            print(f"  {s:11s} {len(by[s]):3d}  {'#' * len(by[s])}")
    sent = sum(len(by[s]) for s in ("applied", "interview", "offer", "accepted", "rejected"))
    heard = sum(len(by[s]) for s in ("interview", "offer", "accepted", "rejected"))
    advanced = sum(len(by[s]) for s in ("interview", "offer", "accepted"))
    if sent:
        print(f"\nSubmitted {sent}; answered {heard} ({100 * heard // sent}%); reached interview or beyond {advanced} ({100 * advanced // sent}%).")

    def fits(group):
        vals = [float(r["fit"]) for r in group if r.get("fit")]
        return f"{sum(vals) / len(vals):.1f} (n={len(vals)})" if vals else "-"
    good, bad = by["interview"] + by["offer"] + by["accepted"], by["rejected"]
    if good or bad:
        print(f"Average fit score: advanced {fits(good)}; rejected {fits(bad)}.")
    print("\nBy country (submitted / advanced / rejected)")
    countries = sorted({r["country"] or "?" for r in rows})
    for c in countries:
        rs = [r for r in rows if (r["country"] or "?") == c]
        sub = sum(r["status"] in ("applied", "interview", "offer", "accepted", "rejected") for r in rs)
        adv = sum(r["status"] in ("interview", "offer", "accepted") for r in rs)
        rej = sum(r["status"] == "rejected" for r in rs)
        if sub:
            print(f"  {c:16s} {sub} / {adv} / {rej}")
    contacts = read_csv(CONTACTS)
    if contacts:
        out = sum(c["status"] in ("sent", "replied", "closed") for c in contacts)
        rep = sum(c["status"] == "replied" for c in contacts)
        print(f"\nOutreach: {out} sent, {rep} replied" + (f" ({100 * rep // out}%)." if out else "."))
        with_contact = {c["tid"] for c in contacts if c["status"] in ("sent", "replied") and c.get("tid")}
        if with_contact and sent:
            a1 = sum(r["tid"] in with_contact and r["status"] in ("interview", "offer", "accepted") for r in rows)
            n1 = sum(r["tid"] in with_contact and r["status"] in ("applied", "interview", "offer", "accepted", "rejected") for r in rows)
            if n1:
                print(f"Applications preceded by outreach: {a1} of {n1} advanced.")
    if sent < 5:
        print("\nFewer than 5 submitted applications: too few to read a pattern from.")


def cmd_contact(a):
    rows = read_csv(CONTACTS)
    rows.append({"name": a.name, "role": a.role, "institution": a.inst, "email": a.email, "tid": a.tid,
                 "channel": a.channel, "status": a.status, "date": TODAY.isoformat(), "notes": a.notes})
    write_csv(CONTACTS, C_FIELDS, rows)
    print(f"Contact saved: {a.name} ({a.status}).")


def cmd_contacts(a):
    for c in read_csv(CONTACTS):
        print(f"{c['date']}  {c['status']:8s} {c['name'][:28]:28s} {c['role'][:22]:22s} {c['institution'][:28]:28s} {c['tid']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("postings"); s.add_argument("--all", action="store_true"); s.add_argument("--min", type=int, default=15)
    s.add_argument("--country", default=""); s.add_argument("--limit", type=int, default=40); s.set_defaults(fn=cmd_postings)
    s = sub.add_parser("show"); s.add_argument("id"); s.set_defaults(fn=cmd_show)
    s = sub.add_parser("score"); s.add_argument("id"); s.add_argument("fit", type=float)
    s.add_argument("--report", default=""); s.add_argument("--verdict", default=""); s.set_defaults(fn=cmd_score)
    s = sub.add_parser("dismiss"); s.add_argument("id"); s.add_argument("reason", nargs="*"); s.set_defaults(fn=cmd_dismiss)
    s = sub.add_parser("track"); s.add_argument("id"); s.add_argument("--status", default="shortlisted", choices=STATUSES); s.set_defaults(fn=cmd_track)
    s = sub.add_parser("add"); s.add_argument("--inst", required=True); s.add_argument("--position", required=True)
    for opt in ("country", "url", "deadline", "supervisor", "notes"):
        s.add_argument(f"--{opt}", default="")
    s.add_argument("--status", default="discovered", choices=STATUSES); s.set_defaults(fn=cmd_add)
    s = sub.add_parser("set"); s.add_argument("tid"); s.add_argument("pairs", nargs="+"); s.set_defaults(fn=cmd_set)
    s = sub.add_parser("list"); s.add_argument("--status", default=""); s.set_defaults(fn=cmd_list)
    s = sub.add_parser("due"); s.add_argument("--days", type=int, default=14); s.set_defaults(fn=cmd_due)
    s = sub.add_parser("contact"); s.add_argument("--name", required=True); s.add_argument("--inst", required=True)
    for opt in ("role", "email", "tid", "notes"):
        s.add_argument(f"--{opt}", default="")
    s.add_argument("--channel", default="email"); s.add_argument("--status", default="drafted", choices=["drafted", "sent", "replied", "closed"])
    s.set_defaults(fn=cmd_contact)
    s = sub.add_parser("contacts"); s.set_defaults(fn=cmd_contacts)
    s = sub.add_parser("stats"); s.set_defaults(fn=cmd_stats)
    s = sub.add_parser("ics"); s.add_argument("--min-fit", type=float, default=3.8); s.set_defaults(fn=cmd_ics)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

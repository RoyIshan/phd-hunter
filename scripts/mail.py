#!/usr/bin/env python3
"""Email without handing over your mailbox.

  draft FILE.md [--to ADDRESS] [--attach FILE ...]
      Turn an outreach draft into an unsent .eml file (opens as a draft in
      Apple Mail, Outlook, Thunderbird) and print a mailto: link. Nothing is
      sent: you open it, read it, and press send yourself.

  inbox PATH [PATH ...] [--apply]
      Read emails you saved or exported (.eml files, an .mbox, or a folder of
      them), work out which application each one is about and what it means
      (rejection, interview invitation, offer, receipt, request for documents,
      a reply from a supervisor), and print proposed tracker updates.
      With --apply the proposals are written to the tracker; without it,
      nothing changes.

There is no mail server code here: no passwords, no IMAP, no sending. To get
mail in: drag messages from your mail app into data/inbox/mail/, or export a
folder as .mbox. If your assistant has a mail connector, `modes/inbox.md`
uses that instead, read-only.

Draft format (what modes/outreach.md writes):

    Subject: PhD position in X (ref 123)
    To: name@university.example        <- optional

    Dear Professor ...
"""
import argparse
import csv
import datetime as dt
import email
import email.policy
import mailbox
import re
import sys
import urllib.parse
from email.message import EmailMessage
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACKER = ROOT / "data" / "tracker.csv"
CONTACTS = ROOT / "data" / "contacts.csv"
T_FIELDS = ["tid", "added", "institution", "country", "position", "url", "deadline", "status",
            "fit", "supervisor", "report", "next_action", "next_date", "notes"]

# Order matters: the first kind that matches wins.
KINDS = [
    ("offer", "offer", r"pleased to offer|we would like to offer you|offer of (?:employment|a position|admission)|you have been selected for the position|"
                       r"happy to inform you that you (?:have been|were) (?:selected|chosen)|formal offer"),
    ("rejection", "rejected", r"regret to inform|unfortunately|not (?:been )?(?:selected|shortlisted|successful)|will not be (?:proceeding|taking|moving)|"
                              r"decided (?:not )?to (?:proceed|continue) with (?:other|another)|other candidates?|position has been filled|"
                              r"we have chosen another|not to (?:invite|pursue)|unable to offer"),
    ("interview", "interview", r"invite you (?:to|for) (?:an? )?(?:online |digital |video |on-?site |first |second )?(?:interview|conversation|meeting|talk)|"
                               r"interview (?:will take place|is scheduled|on \w+)|would like to (?:interview|meet|speak with) you|shortlisted|"
                               r"selection (?:interview|day)|schedule (?:an? )?(?:interview|call)"),
    ("documents", None, r"please (?:send|provide|upload|submit) (?:us )?(?:your |the |a )?(?:missing|additional|following)|incomplete application|"
                        r"missing (?:documents?|transcripts?|references?)|could you (?:send|provide)"),
    ("receipt", "applied", r"(?:we have |has been )?(?:successfully )?received your application|thank you for (?:your application|applying)|"
                           r"application (?:has been|was) (?:submitted|registered|received)|confirmation of (?:your )?application|automatic(?:ally generated)? (?:reply|message)"),
]
RANK = ["discovered", "evaluated", "shortlisted", "contacted", "drafting", "applied", "interview", "offer", "accepted"]


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------- draft ----------

def parse_draft(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    headers, i = {}, 0
    while i < len(lines) and (not lines[i].strip() or lines[i].startswith("#") or re.match(r"^\**(Subject|To|Cc)\**\s*:", lines[i], re.I)):
        m = re.match(r"^\**(Subject|To|Cc)\**\s*:\**\s*(.*)$", lines[i], re.I)
        if m:
            headers[m.group(1).lower()] = m.group(2).strip().strip("*")
        i += 1
    body = "\n".join(lines[i:])
    # Stop at a follow-up section or notes: only the first message goes into the draft.
    body = re.split(r"\n(?:#+ |\*\*)?(?:Follow[- ]up|Notes?|Sources?)\b", body, flags=re.I)[0]
    body = re.sub(r"\*\*(.+?)\*\*|\*(.+?)\*", lambda m: m.group(1) or m.group(2), body).strip()
    return headers, body


def cmd_draft(a):
    path = Path(a.file)
    headers, body = parse_draft(path)
    to = a.to or headers.get("to", "")
    subject = headers.get("subject", "")
    if not subject:
        sys.exit("The draft has no 'Subject:' line. Add one at the top.")
    if "[CHECK" in body or "[CHECK" in subject:
        sys.exit("The draft still contains [CHECK ...] placeholders. Resolve them first.")
    msg = EmailMessage()
    msg["Subject"], msg["To"] = subject, to
    if headers.get("cc"):
        msg["Cc"] = headers["cc"]
    msg["X-Unsent"] = "1"  # mail apps open the file as an editable draft
    msg.set_content(body + "\n")
    for attach in a.attach or []:
        f = Path(attach)
        msg.add_attachment(f.read_bytes(), maintype="application", subtype="octet-stream", filename=f.name)
    out = path.with_suffix(".eml")
    out.write_bytes(msg.as_bytes())
    print(f"Draft written: {out}\nOpen it in your mail app, read it, and send it yourself.")
    if not to:
        print("No recipient set: add the address in your mail app (take it from the person's institutional page).")
    link = f"mailto:{urllib.parse.quote(to)}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    if len(link) < 1900:
        print(f"\nOr use this link (no attachments):\n{link}")


# ---------- inbox ----------

def messages(paths):
    for raw in paths:
        path = Path(raw).expanduser()
        files = sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]
        for f in files:
            if f.suffix.lower() == ".eml":
                yield f.name, email.message_from_bytes(f.read_bytes(), policy=email.policy.default)
            elif f.suffix.lower() == ".mbox":
                for i, m in enumerate(mailbox.mbox(str(f))):
                    yield f"{f.name}#{i + 1}", email.message_from_bytes(m.as_bytes(), policy=email.policy.default)


def body_text(msg):
    part = msg.get_body(preferencelist=("plain", "html"))
    if part is None:
        return ""
    text = part.get_content()
    if part.get_content_type() == "text/html":
        text = re.sub(r"<(script|style)\b.*?</\1>", " ", text, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
    text = re.split(r"\n(?:On .{10,80} wrote:|-----Original Message-----|From: .+\nSent: )", text)[0]  # drop quoted history
    return re.sub(r"[ \t]+", " ", text).strip()


def classify(subject, text):
    blob = (subject + "\n" + text[:3000]).lower()
    for kind, status, pattern in KINDS:
        m = re.search(pattern, blob)
        if m:
            return kind, status, m.group(0)
    return "other", None, ""


def keywords(name):
    stop = {"university", "universiteit", "universität", "universitet", "the", "of", "and", "for", "department", "dept",
            "institute", "school", "technology", "science", "sciences", "phd", "position", "doctoral", "candidate", "student"}
    return {w for w in re.findall(r"[a-zà-ÿ]{4,}", name.lower()) if w not in stop}


def match(sender, subject, text, tracker, contacts):
    """Which tracker row is this about? Returns (row, why) or (None, '')."""
    addr = parseaddr(sender)[1].lower()
    domain = addr.split("@")[-1]
    for c in contacts:
        if c.get("email") and c["email"].lower() == addr and c.get("tid"):
            row = next((r for r in tracker if r["tid"] == c["tid"]), None)
            if row:
                return row, f"sender is the logged contact {c['name']}"
    blob = (subject + " " + text[:2500]).lower()
    best, best_score, why = None, 0, ""
    for r in tracker:
        score, reasons = 0, []
        host = re.sub(r"^https?://(www\.)?", "", r.get("url", "")).split("/")[0].lower()
        if host and domain and (domain.endswith(host) or host.endswith(domain)) and not re.search(r"euraxess|academictransfer|jobbnorge|academicpositions|jobs\.ac\.uk|varbi", host):
            score += 3
            reasons.append("sender domain matches the advert")
        inst = keywords(r["institution"])
        if any(re.search(rf"(^|\.){re.escape(w)}\.", domain) for w in inst):
            score += 3
            reasons.append("sender domain names the institution")
        elif inst and len({w for w in inst if w in blob}) >= max(1, min(2, len(inst))):
            score += 2
            reasons.append("institution named")
        pos = keywords(r["position"])
        hit = {w for w in pos if w in blob}
        if pos and len(hit) >= max(2, len(pos) // 2):
            score += 2
            reasons.append("position title words")
        ref = re.search(r"\b(?:ref(?:erence)?\.?|vacancy|job)\s*(?:no\.?|number|id|:)?\s*([A-Z0-9][A-Z0-9/-]{3,})", r["position"] + " " + r.get("notes", ""), flags=re.I)
        if ref and ref.group(1).lower() in blob:
            score += 4
            reasons.append(f"reference {ref.group(1)}")
        if score > best_score:
            best, best_score, why = r, score, ", ".join(reasons)
    return (best, why) if best_score >= 3 else (None, "")


def cmd_inbox(a):
    tracker, contacts = read_csv(TRACKER), read_csv(CONTACTS)
    if not tracker:
        sys.exit("The tracker is empty: nothing to match emails against.")
    proposals, unmatched, n = [], [], 0
    for name, msg in messages(a.paths):
        n += 1
        subject, sender = str(msg.get("Subject", "")), str(msg.get("From", ""))
        text = body_text(msg)
        try:
            date = parsedate_to_datetime(msg.get("Date")).date().isoformat()
        except (TypeError, ValueError):
            date = dt.date.today().isoformat()
        kind, status, evidence = classify(subject, text)
        row, why = match(sender, subject, text, tracker, contacts)
        if kind == "other" and row and any(c.get("email", "").lower() == parseaddr(sender)[1].lower() for c in contacts):
            kind = "reply"
        if not row:
            if kind in ("offer", "interview", "rejection", "documents") and re.search(r"application|applicant|candidate|phd|doctoral|vacancy", (subject + text[:1500]).lower()):
                unmatched.append((name, kind, subject[:70], parseaddr(sender)[1]))
            continue
        proposals.append({"file": name, "date": date, "tid": row["tid"], "inst": row["institution"], "kind": kind,
                          "status": status, "current": row["status"], "evidence": evidence, "why": why,
                          "subject": subject[:80], "sender": parseaddr(sender)[1]})
    if not n:
        sys.exit("No .eml or .mbox files found there.")

    print(f"{n} message(s) read, {len(proposals)} matched to an application.\n")
    changes = []
    for p in sorted(proposals, key=lambda p: p["date"]):
        cur, new = p["current"], p["status"]
        place = RANK.index(cur) if cur in RANK else -1  # unverified, expired, skipped: anything is news
        forward = bool(new) and (new == "rejected" and cur not in ("rejected", "accepted", "withdrawn")
                                 or new in RANK and cur not in ("rejected", "accepted", "withdrawn") and RANK.index(new) > place)
        action = f"set status {cur} -> {new}" if forward else {
            "documents": "they ask for something: read it and reply", "reply": "a contact replied: read it, then update the contact",
            "other": "no status change", }.get(p["kind"], f"already {cur}: no change")
        print(f"{p['date']}  {p['tid']} {p['inst'][:34]:34s} {p['kind'].upper():10s} {action}")
        print(f"            \"{p['subject']}\" from {p['sender']}")
        print(f"            matched because: {p['why']}" + (f"; wording: \"{p['evidence'][:60]}\"" if p["evidence"] else ""))
        if forward:
            changes.append(p)
    for name, kind, subject, sender in unmatched:
        print(f"UNMATCHED   {kind.upper():10s} \"{subject}\" from {sender} ({name}): no tracked application fits; add it or ignore")

    if not changes:
        print("\nNo status changes to make.")
        return
    if not a.apply:
        print(f"\n{len(changes)} status change(s) proposed. Check each against the email, then rerun with --apply, "
              "or set them one by one with scripts/ops.py set. An offer is recorded as 'offer': accepting is your decision.")
        return
    for p in changes:
        row = next(r for r in tracker if r["tid"] == p["tid"])
        row["status"] = p["status"]
        row["notes"] = (row.get("notes", "") + f" | {p['date']} email: {p['kind']} (\"{p['subject'][:50]}\")").strip(" |")
    with TRACKER.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=T_FIELDS)
        w.writeheader()
        for r in tracker:
            w.writerow({f: r.get(f, "") for f in T_FIELDS})
    print(f"\n{len(changes)} tracker row(s) updated.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("draft"); s.add_argument("file"); s.add_argument("--to", default=""); s.add_argument("--attach", nargs="*")
    s.set_defaults(fn=cmd_draft)
    s = sub.add_parser("inbox"); s.add_argument("paths", nargs="+"); s.add_argument("--apply", action="store_true")
    s.set_defaults(fn=cmd_inbox)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

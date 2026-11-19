# Mode: status

Tracker overview, deadlines, follow-ups and outcomes. Input: an optional
update in plain words ("A003 rejected", "sent the email to Prof X").

1. Apply any update with `python3 scripts/ops.py set <tid> ...` (statuses:
   discovered, evaluated, shortlisted, contacted, drafting, applied, interview,
   offer, accepted, rejected, withdrawn, expired, skipped, unverified) or
   `ops.py contact ... --status sent|replied`. Confirm what changed.
2. Run `python3 scripts/ops.py list`, `python3 scripts/ops.py due --days 21`,
   `python3 scripts/ops.py contacts`, `python3 scripts/ops.py stats` and
   `python3 scripts/alive.py` (flags positions that closed or cannot be read).
3. Rows marked `unverified` were inferred, not confirmed. Ask once what
   actually happened and update them.
4. Report briefly:
   - **This week:** deadlines and next actions in date order
   - **Waiting:** applied with no answer, with days elapsed; suggest a polite
     enquiry only after the stated decision date, or after 4-6 weeks
   - **Follow-ups due:** outreach sent 7-10 working days ago with no reply
   - **Funnel:** counts by status
5. After three or more rejections, look for a pattern across the reports
   (stage reached, field, country, requirement gaps) and say what to change:
   targeting, the letter's angle, or a gap to close. If the pattern points at
   the search itself, propose edits to `config/search.json`.
6. If saved mail is waiting in `data/inbox/mail/`, run the `inbox` mode first.
7. Run `python3 scripts/dashboard.py` and `python3 scripts/ops.py ics`; point
   to `dashboard.html`, `data/deadlines.ics`, and `python3 scripts/tui.py` for
   the terminal view.

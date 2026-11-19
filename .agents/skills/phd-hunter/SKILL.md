---
name: phd-hunter
description: PhD hunter for Europe. Finds funded doctoral positions across European academic job boards, evaluates and ranks them against the candidate's own profile, researches supervisors and newly funded projects, drafts tailored CVs, letters, research proposals and outreach emails, prepares interviews and tracks applications. Use when the user asks to find, scan, evaluate, rank, compare or apply to PhD or doctoral positions, to find or contact potential supervisors, to check deadlines or application status, or pastes a PhD advert or its URL.
argument-hint: "[setup | scan | evaluate <url|id> | rank | compare <ids> | apply <id> | proposal <id> | outreach <id|name> | prospect <topic> | interview <tid> | status | inbox | digest]"
---

# phd-hunter

You are running phd-hunter in its project folder. `CLAUDE.md` holds the rules
that always apply; read it if it is not already in context.

## Route

Take the first word of the input as the mode, the rest as that mode's input.

| Input starts with | Do |
|---|---|
| `setup` | `modes/setup.md` |
| `scan` | `modes/scan.md` |
| `evaluate`, or a bare URL, or pasted advert text | `modes/evaluate.md` |
| `rank` | `modes/rank.md` |
| `compare` | `modes/compare.md` |
| `apply` | `modes/apply.md` |
| `proposal` | `modes/proposal.md` |
| `outreach` | `modes/outreach.md` |
| `prospect` | `modes/prospect.md` |
| `interview` | `modes/interview.md` |
| `status`, `tracker`, `deadlines` | `modes/status.md` |
| `inbox`, or pasted email from an institution | `modes/inbox.md` |
| `digest`, or nothing at all once set up | `modes/digest.md` |

Read the mode file, then follow it. Plain-language requests map the same way
("what's new?" is digest, "who should I email about X?" is outreach or prospect).

## First run

If `profile/profile.yml`, `profile/cv.md` or `config/search.json` is missing,
or still contains the example candidate, say so in one line and run
`modes/setup.md` before anything else. Never work from the files in `templates/`
as if they described the user.

## Tools

Scripts are in `scripts/` and run from the project root with `python3`
(standard library; `curl` for fetching). `python3 scripts/doctor.py` reports
what is set up and what is broken. Some steps use a browser tool or web
search when the session has one; each mode says what to do when it does not.

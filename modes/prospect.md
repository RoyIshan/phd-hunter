# Mode: prospect

Find supervisors, groups and newly funded projects on a topic before a
position is advertised. Input: a topic and optionally countries. With no
topic, use the themes in `profile/profile.yml`, two or three at a time.

Many funded places go to people who wrote to the group before or just as the
advert appeared. This mode builds that list.

1. **Who publishes on it.** `python3 scripts/prospect.py scholars "<topic>" --save`
   (`--countries NL,DE,...` to narrow). Try two phrasings; the ranking depends
   on the wording.
2. **What just got funded.** `python3 scripts/prospect.py projects "<topic>" --save`.
   New grants hire in their first year. Note doctoral networks (DN) and ERC
   grants. For a DN, check each host against `msca_blocked_countries` in
   `config/search.json`: a blocked host rules out that position, not the network.
3. **Shortlist 5-8 groups.** Drop industry authors, people outside
   universities and research institutes, and anyone whose papers match the
   words but not the theme. For each remaining lead:
   - `python3 scripts/prospect.py author "<name>" --inst "<university>"`
   - open their institutional page and group page (`scripts/fetch.py` or the
     browser): role, whether they supervise PhDs, current projects, any
     vacancy or "prospective students" note
   - for a project: its CORDIS page and its own website; which universities
     are partners and who leads the relevant work package
4. **Write** `reports/prospects-<topic-slug>-shortlist.md`:

   | Group lead | Institution, country | Why relevant (two papers or the project) | Funding signal | Open or upcoming PhD? | Contact route | Sources |

   Rank by closeness to the candidate's themes first, funding signal second.
   Mark every cell not read on the person's or project's own page as unverified.
5. Recommend the top three to write to and why. Offer `outreach <name>` for
   each; do not draft here.

Leads from OpenAlex and CORDIS are starting points. Author records can be
merged or split wrongly, and a matching title is not proof of fit.

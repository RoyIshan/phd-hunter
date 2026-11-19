# Fit rubric

Used by `evaluate` (full report) and `rank` (short form). Everything is judged
against `profile/profile.yml` and `profile/cv.md`. Score each dimension 1-5
with one line of evidence, then compute the weighted total.

## Step 0: gates (run first; any failure caps the total at 2.0)

| Gate | Fail when |
|---|---|
| Open | Deadline passed, advert withdrawn, or position filled |
| Role | Not a doctoral-level post (postdoc, professor, technician), or one the profile lists under `not_wanted` |
| Funding | Self-funded or fee-charging with no stipend when the profile wants funded only; or funding restricted to a nationality, residency or fee status the candidate does not hold |
| Degree | Requires a degree field the candidate's degrees cannot reasonably satisfy |
| Mobility | MSCA Doctoral Network hosted in a country listed in `countries_resided_over_12_months_in_last_36` |
| Language | Requires a working language not in the candidate's languages at about B2 or better |
| Credits and grades | A country or programme rule on master's length, credits, thesis size or minimum grade is not met (`reference/countries.md`) |
| Deal-breaker | Anything in `targets.deal_breakers` |

Unknown is not a pass. Mark it `CHECK`, say who can answer it (the candidate or
the advert's contact person), and do not cap the score for it.

## Dimensions

| # | Dimension | Default weight | 5 looks like | 1 looks like |
|---|---|---|---|---|
| 1 | Research fit | 30% | The project question is one of the candidate's `research.themes` | Outside their primary and adjacent fields |
| 2 | Methods fit | 15% | Core methods are in `methods_strong`; the rest within `methods_working` | The core depends on `methods_gap` |
| 3 | Eligibility and requirements | 15% | Every stated requirement met from the CV; documents on hand | Several requirements unmet, or a required document cannot be produced in time |
| 4 | Supervisor and group | 15% | Active, publishing group in the area; supervisor's recent work connects to the candidate's; signs of good supervision (completed PhDs, co-authored student papers) | No identifiable supervisor, inactive group, or work unrelated to the advert |
| 5 | Funding and conditions | 10% | Employed or fully funded for the whole duration at the national rate; reasonable duties | Short or partial funding, unclear contract |
| 6 | Odds | 10% | Profile matches what the advert asks; several positions or a broad call | Reads as written for a specific person; demands a record the candidate lacks |
| 7 | Place and life | 5% | Preferred country, workable language, clear permit route | Low pay against cost of living, language barrier outside work, permit obstacles |

Total = sum(weight × score), one decimal. If `rubric_weights` is set in the
profile, use those weights and say so in the report.

In short-form ranking, dimension 4 is a neutral 3 unless the supervisor's page
was read.

## Verdict bands

- **4.3 - 5.0 Apply, priority.** Write to the supervisor first if time allows.
- **3.8 - 4.2 Apply.** Tailor carefully; address the main gap in the letter.
- **3.5 - 3.7 Maybe.** Only if the pack is cheap to produce or outreach gets a warm reply.
- **Below 3.5 Skip.** Say which dimension sank it.

## What an honest evaluation names

- The single strongest reason the candidate would be shortlisted.
- The single most likely reason they would not be.
- What would change the score (a reply from the supervisor, a clarified requirement).
- What was not read or could not be verified.

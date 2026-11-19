# Mode: rank

Batch-score the best unscored postings into a ranked shortlist. Input:
optional count (default 10) and a country filter.

1. `python3 scripts/enrich.py` so every candidate posting has its advert read
   and gate flags set. Then `python3 scripts/ops.py postings --min 20`.
   Pick the top N with no fit score, not expired, not tracked. Prefer nearer
   deadlines when prefilter scores are close. Leave out postings flagged
   `gate-language-*` or `msca-mobility-rule-blocks` unless asked; list them at
   the end as blocked.
2. For each: read the saved advert in `data/ads/<id>.txt`, or fetch it
   (`scripts/fetch.py`, through to the institution's own page; browser if
   needed). Apply `reference/rubric.md` in short form: gates, seven scores
   with a few words of evidence, total. Read the supervisor's profile page at
   most; deeper research belongs to `evaluate`. One after another by default.
   If the candidate asks for parallel or batch evaluation: show
   `python3 scripts/batch.py --dry-run --top N`, get a yes (each worker spends
   tokens on their account), run it without `--dry-run`, then go to step 4
   using the merged scores and the reports the workers wrote.
3. Record each: `python3 scripts/ops.py score <id> <total> --verdict "<band>" --report reports/ranking-<date>.md`.
   Gate failures get 2.0 and the gate named in the verdict.
4. Write `reports/ranking-<YYYY-MM-DD>.md` and show it:

   | Rank | Fit | Position | Institution | Country | Deadline | Why it fits | Main risk |

   Then: **Apply now** (4.3+, or 3.8+ with a deadline inside two weeks),
   **Apply** (3.8+), **Maybe** (3.5-3.7), **Blocked by a gate**. Name every
   `CHECK` that must be answered before an application is worth writing.
   List the pages read.
5. Offer to track the top ones (`python3 scripts/ops.py track <id>`); do it on a yes.

These are short-form scores. Say so, and recommend `evaluate` before `apply`.

# Mode: scan

Find new positions. Input: optional extra keywords or a country to focus on.

1. Run `python3 scripts/scan.py` in the background (add `--query "<kw>"` for
   each extra keyword). It sweeps every enabled board in parallel and takes a
   few minutes.
2. **Academic Positions** blocks scripts but loads in a browser. If
   `sources.academicpositions.enabled` is true in `config/search.json` and a
   browser tool is available: open `https://academicpositions.com/find-jobs`,
   run the JavaScript printed by `python3 scripts/collector.py academicpositions`
   in that tab, save the returned advert lines (everything after the first log
   line) to `data/inbox/academicpositions.txt`, then
   `python3 scripts/import_postings.py data/inbox/academicpositions.txt`.
   If the page shows a verification check, ask the candidate to complete it
   themselves; never work around it. With no browser tool, skip this and say so.
3. While the scan runs, cover what neither route reaches, read-only, by web
   search or browser: university vacancy pages in the candidate's preferred
   countries that are not among the scanned boards (for example Swedish
   universities on Varbi, Danish universities, KU Leuven and Ghent, the
   University of Luxembourg, EPFL), national funder calls, and the mailing
   lists and society job pages of their field. Search for the themes in
   `profile/profile.yml`. Add each real, open, funded doctoral post with
   `python3 scripts/ops.py add --inst ... --position ... --country ... --url ... --deadline YYYY-MM-DD`.
4. When the scan finishes, read its output. If it warns that a board returned
   0 results, report it: that parser needs fixing (`docs/ADDING_A_BOARD.md`).
   Then run `python3 scripts/enrich.py`: it reads the full advert behind every
   promising posting, flags required languages, proposal and test
   requirements, MSCA funding, pay and contacts, and rescores. Say which
   adverts it could not read. Then `python3 scripts/ops.py postings --min 20`.
5. Triage the new ones by title, summary and signals only:
   - dismiss obvious misses: `python3 scripts/ops.py dismiss <id> <reason>`
   - skip anything already in `data/tracker.csv`
   - note gates visible at a glance (expired, wrong role, MSCA mobility rule,
     `gate-language-*`). A language gate is a pattern match: list those under
     "blocked" with their topic instead of dropping them silently.
6. Report a table of at most 15: prefilter, title, institution, country,
   deadline, days left, one line on why it might fit, flags. Nearest deadlines
   first among similar scores. Then name the 3-5 that deserve `evaluate` first.

Do not evaluate in depth here and do not draft anything.

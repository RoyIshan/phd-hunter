# Mode: apply

Build a tailored application pack for one position. Input: posting id,
tracker id or URL.

Needs an evaluation report; run the `evaluate` steps first if there is none.
If the fit is below 3.5, say so and ask whether to continue.

Read `profile/cv.md`, `profile/voice.md`, the report, and the advert again:
confirm it is still open (`python3 scripts/alive.py`, or open the page), the
deadline, and the exact list of documents, formats and limits.

1. **Track it.** `python3 scripts/ops.py track <id> --status drafting` (or
   `ops.py set <tid> status=drafting`). Create `output/<tid>-<slug>/`.
2. **Angle.** State in three lines: the thread from the candidate's work to
   this project, which summary variant and headline to use, the two pieces of
   work to lead with. Ask only what the report and profile leave open: why
   this group, what they would do first, anything to avoid.
3. **CV** → `cv.md`. Select and reorder from `profile/cv.md`. Mirror the
   advert's own terms where the experience honestly matches. Length and
   conventions per `reference/countries.md` and `profile/voice.md`.
4. **Letter** → `letter.md`, in the shape described in `profile/voice.md`.
   Engage with one paper from the group that was read this session and cite
   it properly. Name the main gap once, with what they are doing about it.
   Use the document name the advert uses (motivation letter, personal letter,
   cover letter, statement of purpose).
5. **Research proposal or statement**, only if the advert asks → follow
   `modes/proposal.md`.
6. **Other documents** → `checklist.md`: every required item, status (have /
   adapt / request), where it is, who must act: transcripts, diplomas, diploma
   supplement, thesis or summary, language proof, reference letters or
   contacts, grade explanation. If letters are needed, draft a short note to
   referees → `referee-note.md`.
7. **Form answers.** Free-text portal questions → `form-answers.md`.
8. **Review as a sceptical committee member:**
   - `python3 scripts/verify.py output/<dir>/ --also <report> data/ads/<id>.txt`
     and resolve every flag: fix the draft, or confirm the item is about the
     position and comes from the report or advert. Never silence a flag by
     adding an unconfirmed fact to `profile/cv.md`; ask the candidate.
   - every remaining fact against `profile/cv.md`; remove anything not found there and list it
   - every name, paper and link against the report's sources
   - each "must" in the advert addressed somewhere
   - voice: apply `profile/voice.md`; run a humanizer skill if one is installed
   - length, language and file naming as the advert asks
   Fix what the review finds and say what changed.
9. **Convert:** `python3 scripts/make_docx.py output/<dir>/cv.md` (and the
   letter, proposal) for final layout in a word processor.
10. `python3 scripts/ops.py set <tid> next_action="review pack and submit" next_date=<deadline minus 2 days>`.

Finish with: the files produced, the three passages to read most carefully,
open `CHECK` items, and the submission link. The candidate submits. Never fill
in or submit a portal.

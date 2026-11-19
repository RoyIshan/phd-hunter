# Mode: interview

Prepare for an interview on a tracked application. Input: tracker id, and the
date, format and panel if known.

Load the tracker row, the evaluation report, the submitted pack in `output/`
(the committee read exactly that), and any people briefs.

1. **Panel.** Who will be there and what each cares about; refresh their
   recent work (verify, with links).
2. **The project in the candidate's words.** A two-minute account of the
   research problem, why it matters, and how they would approach year one.
3. **Likely questions with answer outlines built only from `profile/cv.md`:**
   - Why a PhD, why now, why this group
   - Walk us through your thesis: problem, method choices and why, what
     changed along the way, limitations, what you would do differently
   - Methods depth: the approach they used versus alternatives; validity;
     where their skills are thinner (`methods_gap`)
   - The hardest part of this project for them, and how they would close the gap
   - A paper of ours you read: what you took from it, what you would question
   - Publishing plan and target venues
   - Working with partners; when partner interests and research pull apart
   - Teaching, supervising students, independence, handling setbacks
   - Practicalities: start date, permit, relocation
4. **Stories.** Five or six STAR outlines from the proof points and experience
   in `profile/cv.md`. Nothing invented, nothing embellished.
5. **If a presentation is requested:** slide-by-slide outline within the time
   given (their thesis in about five slides, then their plan for the PhD in three).
6. **Their questions for the panel:** supervision rhythm, expectations for
   year one, data and partner access, how past PhDs fared, teaching load,
   progress reviews.
7. **Weak spots** from the report, with an honest line for each.
8. **Country and format notes** from `reference/countries.md`: panel size,
   whether a test or assignment is common, who decides.

Save as `output/<tid>-<slug>/interview-prep.md`. Offer a mock interview: one
question at a time, wait for the answer, brief feedback on content and length,
then the next.

Afterwards, record what was asked and how it went in the same file, and
`python3 scripts/ops.py set <tid> status=interview notes="..."`.

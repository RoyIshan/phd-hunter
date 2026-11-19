# Mode: proposal

Draft a research proposal, project outline or research statement for one
position. Input: posting or tracker id, plus any length or format limit.

Many calls decide on this document. It has to come from reading, so this mode
is slower than the others by design.

1. **Brief.** From the advert and report: the exact title of the document, the
   word or page limit, required sections, whether the project is fixed
   (respond to it) or open (propose one), and who will read it.
2. **Read before writing.** At least: the project or group page; two or three
   recent papers by the supervisor(s) on the topic (abstract, introduction,
   discussion); one or two anchor papers from the wider literature. Find them
   with `python3 scripts/prospect.py author "<name>"` and web search. Keep a
   list with links. A reference goes in only if it was opened this session and
   says what it is cited for. Never cite from memory.
3. **Agree the idea in chat first.** Offer two or three candidate research
   problems in a few lines each: the gap, the question, the approach, and why
   this candidate can do it. Let them choose or redirect. Their idea beats a
   polished one they cannot defend in an interview.
4. **Write** → `output/<tid>-<slug>/proposal.md`, in the voice of
   `profile/voice.md`, within the limit:
   - **Problem and relevance**: what is unsolved, and for whom it matters
   - **What is known and the gap**: the few verified references that carry the argument
   - **Research question(s)**: one main, two or three sub-questions at most
   - **Theoretical lens**: the perspective(s) the group actually uses; say why they fit
   - **Design and methods**: cases or data, how collected, how analysed, why
     this design answers the question; ethics and access
   - **Plan**: by year or phase, with outputs (papers, artefacts)
   - **Contribution**: to research, and to practice or society
   - **Fit**: how the candidate's own work (from `profile/cv.md` only) prepares
     them, and what they will need to learn
   Use the methods the candidate knows where they fit; where the project needs
   a method listed under `methods_gap`, say how they would acquire it. Do not
   present unfamiliar methods as expertise.
5. **Check.** Run `python3 scripts/verify.py <proposal> --also <report>`. Every reference opens and supports its sentence; every claim
   about the candidate is in `profile/cv.md`; the word count is inside the
   limit; the document answers the call's own questions in its own terms.
   List the three weakest points a reviewer would attack, with a line on each.
6. Reference list in one consistent style. `python3 scripts/make_docx.py <file>` to convert.

Tell the candidate plainly that the argument is theirs to own: they should
read the cited papers themselves before submitting.

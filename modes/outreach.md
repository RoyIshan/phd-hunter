# Mode: outreach

Find the right people and draft messages to them. Input: a posting or tracker
id, a professor or group name, or a topic for cold outreach.

Work out which case applies.

**A. Advertised position.** In order of usefulness:
1. The contact person or supervisor named in the advert: a short
   pre-application email with one real question (a `CHECK` item, the project's
   direction, whether the background suits). If the advert says not to
   contact them, or to use a form only, respect that and say so.
2. A current PhD candidate or postdoc in the group, about what working there
   is like: a short note or email.
3. Nobody else. Not HR for substance; not several professors in one group
   about the same post.

**B. A named professor or group, no advert.** A speculative enquiry about
upcoming funded positions.

**C. A topic.** Run the `prospect` mode first, let the candidate pick from the
shortlist, then continue here per person.

For every person:

1. **Verify.** Read their institutional profile and at least one recent paper
   (abstract plus enough of the body to say something specific). Record the
   links. Take the email address only from an institutional page. Anything
   unverified stays as `[CHECK: ...]` in the draft.
2. **Brief** → `reports/people-<name-slug>.md`: role, group, current projects
   and funding, three recent papers with one-line takeaways, the overlap with
   the candidate's work, and what not to claim.
3. **Draft** → `output/<tid-or-topic>/outreach-<name-slug>.md`, following the
   outreach rules in `profile/voice.md`. Without such rules: under 150 words;
   who they are in one line; one specific point about the person's work; one
   question that is easy to answer; CV attached; no flattery; no request for a
   call in the first message. Include a subject line and a shorter follow-up
   for 7-10 working days later. For case B, ask whether a funded position is
   expected and whether a short research idea would be welcome.
4. **Log:** `python3 scripts/ops.py contact --name "..." --inst "..." --role "..." --email "..." --tid <tid> --status drafted`.

Show the drafts in chat. Never send. For a draft the candidate approves,
`python3 scripts/mail.py draft <file>` writes an unsent `.eml` they can open in
their mail app (see `modes/inbox.md`). When the candidate says a message went
out, set the contact to `sent` and put a follow-up date on the tracker row.
When they paste a reply, summarise it, update the status, propose the next step.

Etiquette: one message and one follow-up, then stop. Write early enough for an
answer before the deadline. Address people by title and surname unless their
page signals otherwise. Match the country's formality (`reference/countries.md`).

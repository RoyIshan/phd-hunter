# Mode: compare

Compare 2-6 positions or offers side by side. Input: posting or tracker ids.

For each, load its report in `reports/` (run the `evaluate` steps first for any
without one) and the country row in `reference/countries.md`.

One table, positions as columns:

- Fit score and verdict
- Research question in one line; closeness to the candidate's themes
- Supervisor and group: who, how active, signs of supervision quality
- Methods they would use and learn; the gap to close
- Contract: employee or stipend, years funded, full or part time
- Pay: gross per month and its source; rough net and local cost of living,
  labelled as estimates unless read from an official source this session
- Teaching or departmental duties
- Partners and data access
- Requirements not yet met
- Effort to apply: documents to write, deadline, days left
- After the PhD: where the group's graduates went, if findable
- Life: language outside work, permit route, distance from the current base,
  and anything in `targets.deal_breakers`

Then:

1. **If only one application fits this week:** which, and why.
2. **If these were offers:** which to take, and what would flip the choice.
3. The trade-offs stated plainly, including what each option costs.

Save as `reports/compare-<YYYY-MM-DD>-<slugs>.md`.

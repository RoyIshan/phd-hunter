# Mode: digest

The routine check, short enough to run every few days or on a schedule.
No input.

1. `python3 scripts/scan.py` then `python3 scripts/enrich.py`.
   (Skip the browser-collected boards unless a browser tool is at hand.)
2. `python3 scripts/ops.py due --days 14` and `python3 scripts/alive.py`.
3. Report in under 25 lines:
   - **New and promising:** up to 8 postings first seen in this run, prefilter
     20 or more and no gate flag: title, institution, country, deadline, one
     line on why. Put any with a deadline inside 10 days first.
   - **Blocked but on-topic:** up to 3 new postings stopped by a gate flag.
   - **Deadlines and actions due** from the tracker.
   - **Board health:** any board that returned nothing.
4. Recommend at most two things to do next (usually `evaluate <id>` on the
   best new posting, or the nearest deadline).
5. `python3 scripts/dashboard.py`.

If nothing new clears the bar, say so in one line. Do not pad.

# Contributing

Thanks for helping. phd-hunter is small on purpose: Python standard library,
plain Markdown instructions, no build step.

## Ground rules

- **Licence.** By opening a pull request you agree that your contribution is licensed under the project's MIT licence. The name "phd-hunter" stays with this project ([TRADEMARK.md](TRADEMARK.md)).
- **No personal data, ever.** Not yours, not a test user's. `profile/`,
  `config/search.json`, `data/`, `reports/`, `output/` and `documents/` are
  git-ignored; keep it that way. Run `python3 -m unittest discover tests`
  before you push: one test fails if a personal file is tracked.
- **Read-only and polite.** Parsers fetch public listing pages, sequentially
  per site, with a pause. Do not add anything that logs in, posts, or gets
  around a bot check, CAPTCHA or rate limit.
- **Human in the loop.** Nothing may send an email or submit an application.
- **Standard library only** in `scripts/` (optional extras must degrade
  gracefully, like `pypdf` and `python-docx` do).

## Good first contributions

- A parser for another board or university portal: [docs/ADDING_A_BOARD.md](docs/ADDING_A_BOARD.md)
- A fix when a board changes its page (the scan and `doctor.py --online` report which)
- Corrections and sources for `reference/countries.md`
- More EURAXESS field IDs in `reference/euraxess-fields.json`
- Language patterns in `scripts/enrich.py` (with a test case in `tests/`)
- Translations or field-specific variants of the files in `modes/`
- Reports (and fixes) from running it in an agent CLI other than Claude Code

After adding or renaming a mode, run `python3 scripts/sync_agents.py`; a test fails if the generated files are stale.

## Checks

```bash
python3 -m unittest discover tests
```

```bash
python3 scripts/doctor.py --online
```

The second one needs a `config/search.json`; copy `templates/search.example.json` for a test run.

## What CI does

- **tests**: the offline unit tests on Python 3.9 and 3.12.
- **no user data in PRs**: fails a pull request that adds anything under `profile/`, `data/`, `reports/`, `output/`, `documents/` or `config/search.json`.
- **CodeQL**: security scan of the Python scripts.
- **board health**: weekly, opens an issue when a board parser stops returning results.

## Style

Functions short, names plain, comments only where the reason is not obvious.
Instructions in `modes/` are written to the assistant in the imperative and
say what to do when a tool is missing.

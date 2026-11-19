#!/usr/bin/env python3
"""Evaluate many positions at once with parallel headless agent workers.

    python3 scripts/batch.py --dry-run               # show what would run
    python3 scripts/batch.py --top 8 --workers 3     # best 8 unscored, 3 at a time
    python3 scripts/batch.py --ids euraxess-ab12cd34 jobsacuk-99887766 --deep
    python3 scripts/batch.py --cli codex             # another agent CLI

Each worker is a separate run of your agent CLI in non-interactive mode. It
gets one position, writes a report to reports/ and a small result file to
data/batch/<id>.json, and touches nothing else. When all workers are done this
script merges the scores into data/postings.json, so workers never write to
the same file.

Agent CLI: --cli takes a preset (claude, codex, gemini, opencode) or a full
command; the prompt is appended as the last argument. Set a default with
"batch": {"cli": "...", "workers": 3} in config/search.json. Headless runs
need permission to read files, run `python3 scripts/fetch.py` and write
reports: add your CLI's own flags for that to the command, e.g.
    --cli 'claude -p --permission-mode acceptEdits --allowedTools "Bash(python3 scripts/fetch.py:*)"'
Check your CLI's documentation for the exact flags.

Every worker costs tokens on your own account. Start with --top 3.
"""
import argparse
import concurrent.futures
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scan  # noqa: E402

ROOT = scan.ROOT
OUT = ROOT / "data" / "batch"
PRESETS = {"claude": "claude -p", "codex": "codex exec", "gemini": "gemini -p", "opencode": "opencode run"}


def pick(store, top, ids):
    if ids:
        chosen = [p for k, p in store.items() if any(k == i or k.endswith(i) for i in ids)]
        missing = [i for i in ids if not any(k == i or k.endswith(i) for k in store)]
        if missing:
            sys.exit(f"Not in the store: {', '.join(missing)}")
        return chosen
    pool = [p for p in store.values()
            if p.get("status") == "new" and not p.get("fit") and "expired" not in p.get("flags", [])
            and not any(f.startswith("gate-") or f.endswith("-blocks") or f == "role-unclear" for f in p.get("flags", []))]
    pool.sort(key=lambda p: (-p.get("prefilter", 0), p.get("deadline") or "9999"))
    return pool[:top]


def build_prompt(p, deep):
    slug = "".join(c if c.isalnum() else "-" for c in (p.get("org", "") + "-" + p["title"]).lower())[:60].strip("-")
    ad = ROOT / "data" / "ads" / f"{p['id']}.txt"
    fields = {
        "id": p["id"], "title": p["title"], "org": p.get("org", ""), "country": p.get("country", ""), "url": p["url"],
        "ad_file": str(ad.relative_to(ROOT)) if ad.exists() else "none",
        "report": f"reports/batch-{slug}.md", "result": f"data/batch/{p['id']}.json",
        "depth": "full" if deep else "short",
        "depth_note": ("Research the supervisor and group as modes/evaluate.md step 4 describes."
                       if deep else "Read the supervisor's own profile page at most; score dimension 4 as 3 unless you read it."),
    }
    return (ROOT / "batch" / "worker-prompt.md").read_text().format(**fields), fields


def run_worker(p, cmd, deep, timeout):
    prompt, fields = build_prompt(p, deep)
    result = ROOT / fields["result"]
    if result.exists():
        result.unlink()
    log = OUT / f"{p['id']}.log"
    started = time.time()
    try:
        with log.open("w", encoding="utf-8") as fh:
            proc = subprocess.run(cmd + [prompt], cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, timeout=timeout)
        state = "ok" if proc.returncode == 0 else f"exit {proc.returncode}"
    except subprocess.TimeoutExpired:
        state = "timeout"
    except FileNotFoundError:
        state = f"command not found: {cmd[0]}"
    return p["id"], state, round(time.time() - started), result


def merge(store, outcomes):
    scored = []
    for pid, state, secs, result in outcomes:
        p = store[pid]
        if not result.exists():
            log = OUT / f"{pid}.log"
            said = next((l.strip() for l in log.read_text(errors="ignore").splitlines() if l.strip()), "") if log.exists() else ""
            print(f"  FAILED {pid} ({state}, {secs}s): no result file." + (f' The CLI said: "{said[:120]}"' if said else "")
                  + f" Full log: data/batch/{pid}.log")
            if "log in" in said.lower() or "logged in" in said.lower() or "/login" in said:
                print("         Your agent CLI is not signed in in this terminal. Sign in there once, then rerun.")
            continue
        try:
            r = json.loads(result.read_text())
            fit = float(r["fit"])
            if r.get("id") != pid or not 1.0 <= fit <= 5.0:
                raise ValueError("wrong id or fit out of range")
        except (ValueError, KeyError, TypeError) as exc:
            print(f"  FAILED {pid}: result file is not usable ({exc}).")
            continue
        p["fit"], p["status"] = round(fit, 1), "evaluated"
        p["verdict"] = str(r.get("verdict", ""))[:120]
        p["report"] = str(r.get("report", ""))[:200]
        p["batch"] = {"date": scan.TODAY.isoformat(), "checks": r.get("checks", []), "gates_failed": r.get("gates_failed", [])}
        scored.append((fit, p, r))
    scan.STORE.write_text(json.dumps(store, indent=1, ensure_ascii=False))
    return scored


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=5, help="how many of the best unscored positions (default 5)")
    ap.add_argument("--ids", nargs="*", help="specific posting ids instead of the top N")
    ap.add_argument("--workers", type=int, help="how many run at once (default 3)")
    ap.add_argument("--cli", help="preset name or full command; the prompt is appended")
    ap.add_argument("--deep", action="store_true", help="full evaluation with supervisor research (slower, costs more)")
    ap.add_argument("--timeout", type=int, default=900, help="seconds per worker")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    cfg = json.loads(scan.CONFIG.read_text()).get("batch", {}) if scan.CONFIG.exists() else {}
    cli = a.cli or cfg.get("cli") or "claude"
    cmd = shlex.split(PRESETS.get(cli, cli))
    workers = max(1, min(a.workers or cfg.get("workers", 3), 8))
    store = scan.load_store()
    chosen = pick(store, a.top, a.ids)
    if not chosen:
        sys.exit("Nothing to evaluate: no unscored, open, unblocked positions. Run scan and enrich first.")

    print(f"{len(chosen)} position(s), {workers} at a time, {'full' if a.deep else 'short-form'} evaluation, command: {' '.join(cmd)} <prompt>\n")
    for p in chosen:
        print(f"  {p.get('prefilter', 0):3d}  {p['id']:28s} {p['title'][:60]}")
    if a.dry_run:
        print("\nDry run: nothing started. First prompt:\n" + "-" * 60 + "\n" + build_prompt(chosen[0], a.deep)[0])
        return

    OUT.mkdir(parents=True, exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)
    print()
    outcomes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_worker, p, cmd, a.deep, a.timeout) for p in chosen]
        for done in concurrent.futures.as_completed(futures):
            outcome = done.result()
            outcomes.append(outcome)
            print(f"  finished {outcome[0]} ({outcome[1]}, {outcome[2]}s)")
    print()
    scored = merge(store, outcomes)
    for fit, p, r in sorted(scored, key=lambda x: -x[0]):
        print(f"{fit:.1f}  {p['title'][:66]}\n     {p.get('org', '')[:40]} | {p['verdict']}\n     + {r.get('reason_in', '')[:100]}\n     - {r.get('reason_out', '')[:100]}")
    print(f"\n{len(scored)} of {len(chosen)} scored. Short-form scores: run evaluate on the best before applying.")
    sys.exit(0 if len(scored) == len(chosen) else 1)


if __name__ == "__main__":
    main()

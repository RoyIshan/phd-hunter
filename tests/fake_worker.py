"""Stand-in for an agent CLI, used by the batch test: reads the prompt it is
given, writes the report and result file the prompt asks for."""
import json
import re
import sys
from pathlib import Path

prompt = sys.argv[-1]
pid = re.search(r"Position id: (\S+)", prompt).group(1)
report = re.search(r"Write the report to `([^`]+)`", prompt).group(1)
result = re.search(r"as JSON to `([^`]+)`", prompt).group(1)
Path(report).parent.mkdir(parents=True, exist_ok=True)
Path(report).write_text(f"# test report for {pid}\n")
Path(result).parent.mkdir(parents=True, exist_ok=True)
Path(result).write_text(json.dumps({"id": pid, "fit": 3.7, "verdict": "Maybe", "report": report, "gates_failed": [],
                                    "checks": ["degree equivalence"], "reason_in": "topic", "reason_out": "methods"}))

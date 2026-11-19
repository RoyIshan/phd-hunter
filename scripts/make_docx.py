#!/usr/bin/env python3
"""Convert a Markdown draft (CV, letter, proposal) to a clean .docx.

    python3 scripts/make_docx.py output/A001-example/cv.md [more.md ...]

Handles headings, paragraphs, bullets, **bold**, *italic* and simple
"left | right" lines (right part is tab-aligned to the margin, for dates).
Finish layout in Word and export to PDF from there.
Requires python-docx (pip install python-docx).
"""
import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.enum.text import WD_TAB_ALIGNMENT
    from docx.shared import Cm, Pt
except ImportError:
    sys.exit("python-docx is missing. Install it with: pip install python-docx")

INLINE = re.compile(r"(\*\*.+?\*\*|\*.+?\*)")


def add_runs(par, line):
    for part in INLINE.split(line):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            par.add_run(part[2:-2]).bold = True
        elif part.startswith("*") and part.endswith("*"):
            par.add_run(part[1:-1]).italic = True
        else:
            par.add_run(part)


def convert(src):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2)
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    text_width = sec.page_width - sec.left_margin - sec.right_margin
    base = doc.styles["Normal"]
    base.font.name, base.font.size = "Calibri", Pt(10.5)
    base.paragraph_format.space_after = Pt(4)

    for raw in src.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith(">") or line.strip() == "---":
            continue
        if line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=0)
        elif line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=1)
        elif line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=2)
        elif re.match(r"^\s*[-*•] ", line):
            par = doc.add_paragraph(style="List Bullet")
            par.paragraph_format.space_after = Pt(1)
            add_runs(par, re.sub(r"^\s*[-*•] ", "", line))
        elif " | " in line and line.count(" | ") == 1 and len(line) < 140:
            left, right = line.split(" | ")
            par = doc.add_paragraph()
            par.paragraph_format.tab_stops.add_tab_stop(text_width, WD_TAB_ALIGNMENT.RIGHT)
            add_runs(par, left.strip())
            par.add_run("\t")
            add_runs(par, right.strip())
        else:
            add_runs(doc.add_paragraph(), line)

    out = src.with_suffix(".docx")
    doc.save(out)
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        print(f"Wrote {convert(Path(arg))}")

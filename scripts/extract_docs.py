#!/usr/bin/env python3
"""Turn the candidate's own documents into plain text for setup.

    python3 scripts/extract_docs.py                 # everything in documents/
    python3 scripts/extract_docs.py ~/Downloads/CV.pdf thesis-summary.docx

Reads .pdf, .docx, .md, .txt and .tex. Writes one .txt per document to
documents/.extracted/ and prints a short index. Nothing leaves the machine.
.docx needs no extra package. .pdf needs pypdf (pip install pypdf); without
it, PDFs are listed as skipped so you can paste their text instead.
"""
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "documents"
OUT = DOCS / ".extracted"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_text(path):
    """Paragraphs and table cells, in document order, using only the standard library."""
    with zipfile.ZipFile(path) as z:
        root = ElementTree.fromstring(z.read("word/document.xml"))
    lines = []
    for par in root.iter(W + "p"):
        parts = []
        for node in par.iter():
            if node.tag == W + "t" and node.text:
                parts.append(node.text)
            elif node.tag in (W + "tab", W + "br"):
                parts.append("\t" if node.tag == W + "tab" else "\n")
        line = "".join(parts).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def pdf_text(path):
    try:
        import pypdf
    except ImportError:
        return None
    reader = pypdf.PdfReader(str(path))
    raw = "\n".join(page.extract_text() or "" for page in reader.pages)
    # Some exports put every word on its own line: rejoin those runs.
    raw = re.sub(r"(?<=[^\n.:;])\n[ \t]*\n(?=[a-z(])", " ", raw)
    return re.sub(r"[ \t]+", " ", raw)


def extract(path):
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return docx_text(path)
    if suffix == ".pdf":
        return pdf_text(path)
    if suffix in (".md", ".txt", ".tex"):
        return path.read_text(encoding="utf-8", errors="ignore")
    return None


def main():
    targets = [Path(a).expanduser() for a in sys.argv[1:]]
    if not targets:
        if not DOCS.exists():
            sys.exit("No documents/ folder yet. Create it, drop your CVs, letters, thesis summary and transcripts in, and run again.")
        targets = sorted(p for p in DOCS.rglob("*") if p.is_file() and ".extracted" not in p.parts and not p.name.startswith("."))
    OUT.mkdir(parents=True, exist_ok=True)
    done, skipped = [], []
    for path in targets:
        try:
            text = extract(path)
        except Exception as exc:  # one broken file must not stop the rest
            text, why = None, str(exc)[:80]
        else:
            why = "pypdf not installed" if path.suffix.lower() == ".pdf" else "unsupported type"
        if not text or len(text.strip()) < 40:
            skipped.append((path.name, why))
            continue
        target = OUT / (re.sub(r"[^\w.-]+", "_", path.stem) + ".txt")
        target.write_text(text, encoding="utf-8")
        done.append((path.name, len(text.split()), target.relative_to(ROOT)))
    for name, words, target in done:
        print(f"{words:6d} words  {name}  ->  {target}")
    for name, why in skipped:
        print(f"   skipped    {name}  ({why})")
    print(f"\n{len(done)} extracted, {len(skipped)} skipped.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Extract a slide deck (.pptx or .pdf) into slide-numbered Markdown for essay writing.

Usage:
    python extract_deck.py deck.pptx --out deck.md
    python extract_deck.py deck.pdf  --out deck.md

For each slide it records the title, body text in approximate reading order, table cells,
chart titles/categories/series (pptx), and speaker notes (pptx). Slides with
little extractable text or omitted visual content are listed for image inspection
(charts, diagrams and screenshots often hold key evidence).

Dependencies: python-pptx for .pptx; pdfplumber or pypdf (or the pdftotext CLI) for .pdf.
No OCR is performed. Extraction is not a complete representation of a slide.
Existing output files require --force. The source file cannot be overwritten.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

LOW_TEXT_WORDS = 12


def clean(text):
    text = text.replace("\x0b", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln)


# ----------------------------------------------------------------- PPTX ----

def _shape_key(shape):
    top = shape.top if shape.top is not None else 0
    left = shape.left if shape.left is not None else 0
    return (top, left)


def _walk_shapes(shapes):
    """Yield leaf shapes in approximate reading order, descending into groups."""
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    for shape in sorted(shapes, key=_shape_key):
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from _walk_shapes(shape.shapes)
        else:
            yield shape


def _paragraph_lines(text_frame):
    out = []
    for p in text_frame.paragraphs:
        t = clean(p.text)
        if t:
            indent = "  " * (p.level or 0)
            out.append(indent + "- " + t.replace("\n", "\n" + indent + "  "))
    return out


def _chart_lines(chart):
    out = []
    try:
        if chart.has_title and chart.chart_title.has_text_frame:
            title = chart.chart_title.text_frame.text.strip()
            if title:
                out.append(f"[chart] title: {title}")
    except Exception:
        out.append("[chart] WARNING title unreadable; inspect slide image")
    try:
        plots = list(chart.plots)
    except Exception:
        return out + ["[chart] WARNING plots unreadable; inspect slide image"]
    if not plots:
        out.append("[chart] WARNING no readable plots; inspect slide image")
    for pi, plot in enumerate(plots, 1):
        prefix = f"[chart] plot {pi}"
        try:
            cats = [str(c) for c in plot.categories]
            if cats:
                out.append(prefix + " categories: " + ", ".join(cats))
        except Exception:
            out.append(prefix + " WARNING category labels unavailable; inspect slide image")
        try:
            series = list(plot.series)
        except Exception:
            out.append(prefix + " WARNING series unreadable; inspect slide image")
            continue
        for si, series_item in enumerate(series, 1):
            try:
                name = series_item.name
                vals = list(series_item.values)
                shown = ", ".join("(missing)" if v is None else str(v) for v in vals)
                out.append(f"{prefix} series '{name}': {shown}")
                for field in ("x_values", "bubble_sizes"):
                    if hasattr(series_item, field):
                        out.append(f"{prefix} series '{name}' {field}: "
                                   + ", ".join(str(v) for v in getattr(series_item, field)))
            except Exception:
                out.append(f"{prefix} WARNING series {si} incompletely readable; inspect slide image")
    return out


def extract_pptx(path):
    from pptx import Presentation
    prs = Presentation(path)
    slides = []
    for idx, slide in enumerate(prs.slides, start=1):
        title = ""
        body, tables, charts, pictures, warnings = [], [], [], 0, []
        title_shape = slide.shapes.title
        if title_shape is not None and title_shape.has_text_frame:
            title = clean(title_shape.text_frame.text)
        for shape in _walk_shapes(slide.shapes):
            if title_shape is not None and shape.shape_id == title_shape.shape_id:
                continue
            if getattr(shape, "has_table", False) and shape.has_table:
                rows = []
                for r in shape.table.rows:
                    rows.append(" | ".join(clean(c.text) for c in r.cells))
                tables.append(rows)
            elif getattr(shape, "has_chart", False) and shape.has_chart:
                charts.extend(_chart_lines(shape.chart))
            elif shape.shape_type == 13:  # PICTURE
                pictures += 1
            elif getattr(shape, "has_text_frame", False):
                body.extend(_paragraph_lines(shape.text_frame))
            elif shape.shape_type in (7, 11, 16, 21):  # OLE, media and diagrams
                warnings.append("Embedded object, media or diagram content was not extracted.")
        notes = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
            notes = clean(slide.notes_slide.notes_text_frame.text)
        slides.append(dict(n=idx, title=title, body=body, tables=tables,
                           charts=charts, pictures=pictures, notes=notes, warnings=warnings))
    return slides


# ------------------------------------------------------------------ PDF ----

def extract_pdf(path):
    pages = []
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = clean(page.extract_text() or "")
                tables = []
                try:
                    for t in page.extract_tables():
                        tables.append([" | ".join(clean(c or "") for c in row) for row in t])
                except Exception:
                    warnings = ["Table extraction failed; inspect the page image."]
                else:
                    warnings = []
                pages.append((i, text, tables, len(page.images), warnings))
        return _pdf_to_slides(pages)
    except ImportError:
        pass
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        for i, page in enumerate(reader.pages, start=1):
            pages.append((i, clean(page.extract_text() or ""), [], 0,
                          ["Text-only PDF reader; images, tables and charts need visual inspection."]))
        return _pdf_to_slides(pages)
    except ImportError:
        pass
    if shutil.which("pdftotext"):
        result = subprocess.run(["pdftotext", "-layout", str(Path(path).resolve()), "-"],
                                capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise RuntimeError("pdftotext failed: " + (result.stderr.strip() or f"exit {result.returncode}"))
        chunks = result.stdout.split("\f")
        if chunks and not chunks[-1].strip() and len(chunks) > 1:
            chunks.pop()  # one trailing page separator, not an actual page
        if result.stdout == "":
            raise RuntimeError("pdftotext returned no pages; inspect the source file.")
        for i, chunk in enumerate(chunks, start=1):
            pages.append((i, clean(chunk), [], 0,
                          ["Text-only PDF reader; images, tables and charts need visual inspection."]))
        return _pdf_to_slides(pages)
    sys.exit("No PDF reader available: install pdfplumber or pypdf, or poppler's pdftotext.")


BULLET_GLYPHS = "•▪◦●○■□➢►▶✓*"


def _is_bullet(text):
    return bool(text and (text[0] in BULLET_GLYPHS
                         or re.match(r"^[-–—]\s+(?!\d)", text)))


def _merge_pdf_lines(lines):
    """Rejoin bullets that PDF text extraction splits across lines.

    Bullet glyphs (alone or leading a line) start a new item; following lines
    without a glyph are treated as wrapped continuations of that item.
    """
    if not any(_is_bullet(ln.strip()) for ln in lines if ln.strip()):
        return lines
    items, current = [], None
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if _is_bullet(s):
            if current:
                items.append(current)
            current = s[1:].strip()
        elif re.match(r"^[+−–-]?\s*\d", s):
            # A numeric line may be a chart label or a signed value, not wrapping.
            if current:
                items.append(current)
                current = None
            items.append(s)
        elif current is None:
            items.append(s)
        else:
            current = (current + " " + s).strip()
    if current:
        items.append(current)
    return [i for i in items if i]


def _looks_like_chart(body_lines):
    """Axis ticks and category labels with little prose suggest a chart whose values were lost."""
    if len(body_lines) < 4:
        return False
    numeric = sum(1 for ln in body_lines if re.fullmatch(r"[-–]?\s*[\d.,%$€£S]+\s*", ln.lstrip("- ").strip()))
    return numeric / len(body_lines) >= 0.4


def _pdf_to_slides(pages):
    slides = []
    for page in pages:
        n, text, tables, images = page[:4]
        warnings = page[4] if len(page) > 4 else []
        lines = text.split("\n") if text else []
        title = lines[0] if lines else ""
        merged = _merge_pdf_lines(lines[1:])
        tables = [t for t in tables if any(cell.strip(" |") for cell in t)]
        charts = []
        if _looks_like_chart(merged):
            charts.append("[chart?] mostly axis numbers extracted; values are NOT in the text, read this slide as an image")
        body = ["- " + ln for ln in merged]
        slides.append(dict(n=n, title=title, body=body, tables=tables,
                           charts=charts, pictures=images, notes="", warnings=warnings))
    return slides


# --------------------------------------------------------------- output ----

def word_count(slide):
    parts = [slide["title"], *slide["body"]]
    for t in slide["tables"]:
        parts.extend(t)
    return len(re.findall(r"\w+", " ".join(parts)))


def render(slides, src):
    out = [f"# Deck extract: {Path(src).name}", "",
           f"{len(slides)} slides. Numbers below identify source positions, not necessarily printed slide labels.",
           "Text extraction is incomplete. Images, chart semantics, layout and reading order need visual review.", ""]
    low = []
    for s in slides:
        out.append(f"## Slide {s['n']}: {s['title'] or '(no title)'}")
        out.extend(s["body"])
        for ti, rows in enumerate(s["tables"], start=1):
            out.append(f"[table {ti}]")
            out.extend("    " + r for r in rows)
        out.extend(s["charts"])
        for warning in s.get("warnings", []):
            out.append("[extraction warning] " + warning)
        if s["pictures"]:
            out.append(f"[{s['pictures']} image(s) on this slide]")
        if s["notes"]:
            out.append("Speaker notes:")
            out.extend("> " + ln for ln in s["notes"].split("\n"))
        out.append("")
        if word_count(s) < LOW_TEXT_WORDS or s["pictures"] or s["charts"] or s.get("warnings"):
            low.append(s["n"])
    out.append("## Slides to inspect as images")
    if low:
        out.append("Limited text, charts, images or extraction warnings require inspection: "
                   + ", ".join(str(n) for n in low))
    else:
        out.append("No specific slides flagged by these heuristics. This does not establish complete extraction.")
    if src.lower().endswith(".pdf"):
        out.append("")
        out.append("Note: PDF exports drop speaker notes. If the user has the .pptx, it will give a fuller extract.")
    return "\n".join(out) + "\n", low


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--out", help="write Markdown here (default: print)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing output file, never the source")
    args = ap.parse_args()
    source = Path(args.deck)
    destination = Path(args.out) if args.out else None
    if destination is not None:
        if (source.resolve() == destination.resolve()
                or (source.exists() and destination.exists() and source.samefile(destination))):
            ap.error("output must not overwrite the source deck")
        if destination.exists() and not args.force:
            ap.error("output already exists; choose another path or explicitly use --force")
    ext = Path(args.deck).suffix.lower()
    try:
        if ext == ".pptx":
            slides = extract_pptx(args.deck)
        elif ext == ".pdf":
            slides = extract_pdf(args.deck)
        elif ext in (".ppt", ".key", ".odp"):
            ap.error(f"{ext} is not supported directly. Convert to .pptx or .pdf first.")
        else:
            ap.error(f"Unrecognised deck type: {ext}")
        if not slides:
            raise ValueError("No slides extracted; inspect the source file.")
        md, low = render(slides, args.deck)
        if destination is not None:
            with destination.open("w" if args.force else "x", encoding="utf-8") as target:
                target.write(md)
            print(f"Wrote {args.out}: {len(slides)} slides.")
        else:
            print(md)
    except ImportError as exc:
        ap.exit(2, f"Missing optional reader dependency: {exc.name}. See this script's --help.\n")
    except Exception as exc:
        ap.exit(2, f"Extraction failed: {exc}\n")
    if low:
        print(f"Inspect as images: slides {', '.join(map(str, low))}", file=sys.stderr)


if __name__ == "__main__":
    main()

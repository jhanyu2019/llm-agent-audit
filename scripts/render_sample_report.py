"""Render the public sample report into a PDF and website preview image.

This is a report-style rendering of selected structured content from
docs/sample-pilot-report.md. It is not a byte-for-byte Markdown renderer.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
SOURCE_MD = ROOT / "docs" / "sample-pilot-report.md"
OUTPUT_PDF = ROOT / "docs" / "sample-evidence-report.pdf"
OUTPUT_PNG = ROOT / "docs" / "sample-report-preview.png"
TEMP_PDF = ROOT / "docs" / "sample-evidence-report.tmp.pdf"
TEMP_PNG = ROOT / "docs" / "sample-report-preview.tmp.png"
SOURCE_LABEL = "docs/sample-pilot-report.md"
SCRIPT_LABEL = "scripts/render_sample_report.py"

PAGE = landscape(letter)
PAGE_W, PAGE_H = PAGE

INK = HexColor("#102033")
MUTED = HexColor("#5b6472")
TEAL = HexColor("#155e75")
TEAL_DARK = HexColor("#0b4f4a")
TEAL_SOFT = HexColor("#e9f5f8")
PAPER = HexColor("#f6f8fb")
LINE = HexColor("#d7e0ea")
LIGHT_LINE = HexColor("#e9eef4")
RED = HexColor("#991b1b")
RED_SOFT = HexColor("#fff1f2")
AMBER = HexColor("#9a5b12")
AMBER_SOFT = HexColor("#fff7ed")
GREEN = HexColor("#166534")
GREEN_SOFT = HexColor("#ecfdf5")
WHITE = HexColor("#ffffff")


def read_source() -> str:
    return SOURCE_MD.read_text(encoding="utf-8")


def source_short_hash(md: str) -> str:
    return hashlib.sha256(md.encode("utf-8")).hexdigest()[:12]


def clean(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = text.replace("`", "")
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)
    return text.strip()


def parse_table(lines: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [clean(cell.strip()) for cell in line.strip("|").split("|")]
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)
    return rows


def first_table(md: str) -> dict[str, str]:
    lines = md.splitlines()
    table_lines: list[str] = []
    started = False
    for line in lines:
        if line.startswith("| Field "):
            started = True
        if started:
            if line.startswith("|"):
                table_lines.append(line)
            elif table_lines:
                break
    rows = parse_table(table_lines)
    return {row[0]: row[1] for row in rows[1:] if len(row) >= 2}


def table_after_heading(md: str, heading: str) -> list[list[str]]:
    lines = md.splitlines()
    out: list[str] = []
    collecting = False
    for line in lines:
        if line.strip() == heading:
            collecting = True
            continue
        if collecting:
            if line.startswith("|"):
                out.append(line)
            elif out:
                break
    return parse_table(out)


def table_dict_after_heading(md: str, heading: str) -> dict[str, str]:
    rows = table_after_heading(md, heading)
    return {row[0]: row[1] for row in rows[1:] if len(row) >= 2}


def first_table_in(md: str) -> list[list[str]]:
    lines = md.splitlines()
    out: list[str] = []
    collecting = False
    for line in lines:
        if line.startswith("|"):
            collecting = True
            out.append(line)
        elif collecting:
            break
    return parse_table(out)


def table_after_marker(md: str, marker: str) -> list[list[str]]:
    idx = md.find(marker)
    if idx < 0:
        return []
    lines = md[idx + len(marker) :].splitlines()
    out: list[str] = []
    collecting = False
    for line in lines:
        if line.startswith("|"):
            collecting = True
            out.append(line)
        elif collecting:
            break
    return parse_table(out)


def paragraph_after(md: str, marker: str) -> str:
    idx = md.find(marker)
    if idx < 0:
        return ""
    rest = md[idx + len(marker) :].strip()
    parts = re.split(r"\n\s*\n", rest, maxsplit=1)
    return clean(parts[0])


def paragraph_containing(md: str, phrase: str) -> str:
    paragraphs = re.split(r"\n\s*\n", md)
    for paragraph in paragraphs:
        if phrase in paragraph:
            return clean(" ".join(line.strip() for line in paragraph.splitlines()))
    return ""


def finding_block(md: str, title: str, next_title: str | None = None) -> str:
    start = md.find(title)
    if start < 0:
        return ""
    end = md.find(next_title, start + len(title)) if next_title else -1
    if end < 0:
        end = len(md)
    return md[start:end]


def code_block_after(md: str, marker: str) -> str:
    idx = md.find(marker)
    if idx < 0:
        return ""
    match = re.search(r"```(?:[a-zA-Z0-9_-]+)?\n(.*?)\n```", md[idx:], re.DOTALL)
    return match.group(1).strip() if match else ""


def section_after_heading(md: str, heading: str) -> str:
    idx = md.find(heading)
    if idx < 0:
        return ""
    rest = md[idx + len(heading) :].strip()
    match = re.search(r"\n##\s+", rest)
    return rest[: match.start()].strip() if match else rest


def retest_plan_summary(md: str) -> str:
    section = section_after_heading(md, "## Retest Plan")
    if not section:
        return ""
    lines = [clean(line.lstrip("- ").rstrip(";.")) for line in section.splitlines() if line.strip()]
    intro: list[str] = []
    checks: list[str] = []
    for line in lines:
        if line.startswith("-"):
            continue
        if "requires:" in line:
            intro.append(line.replace(" requires:", " requires"))
        elif line.startswith("no ") or line.startswith("both ") or line.startswith("trace "):
            checks.append(line)
        else:
            intro.append(line)
    if not intro:
        intro = ["After remediation, rerun the same 8 scenarios against the staging agent."]
    if checks:
        return f"{' '.join(intro)}: " + "; ".join(checks) + "."
    return " ".join(intro)


def short_environment(value: str) -> str:
    return "Staging only" if "Staging" in value else value


def short_evidence(value: str) -> str:
    return "Tool-call traces" if "Tool-call traces" in value else value


def short_classification(value: str) -> str:
    return "Public synthetic sample" if "Public sample" in value else value


def wrap(text: str, font: str, size: int, width: float) -> list[str]:
    return simpleSplit(clean(text), font, size, width)


def draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    font: str = "Helvetica",
    size: int = 9,
    leading: float = 12,
    color=INK,
    max_lines: int | None = None,
) -> float:
    c.setFont(font, size)
    c.setFillColor(color)
    lines = wrap(text, font, size, width)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def panel(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill=WHITE, stroke=LINE) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, 6, fill=1, stroke=1)


def label(c: canvas.Canvas, text: str, x: float, y: float, color=MUTED) -> None:
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 7.6)
    c.drawString(x, y, text.upper())


def status_chip(c: canvas.Canvas, text: str, x: float, y: float, color, fill) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(fill)
    c.roundRect(x, y - 2, 38, 15, 7, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(x + 19, y + 2, text)


def draw_page_header(c: canvas.Canvas, meta: dict[str, str], title: str) -> None:
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(42, PAGE_H - 48, "AGENT AUTHORIZATION REVIEW")
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(42, PAGE_H - 76, title)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 10)
    c.drawString(42, PAGE_H - 96, "Trace-based review of high-impact agent actions against trusted authorization evidence.")

    panel(c, PAGE_W - 286, PAGE_H - 112, 244, 72, PAPER, LINE)
    label(c, "Prepared by", PAGE_W - 270, PAGE_H - 62)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(INK)
    c.drawString(PAGE_W - 270, PAGE_H - 76, meta.get("Prepared by", "Jiahao Zhang, JZ Software Consulting")[:44])
    label(c, "Report", PAGE_W - 270, PAGE_H - 94)
    c.setFont("Helvetica", 8.5)
    c.setFillColor(INK)
    c.drawString(PAGE_W - 228, PAGE_H - 94, f"{meta.get('Version', 'Sample')} | {meta.get('Report date', '')}")

    c.setStrokeColor(TEAL)
    c.setLineWidth(1.6)
    c.line(42, PAGE_H - 126, PAGE_W - 42, PAGE_H - 126)


def draw_simple_table(
    c: canvas.Canvas,
    rows: list[list[str]],
    x: float,
    y_top: float,
    widths: list[float],
    font_size: int = 8,
    leading: float = 10,
    max_rows: int | None = None,
) -> float:
    if not rows:
        return y_top
    rows = rows[: max_rows or len(rows)]
    header = rows[0]
    body = rows[1:]
    y = y_top

    def row_height(row: list[str]) -> float:
        heights = []
        for cell, width in zip(row, widths):
            lines = wrap(cell, "Helvetica", font_size, width - 8)
            heights.append(max(1, len(lines)) * leading + 9)
        return max(22, max(heights))

    h = row_height(header)
    c.setFillColor(PAPER)
    c.setStrokeColor(LINE)
    c.rect(x, y - h, sum(widths), h, fill=1, stroke=1)
    cx = x
    for cell, width in zip(header, widths):
        label(c, cell, cx + 4, y - 14, MUTED)
        cx += width
    y -= h

    for idx, row in enumerate(body):
        h = row_height(row)
        c.setFillColor(WHITE if idx % 2 == 0 else HexColor("#fbfcfd"))
        c.setStrokeColor(LIGHT_LINE)
        c.rect(x, y - h, sum(widths), h, fill=1, stroke=1)
        cx = x
        for cell, width in zip(row, widths):
            font = "Helvetica-Bold" if cell in {"Fail", "Pass", "Critical", "High"} else "Helvetica"
            color = RED if cell == "Fail" else GREEN if cell == "Pass" else INK
            draw_wrapped(c, cell, cx + 4, y - 12, width - 8, font, font_size, leading, color)
            cx += width
        y -= h
    return y


def overview_page(c: canvas.Canvas, md: str, meta: dict[str, str], source_hash: str) -> None:
    draw_page_header(c, meta, "Sample Evidence Report")
    scope = table_dict_after_heading(md, "## Scope and Method")

    card_y = PAGE_H - 176
    card_w = 166
    cards = [
        ("Target", meta.get("Target system", "Acme AP agent")),
        ("Environment", short_environment(scope.get("Environment", "Staging only"))),
        ("Evidence", short_evidence(scope.get("Evidence source", "Tool-call traces"))),
        ("Classification", short_classification(meta.get("Classification", "Public synthetic sample"))),
    ]
    for i, (k, v) in enumerate(cards):
        x = 42 + i * (card_w + 12)
        panel(c, x, card_y, card_w, 38, PAPER, LINE)
        label(c, k, x + 10, card_y + 24)
        c.setFont("Helvetica-Bold", 9.5)
        c.setFillColor(INK)
        c.drawString(x + 10, card_y + 10, v[:31])

    exec_box = (42, 314, 438, 104)
    panel(c, *exec_box)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(56, 394, "Executive summary")
    summary = paragraph_containing(md, "Overall result:") or "Overall result is documented in the source sample report."
    draw_wrapped(c, summary, 56, 374, 404, "Helvetica", 9, 12, INK, max_lines=5)

    panel(c, 500, 314, 250, 104)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(514, 394, "Risk summary")
    risk_rows = table_after_heading(md, "## Risk Summary")
    compact_risks = []
    for row in risk_rows[1:]:
        if len(row) < 3 or row[0] == "Medium":
            continue
        severity, count, desc = row[0], row[1], row[2]
        if severity == "Critical":
            compact_risks.append((RED_SOFT, RED, f"{count} Critical", desc))
        elif severity == "High":
            compact_risks.append((AMBER_SOFT, AMBER, f"{count} High", desc))
        elif severity == "Passed safely":
            compact_risks.append((GREEN_SOFT, GREEN, f"{count} Safe", desc))
    y = 382
    for fill, color, count, desc in compact_risks:
        c.setFillColor(fill)
        c.roundRect(514, y - 11, 52, 17, 8, fill=1, stroke=0)
        c.setFillColor(color)
        c.setFont("Helvetica-Bold", 7.3)
        c.drawCentredString(540, y - 6, count)
        draw_wrapped(c, desc, 574, y - 2, 154, "Helvetica", 7.8, 9.3, INK, max_lines=2)
        y -= 22

    panel(c, 42, 206, 708, 94)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(56, 276, "Scope and method")
    access_boundary = (
        f"Production access: {scope.get('Production access', 'None')}; "
        f"real customer data: {scope.get('Real customer data', 'None')}; "
        f"credential sharing: {scope.get('Credential sharing', 'None')}"
    )
    scope_items = [
        ("Environment", scope.get("Environment", "")),
        ("Data", scope.get("Data", "")),
        ("Access boundary", access_boundary),
        ("Evidence source", scope.get("Evidence source", "")),
    ]
    for idx, (k, v) in enumerate(scope_items):
        col = idx % 2
        row = idx // 2
        x = 56 + col * 342
        y = 258 - row * 22
        label(c, k, x, y, MUTED)
        draw_wrapped(c, v, x, y - 13, 304, "Helvetica", 7.8, 9.3, INK, max_lines=2)

    scenarios = table_after_heading(md, "## Scenario Matrix")
    scenario_rows = [["ID", "Scenario", "Rule", "Verdict", "Evidence"]]
    for row in scenarios[1:4]:
        scenario_rows.append([row[0], row[1], row[3], row[4], row[5]])
    panel(c, 42, 48, 708, 140)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(56, 168, "Scenario matrix excerpt")
    draw_simple_table(c, scenario_rows, 56, 152, [38, 210, 294, 48, 58], 7.3, 8.5, max_rows=4)

    footer(
        c,
        "Public sample. Synthetic AP workflow. Not a SOC report, certification, legal opinion, or production penetration test.",
        source_hash,
    )
    c.showPage()


def findings_page(c: canvas.Canvas, md: str, meta: dict[str, str], source_hash: str) -> None:
    draw_page_header(c, meta, "Findings and Evidence")
    f1 = finding_block(md, "### F-1 Payment redirected by a vendor email", "### F-2 Approval bypassed by a pre-approved note")
    f2 = finding_block(md, "### F-2 Approval bypassed by a pre-approved note", "## Evidence Register")
    f1_meta_rows = first_table_in(f1)
    f1_meta = {row[0]: row[1] for row in f1_meta_rows[1:] if len(row) >= 2}
    f2_meta_rows = first_table_in(f2)
    f2_meta = {row[0]: row[1] for row in f2_meta_rows[1:] if len(row) >= 2}

    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(42, PAGE_H - 160, "F-1 Payment redirected by vendor email")
    status_chip(c, "FAIL", 354, PAGE_H - 160, RED, RED_SOFT)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(RED)
    c.drawString(402, PAGE_H - 156, f1_meta.get("Severity", "Critical"))

    condition = paragraph_after(f1, "**Condition.**")
    criteria = paragraph_after(f1, "**Criteria.**")
    draw_wrapped(c, "Condition. " + condition, 42, PAGE_H - 184, 438, "Helvetica", 9, 12, INK, max_lines=4)
    draw_wrapped(c, "Criteria. " + criteria, 42, PAGE_H - 236, 438, "Helvetica", 9, 12, INK, max_lines=4)

    panel(c, 42, 250, 438, 92, PAPER, LINE)
    label(c, "Trace excerpt", 56, 320)
    trace = code_block_after(f1, "**Trace excerpt.**")
    c.setFont("Courier", 8)
    c.setFillColor(INK)
    for i, line in enumerate(trace.splitlines()):
        c.drawString(56, 302 - i * 14, line)

    evidence_rows = table_after_marker(f1, "**Authorization evidence.**")
    panel(c, 504, 352, 246, 122)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(518, 448, "Authorization evidence")
    draw_simple_table(c, evidence_rows, 518, 432, [92, 94, 42], 7.4, 8.8, max_rows=2)

    rec = paragraph_after(f1, "**Recommendation.**")
    retest = paragraph_after(f1, "**Retest rule.**")
    panel(c, 504, 198, 246, 134)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(518, 306, "Fix and retest rule")
    draw_wrapped(c, "Fix. " + rec, 518, 288, 216, "Helvetica", 8.2, 10.5, INK, max_lines=5)
    draw_wrapped(c, "Retest. " + retest, 518, 234, 216, "Helvetica", 8.2, 10.5, INK, max_lines=4)

    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(42, 180, "F-2 Approval bypassed by a pre-approved note")
    status_chip(c, "FAIL", 354, 180, RED, RED_SOFT)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(AMBER)
    c.drawString(402, 184, f2_meta.get("Severity", "High"))
    condition2 = paragraph_after(f2, "**Condition.**")
    criteria2 = paragraph_after(f2, "**Criteria.**")
    draw_wrapped(c, "Condition. " + condition2, 42, 156, 332, "Helvetica", 8.5, 11, INK, max_lines=4)
    draw_wrapped(c, "Criteria. " + criteria2, 404, 156, 346, "Helvetica", 8.5, 11, INK, max_lines=4)

    footer(c, "Report evidence comes from staging tool-call traces and workflow-specific authorization rules.", source_hash)
    c.showPage()


def remediation_page(c: canvas.Canvas, md: str, meta: dict[str, str], source_hash: str) -> None:
    draw_page_header(c, meta, "Evidence Register and Remediation")

    evidence = table_after_heading(md, "## Evidence Register")
    evidence_rows = [["ID", "Scenario", "Required evidence", "Observed", "Decision"]]
    for row in evidence[1:5]:
        evidence_rows.append([row[0], row[1], row[3], row[4], row[5]])
    panel(c, 42, 326, 708, 150)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(56, 452, "Evidence register excerpt")
    draw_simple_table(c, evidence_rows, 56, 436, [44, 186, 190, 142, 50], 7.1, 8.5, max_rows=5)

    roadmap = table_after_heading(md, "## Remediation Roadmap")
    roadmap_rows = [["Priority", "Control objective", "Recommended implementation", "Retest evidence"]]
    for row in roadmap[1:5]:
        roadmap_rows.append([row[0], row[1], row[2], row[4]])
    panel(c, 42, 130, 708, 174)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(56, 280, "Remediation roadmap")
    draw_simple_table(c, roadmap_rows, 56, 264, [48, 142, 334, 114], 7.1, 8.5, max_rows=5)

    panel(c, 42, 52, 708, 58, TEAL_SOFT, LINE)
    c.setFillColor(TEAL_DARK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(56, 90, "Retest plan")
    retest = retest_plan_summary(md)
    draw_wrapped(c, retest, 56, 74, 486, "Helvetica", 8.3, 10.5, INK, max_lines=3)

    c.setStrokeColor(LINE)
    c.line(558, 62, 558, 100)
    label(c, "Source-backed sample", 574, 91, TEAL_DARK)
    draw_wrapped(
        c,
        f"Rendered from source Markdown. Hash prefix: {source_hash}. Real reports use client traces.",
        574,
        76,
        150,
        "Helvetica",
        7.3,
        9.2,
        INK,
        max_lines=3,
    )

    footer(c, "Prepared by Jiahao Zhang, JZ Software Consulting. Public sample for ActionBoundary.", source_hash)
    c.showPage()


def footer(c: canvas.Canvas, text: str, source_hash: str) -> None:
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(42, 38, PAGE_W - 42, 38)
    c.setFont("Helvetica", 7.2)
    c.setFillColor(MUTED)
    c.drawString(42, 25, text)
    provenance = f"Generated from {SOURCE_LABEL} by {SCRIPT_LABEL}. Source SHA-256 prefix: {source_hash}"
    c.setFont("Helvetica", 6.6)
    c.drawString(42, 13, provenance)


def render_pdf(target_pdf: Path) -> None:
    md = read_source()
    meta = first_table(md)
    source_hash = source_short_hash(md)
    c = canvas.Canvas(str(target_pdf), pagesize=PAGE)
    c.setTitle("Agent Authorization Review Sample Evidence Report")
    c.setAuthor("Jiahao Zhang, JZ Software Consulting")
    overview_page(c, md, meta, source_hash)
    findings_page(c, md, meta, source_hash)
    remediation_page(c, md, meta, source_hash)
    c.save()


def pdftoppm_candidates() -> list[str]:
    candidates: list[str] = []
    found = shutil.which("pdftoppm")
    if found:
        candidates.append(found)
    candidates.append(str(Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "native" / "poppler" / "Library" / "bin" / "pdftoppm.exe"))
    candidates.append(str(Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "bin" / "pdftoppm.cmd"))
    return [candidate for candidate in candidates if Path(candidate).exists()]


def render_preview_png(source_pdf: Path, target_png: Path) -> None:
    candidates = pdftoppm_candidates()
    if not candidates:
        raise RuntimeError("pdftoppm was not found. Install Poppler or use the bundled Codex runtime.")
    prefix = target_png.with_suffix("")
    cmd = [
        candidates[0],
        "-f",
        "1",
        "-l",
        "1",
        "-singlefile",
        "-png",
        "-r",
        "180",
        str(source_pdf),
        str(prefix),
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    for temp_path in (TEMP_PDF, TEMP_PNG):
        if temp_path.exists():
            temp_path.unlink()
    render_pdf(TEMP_PDF)
    render_preview_png(TEMP_PDF, TEMP_PNG)
    try:
        TEMP_PDF.replace(OUTPUT_PDF)
        TEMP_PNG.replace(OUTPUT_PNG)
    except PermissionError as exc:
        print(
            "Rendered temporary files, but could not replace the final PDF/PNG. "
            "Close any open PDF viewer for docs/sample-evidence-report.pdf and rerun this script.",
            file=sys.stderr,
        )
        print(f"temporary PDF: {TEMP_PDF.relative_to(ROOT)}", file=sys.stderr)
        print(f"temporary PNG: {TEMP_PNG.relative_to(ROOT)}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"wrote {OUTPUT_PDF.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_PNG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

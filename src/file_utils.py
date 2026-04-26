import base64
import html
import io
import re
from dataclasses import dataclass
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
CODE_RE = re.compile(r"`([^`]+)`")
HEADING_NOISE_RE = re.compile(r"^[\ufeff\u2022\u25A0\u25AA\u25AB\u00B7]+")
ORDERED_BULLET_RE = re.compile(r"^\s*(\d+)\.\s+(.+)$")
PAGEBREAK_MARKERS = {"\\f", "---PAGE---", "---PAGEBREAK---", "<!-- pagebreak -->", "<!--PAGEBREAK-->"}
IMAGE_RE = re.compile(r"!\[.*?\]\((.*?)\)")

def get_image_data(src: str, images_map: dict = None) -> io.BytesIO:
    if not src:
        return None
    if src.startswith("data:image"):
        try:
            _, encoded = src.split(",", 1)
            return io.BytesIO(base64.b64decode(encoded))
        except Exception:
            return None
    if images_map and src in images_map:
        return images_map[src]
    return None


@dataclass
class Block:
    type: str
    data: Any


def clean_heading_text(text: str) -> str:
    cleaned = HEADING_NOISE_RE.sub("", (text or "").strip())
    cleaned = re.sub(r"^\s*#+\s*", "", cleaned).strip()
    return cleaned


def markdown_inline_to_rl(text: str) -> str:
    escaped = html.escape(text or "")
    escaped = CODE_RE.sub(r'<font name="Courier" color="#0F766E">\1</font>', escaped)
    escaped = BOLD_RE.sub(r"<b>\1</b>", escaped)
    escaped = ITALIC_RE.sub(r"<i>\1</i>", escaped)
    return escaped


def add_markdown_runs(paragraph, text: str) -> None:
    """
    Render inline markdown emphasis into a DOCX paragraph.

    Args:
        paragraph: Target python-docx paragraph object.
        text (str): Source text with simple markdown markers.

    Returns:
        None: Mutates paragraph runs in-place.
    """
    paragraph.text = ""
    tokens = re.split(r"(\*\*.*?\*\*|\*[^*]+\*|`[^`]+`)", text or "")
    for token in tokens:
        if not token:
            continue
        if token.startswith("**") and token.endswith("**") and len(token) >= 4:
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        elif token.startswith("*") and token.endswith("*") and len(token) >= 3:
            run = paragraph.add_run(token[1:-1])
            run.italic = True
        elif token.startswith("`") and token.endswith("`") and len(token) >= 3:
            run = paragraph.add_run(token[1:-1])
            run.font.name = "Consolas"
            run.font.color.rgb = RGBColor(15, 118, 110)
        else:
            paragraph.add_run(token)


def format_docx_paragraph(paragraph, is_bullet: bool = False) -> None:
    """
    Apply paragraph spacing, line-height, alignment, and optional bullet indentation.

    Args:
        paragraph: Target python-docx paragraph object.
        is_bullet (bool, optional): Whether to apply bullet-style indentation.

    Returns:
        None: Mutates paragraph formatting in-place.
    """
    pf = paragraph.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(8)
    pf.line_spacing = 1.2
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if is_bullet:
        pf.left_indent = Inches(0.58)
        pf.first_line_indent = Inches(-0.24)


def parse_markdown_table_row(line: str) -> list[str]:
    row = line.strip().strip("|")
    return [cell.strip() for cell in row.split("|")]


def extract_report_blocks(content: str) -> list[Block]:
    """
    Parse markdown report content into structured blocks for rendering.

    Args:
        content (str): Raw markdown content.

    Returns:
        list[Block]: Parsed sequence of headings, paragraphs, bullets, tables, and page-break blocks.
    """
    lines = (content or "").replace("\r\n", "\n").split("\n")
    blocks: list[Block] = []
    i = 0
    paragraph_buf: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_buf:
            text = " ".join(x.strip() for x in paragraph_buf if x.strip()).strip()
            if text:
                blocks.append(Block("paragraph", text))
            paragraph_buf.clear()

    while i < len(lines):
        raw = lines[i].lstrip("\ufeff")
        line = HEADING_NOISE_RE.sub("", raw).strip()

        if not line:
            flush_paragraph()
            i += 1
            continue

        if line in PAGEBREAK_MARKERS:
            flush_paragraph()
            blocks.append(Block("page_break", None))
            i += 1
            continue

        if line.startswith("### "):
            flush_paragraph()
            blocks.append(Block("heading", (3, clean_heading_text(line[4:]))))
            i += 1
            continue
        if line.startswith("## "):
            flush_paragraph()
            blocks.append(Block("heading", (2, clean_heading_text(line[3:]))))
            i += 1
            continue
        if line.startswith("# "):
            flush_paragraph()
            blocks.append(Block("heading", (1, clean_heading_text(line[2:]))))
            i += 1
            continue

        if line.startswith("|") and i + 1 < len(lines) and "|" in lines[i + 1] and "-" in lines[i + 1]:
            flush_paragraph()
            rows: list[list[str]] = [parse_markdown_table_row(line)]
            i += 2
            while i < len(lines):
                row_line = lines[i].strip()
                if not row_line.startswith("|"):
                    break
                rows.append(parse_markdown_table_row(row_line))
                i += 1
            blocks.append(Block("table", rows))
            continue

        ordered = ORDERED_BULLET_RE.match(line)
        img_match = IMAGE_RE.match(line.strip())

        if img_match:
            flush_paragraph()
            blocks.append(Block("image", img_match.group(1)))
            i += 1
            continue

        if line.startswith("- ") or line.startswith("* "):
            flush_paragraph()
            blocks.append(Block("bullet", line[2:].strip()))
            i += 1
            continue
        if ordered:
            flush_paragraph()
            blocks.append(Block("ordered", (int(ordered.group(1)), ordered.group(2).strip())))
            i += 1
            continue

        paragraph_buf.append(line)
        i += 1

    flush_paragraph()
    return blocks


def build_docx_report(doc: Document, content: str, report_title: str, images_map: dict = {}) -> None:
    """
    Build a DOCX report from markdown content using project formatting rules.

    Args:
        doc (Document): Target python-docx Document instance.
        content (str): Markdown report content.
        report_title (str): Report title used for metadata/title rendering.

    Returns:
        None: The provided document object is mutated in-place.
    """
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.2

    heading_1 = doc.styles["Heading 1"]
    heading_1.font.name = "Arial"
    heading_1.font.bold = True
    heading_1.font.size = Pt(18)
    heading_1.font.color.rgb = RGBColor(0, 0, 0)
    heading_1.paragraph_format.space_before = Pt(8)
    heading_1.paragraph_format.space_after = Pt(10)

    heading_2 = doc.styles["Heading 2"]
    heading_2.font.name = "Arial"
    heading_2.font.bold = True
    heading_2.font.size = Pt(14)
    heading_2.font.color.rgb = RGBColor(0, 0, 0)
    heading_2.paragraph_format.space_before = Pt(8)
    heading_2.paragraph_format.space_after = Pt(8)

    heading_3 = doc.styles["Heading 3"]
    heading_3.font.name = "Arial"
    heading_3.font.bold = True
    heading_3.font.size = Pt(12)
    heading_3.font.color.rgb = RGBColor(0, 0, 0)
    heading_3.paragraph_format.space_before = Pt(6)
    heading_3.paragraph_format.space_after = Pt(6)

    if doc.sections:
        sec = doc.sections[0]
        sec.top_margin = Inches(0.8)
        sec.bottom_margin = Inches(0.8)
        sec.left_margin = Inches(0.85)
        sec.right_margin = Inches(0.85)

    doc.core_properties.title = clean_heading_text(report_title)
    blocks = extract_report_blocks(content)

    for block in blocks:
        if block.type == "heading":
            level, text = block.data
            doc.add_heading(text, level=max(1, min(level, 3)))
        elif block.type == "paragraph":
            p = doc.add_paragraph("")
            add_markdown_runs(p, block.data)
            format_docx_paragraph(p)
        elif block.type == "bullet":
            p = doc.add_paragraph("", style="List Bullet")
            add_markdown_runs(p, block.data)
            format_docx_paragraph(p, is_bullet=True)
        elif block.type == "ordered":
            p = doc.add_paragraph("", style="List Number")
            _, ordered_text = block.data
            add_markdown_runs(p, ordered_text)
            format_docx_paragraph(p, is_bullet=True)
        elif block.type == "table":
            rows: list[list[str]] = block.data
            cols = max(len(r) for r in rows)
            table = doc.add_table(rows=1, cols=cols)
            table.style = "Table Grid"

            for c, text in enumerate(rows[0]):
                p = table.rows[0].cells[c].paragraphs[0]
                add_markdown_runs(p, text)
                for run in p.runs:
                    run.bold = True

            for row in rows[1:]:
                cells = table.add_row().cells
                for c, text in enumerate(row):
                    p = cells[c].paragraphs[0]
                    add_markdown_runs(p, text)

            doc.add_paragraph("")
        elif block.type == "page_break":
            doc.add_page_break()
        elif block.type == "image":
            img_data = get_image_data(block.data, images_map)
            if img_data:
                try:
                    p = doc.add_paragraph("")
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = p.add_run()
                    img_data.seek(0)
                    run.add_picture(img_data, width=Inches(6))
                except Exception as e:
                    print(f"Error adding image to docx: {e}")


def build_pdf_report(
    file_path: str,
    content: str,
    report_title: str,
    images_map: dict = None
) -> None:
    """
    Build a PDF report from markdown content using reportlab styles.

    Args:
        file_path (str): Output PDF file path.
        content (str): Markdown report content.
        report_title (str): Report title used for document metadata/title rendering.

    Returns:
        None: Writes the PDF file to `file_path`.
    """
    body_font, body_bold = "Helvetica", "Helvetica-Bold"
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName=body_bold,
        fontSize=18,
        leading=22,
        spaceAfter=12,
    )
    h1 = ParagraphStyle("ReportH1", parent=styles["Heading1"], fontName=body_bold, fontSize=14, leading=18)
    h2 = ParagraphStyle("ReportH2", parent=styles["Heading2"], fontName=body_bold, fontSize=12.5, leading=16)
    h3 = ParagraphStyle("ReportH3", parent=styles["Heading3"], fontName=body_bold, fontSize=11.5, leading=15)

    body = ParagraphStyle(
        "BodyReport",
        parent=styles["BodyText"],
        fontName=body_font,
        fontSize=10,
        leading=14,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
    )
    bullet = ParagraphStyle(
        "BulletReport",
        parent=body,
        leftIndent=42,
        bulletIndent=24,
        spaceAfter=8,
    )
    ordered = ParagraphStyle(
        "OrderedReport",
        parent=body,
        leftIndent=42,
        firstLineIndent=-18,
        spaceAfter=8,
    )

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        title=clean_heading_text(report_title),
    )

    blocks = extract_report_blocks(content)
    elements = []

    for block in blocks:
        if block.type == "heading":
            level, text = block.data
            rich = markdown_inline_to_rl(clean_heading_text(text))
            if level == 1:
                elements.append(Paragraph(rich, title_style))
            elif level == 2:
                elements.append(Paragraph(rich, h1))
            elif level == 3:
                elements.append(Paragraph(rich, h2))
            else:
                elements.append(Paragraph(rich, h3))
            elements.append(Spacer(1, 8))
        elif block.type == "paragraph":
            elements.append(Paragraph(markdown_inline_to_rl(block.data), body))
        elif block.type == "bullet":
            elements.append(Paragraph(markdown_inline_to_rl(block.data), bullet, bulletText="\u2022"))
        elif block.type == "ordered":
            ordered_no, ordered_text = block.data
            elements.append(Paragraph(markdown_inline_to_rl(f"{ordered_no}. {ordered_text}"), ordered))
        elif block.type == "table":
            rows: list[list[str]] = block.data
            styled_rows = [
                [Paragraph(markdown_inline_to_rl(str(cell)), body) for cell in row]
                for row in rows
            ]
            table = Table(styled_rows, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (-1, 0), body_bold),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            elements.append(table)
            elements.append(Spacer(1, 10))
        elif block.type == "page_break":
            elements.append(PageBreak())
        elif block.type == "image":
            img_data = get_image_data(block.data, images_map)
            if img_data:
                try:
                    from reportlab.platypus import Image as RLImage
                    import PIL.Image as PILImage
                    img_data.seek(0)
                    pil_img = PILImage.open(img_data)
                    width, height = pil_img.size
                    
                    max_width = 6 * inch
                    if width > max_width:
                        ratio = max_width / width
                        width = max_width
                        height = height * ratio
                        
                    img_data.seek(0)
                    img = RLImage(img_data, width=width, height=height)
                    elements.append(img)
                    elements.append(Spacer(1, 10))
                except Exception as e:
                    print(f"Error adding image to pdf: {e}")

    doc.build(elements)

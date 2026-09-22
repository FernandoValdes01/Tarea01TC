"""Genera el informe PDF final desde el Markdown y los diagramas versionados."""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from build_report_diagrams import DEFAULT_OUTPUT as DEFAULT_APPENDIX
from build_report_diagrams import build as build_diagrams


ROOT = Path(__file__).resolve().parents[1]
REPORT_SOURCE = ROOT / "docs" / "informe" / "informe_tecnico.md"
DEFAULT_OUTPUT = ROOT / "docs" / "informe" / "Fernandovaldestareaspark.pdf"
LOGO = ROOT / "docs" / "ing_civil-informatica_gris.png"

BLUE = colors.HexColor("#007DB3")
DARK_BLUE = colors.HexColor("#183B56")
YELLOW = colors.HexColor("#FDC400")
GREY = colors.HexColor("#858789")
LIGHT_BLUE = colors.HexColor("#E8F3F8")
LIGHT_GREY = colors.HexColor("#F4F5F5")
INK = colors.HexColor("#263238")


def register_fonts() -> tuple[str, str, str]:
    font_dir = Path("/usr/share/fonts/truetype/dejavu")
    regular = font_dir / "DejaVuSans.ttf"
    bold = font_dir / "DejaVuSans-Bold.ttf"
    mono = font_dir / "DejaVuSansMono.ttf"
    if regular.is_file() and bold.is_file() and mono.is_file():
        pdfmetrics.registerFont(TTFont("ReportSans", regular))
        pdfmetrics.registerFont(TTFont("ReportSans-Bold", bold))
        pdfmetrics.registerFont(TTFont("ReportMono", mono))
        return "ReportSans", "ReportSans-Bold", "ReportMono"
    return "Helvetica", "Helvetica-Bold", "Courier"


def inline_markup(text: str, regular: str, mono: str) -> str:
    parts = re.split(r"(`[^`]*`)", text)
    rendered: list[str] = []
    for part in parts:
        if part.startswith("`") and part.endswith("`"):
            rendered.append(
                f'<font name="{mono}" color="#333333">{html.escape(part[1:-1])}</font>'
            )
            continue
        escaped = html.escape(part)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
        escaped = re.sub(
            r"(https://[^\s<]+)",
            r'<link href="\1" color="#1F4E78">\1</link>',
            escaped,
        )
        rendered.append(escaped)
    return "".join(rendered)


def make_styles(regular: str, bold: str, mono: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=9.4,
            leading=13.2,
            spaceAfter=6,
            textColor=INK,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName=bold,
            fontSize=17,
            leading=21,
            textColor=DARK_BLUE,
            spaceBefore=12,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName=bold,
            fontSize=13,
            leading=16,
            textColor=DARK_BLUE,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName=bold,
            fontSize=11,
            leading=14,
            textColor=BLUE,
            spaceBefore=8,
            spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=9.2,
            leading=12.5,
            leftIndent=14,
            firstLineIndent=-8,
            bulletIndent=5,
            spaceAfter=3,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName=mono,
            fontSize=7.5,
            leading=10,
            backColor=LIGHT_GREY,
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=7,
        ),
        "table": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=6.7,
            leading=8.6,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["BodyText"],
            fontName=bold,
            fontSize=6.8,
            leading=8.7,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
    }


def markdown_table(
    rows: list[list[str]],
    styles: dict[str, ParagraphStyle],
    regular: str,
    mono: str,
    width: float,
) -> Table:
    column_count = max(len(row) for row in rows)
    normalized = [row + [""] * (column_count - len(row)) for row in rows]
    data = []
    for row_index, row in enumerate(normalized):
        style = styles["table_header"] if row_index == 0 else styles["table"]
        data.append([Paragraph(inline_markup(cell, regular, mono), style) for cell in row])
    table = Table(data, colWidths=[width / column_count] * column_count, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
                ("LINEBELOW", (0, 0), (-1, 0), 1.1, YELLOW),
                ("LINEBELOW", (0, 1), (-1, -2), 0.25, colors.HexColor("#D4D9DC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def split_markdown_row(line: str) -> list[str]:
    """Divide una fila sin cortar ``|`` escapados o incluidos en código inline."""

    content = line.strip().strip("|")
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    index = 0
    while index < len(content):
        char = content[index]
        if char == "\\" and index + 1 < len(content) and content[index + 1] == "|":
            current.extend((char, "|"))
            index += 2
            continue
        if char == "`":
            in_code = not in_code
            current.append(char)
            index += 1
            continue
        if char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    cells.append("".join(current).strip())
    return cells


def parse_markdown(
    text: str,
    styles: dict[str, ParagraphStyle],
    regular: str,
    mono: str,
    available_width: float,
) -> list:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "### Resumen")
    lines = lines[start:]
    story: list = []
    paragraph: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        if paragraph:
            content = " ".join(part.strip() for part in paragraph)
            story.append(Paragraph(inline_markup(content, regular, mono), styles["body"]))
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            language = stripped[3:].strip()
            index += 1
            code: list[str] = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code.append(lines[index])
                index += 1
            caption = f"Código ({language})" if language else "Código"
            story.append(
                KeepTogether(
                    [
                        Paragraph(caption, styles["h3"]),
                        Preformatted("\n".join(code), styles["code"]),
                    ]
                )
            )
            index += 1
            continue
        if stripped.startswith("|") and index + 1 < len(lines):
            separator = lines[index + 1].strip()
            if separator.startswith("|") and re.fullmatch(r"[| :\-]+", separator):
                flush_paragraph()
                raw_rows: list[list[str]] = []
                while index < len(lines) and lines[index].strip().startswith("|"):
                    current = lines[index].strip()
                    if not re.fullmatch(r"[| :\-]+", current):
                        raw_rows.append(split_markdown_row(current))
                    index += 1
                story.extend(
                    [
                        markdown_table(raw_rows, styles, regular, mono, available_width),
                        Spacer(1, 7),
                    ]
                )
                continue
        heading = re.match(r"^(#{2,4})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            title = heading.group(2)
            style = styles["h1"] if level == 2 else styles["h2"] if level == 3 else styles["h3"]
            story.append(Paragraph(inline_markup(title, regular, mono), style))
            index += 1
            continue
        if stripped.startswith("- "):
            flush_paragraph()
            story.append(
                Paragraph(
                    inline_markup(stripped[2:], regular, mono),
                    styles["bullet"],
                    bulletText="•",
                )
            )
            index += 1
            continue
        paragraph.append(stripped)
        index += 1
    flush_paragraph()
    return story


def page_decorations(canvas, document) -> None:
    page = canvas.getPageNumber()
    if page == 1:
        return
    canvas.saveState()
    canvas.setFillColor(BLUE)
    canvas.rect(0, A4[1] - 0.22 * cm, A4[0], 0.22 * cm, stroke=0, fill=1)
    canvas.setStrokeColor(colors.HexColor("#C9D7DE"))
    canvas.line(2 * cm, A4[1] - 1.4 * cm, A4[0] - 2 * cm, A4[1] - 1.4 * cm)
    canvas.setFont(document.regular_font, 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(2 * cm, A4[1] - 1.15 * cm, "UNIVERSIDAD CATÓLICA DE TEMUCO  ·  INFO1148")
    canvas.setFillColor(YELLOW)
    canvas.circle(A4[0] - 2 * cm - 20, 1.13 * cm, 2.2, stroke=0, fill=1)
    canvas.setFillColor(GREY)
    canvas.drawRightString(A4[0] - 2 * cm, 1.05 * cm, f"{page:02d}")
    canvas.restoreState()


def build_base_pdf(output: Path) -> None:
    regular, bold, mono = register_fonts()
    styles = make_styles(regular, bold, mono)
    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="Análisis léxico del lenguaje Prolog",
        author="Fernando Valdés; Juan Muñoz; Vicente Rivera",
    )
    document.regular_font = regular
    width = A4[0] - 4 * cm
    if not LOGO.is_file():
        raise FileNotFoundError(LOGO)
    story: list = [Spacer(1, 0.5 * cm)]
    logo = Image(str(LOGO), width=16.4 * cm, height=3.28 * cm)
    logo.hAlign = "LEFT"
    story.extend([logo, Spacer(1, 1.8 * cm)])
    story.append(
        Paragraph(
            "INFORME DE TAREA",
            ParagraphStyle(
                "CoverTitle",
                fontName=bold,
                fontSize=11,
                leading=14,
                alignment=TA_LEFT,
                textColor=GREY,
                spaceAfter=7,
            ),
        )
    )
    story.append(Table([["", ""]], colWidths=[1.5 * cm, width - 1.5 * cm], rowHeights=[0.11 * cm], style=TableStyle([("BACKGROUND",(0,0),(0,0),YELLOW),("BACKGROUND",(1,0),(1,0),BLUE)])))
    story.append(Spacer(1, 0.55 * cm))
    story.append(
        Paragraph(
            "Análisis léxico del lenguaje Prolog",
            ParagraphStyle(
                "CoverSubtitle",
                fontName=bold,
                fontSize=27,
                leading=32,
                alignment=TA_LEFT,
                textColor=DARK_BLUE,
            ),
        )
    )
    story.append(Spacer(1, 0.28 * cm))
    story.append(
        Paragraph(
            "Diseño, implementación y validación de un analizador léxico para un subconjunto de Prolog",
            ParagraphStyle(
                "Course",
                fontName=regular,
                fontSize=11.5,
                leading=16.5,
                alignment=TA_LEFT,
                textColor=GREY,
            ),
        )
    )
    story.append(Spacer(1, 1.35 * cm))
    cover_data = [
        ["ASIGNATURA", "Teoría de la Computación · INFO1148"],
        ["ESTUDIANTES", "Fernando Valdés · Juan Muñoz · Vicente Rivera"],
        ["PROFESOR", "Prof. M. Lévano"],
        ["ENTREGA", "17 de septiembre de 2026"],
        ["REPOSITORIO", "github.com/FernandoValdes01/Tarea01TC"],
    ]
    cover_label = ParagraphStyle("CoverLabel",fontName=bold,fontSize=7.2,leading=10,textColor=BLUE)
    cover_value = ParagraphStyle("CoverValue",fontName=regular,fontSize=9.2,leading=12.5,textColor=INK)
    cover_table = Table(
        [[Paragraph(html.escape(a), cover_label), Paragraph(inline_markup(b, regular, mono), cover_value)] for a, b in cover_data],
        colWidths=[3.1 * cm, width - 3.1 * cm],
    )
    cover_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
                ("LINEBELOW", (0, 0), (-1, -2), 0.35, colors.HexColor("#D4D9DC")),
                ("LINEBEFORE", (0, 0), (0, -1), 3, BLUE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend([cover_table, Spacer(1, 1.0 * cm)])
    story.append(
        Paragraph(
            "TEMUCO · CHILE · 2026",
            ParagraphStyle(
                "Place",
                fontName=regular,
                fontSize=7.5,
                textColor=GREY,
                alignment=TA_LEFT,
            ),
        )
    )
    story.append(PageBreak())
    story.extend(
        parse_markdown(
            REPORT_SOURCE.read_text(encoding="utf-8"),
            styles,
            regular,
            mono,
            width,
        )
    )
    document.build(story, onFirstPage=page_decorations, onLaterPages=page_decorations)


def build_final(output: Path, appendix: Path = DEFAULT_APPENDIX) -> None:
    pdfunite = shutil.which("pdfunite")
    if pdfunite is None:
        raise RuntimeError("pdfunite no está disponible")
    output.parent.mkdir(parents=True, exist_ok=True)
    build_diagrams(appendix)
    with TemporaryDirectory(prefix="prolog-report-") as temporary_directory:
        base = Path(temporary_directory) / "informe_base.pdf"
        build_base_pdf(base)
        subprocess.run([pdfunite, str(base), str(appendix), str(output)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="ruta del PDF final (por defecto: %(default)s)",
    )
    args = parser.parse_args()
    build_final(args.output)
    print(f"Informe final generado: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

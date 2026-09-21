"""Construye un anexo PDF con los diagramas Mermaid renderizados."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parents[1]
DIAGRAM_DIR = ROOT / "docs" / "automatas" / "diagramas"
DEFAULT_OUTPUT = ROOT / "docs" / "informe" / "automatas_appendix.pdf"

DIAGRAMS = (
    ("Figura 1. AFD de átomos", "atomos.mmd"),
    ("Figura 2. AFD de variables y variable anónima", "variables.mmd"),
    ("Figura 3. AFD de números", "numeros.mmd"),
    ("Figura 4. AFD de literales entrecomillados", "literales.mmd"),
    ("Figura 5. AFD de comentarios", "comentarios.mmd"),
    ("Figura 6. Trie de operadores", "operadores.mmd"),
    ("Figura 7. AFN representativo de operadores", "afn_operadores.mmd"),
    ("Figura 8. AFD por construcción de subconjuntos", "afd_subconjuntos.mmd"),
    ("Figura 9. AFD mínimo etiquetado", "afd_minimo.mmd"),
)


def render_mermaid(source: Path, png: Path) -> None:
    executable = shutil.which("mmdc")
    command = [executable] if executable is not None else [
        "npx",
        "--yes",
        "@mermaid-js/mermaid-cli",
    ]
    subprocess.run(
        [*command, "-i", str(source), "-o", str(png), "-b", "white", "-t", "default"],
        check=True,
    )


def draw_diagram_page(canvas: Canvas, title: str, png: Path) -> None:
    image = ImageReader(str(png))
    image_width, image_height = image.getSize()
    ratio = image_width / image_height
    page_size = landscape(A4) if ratio < 0.8 else A4
    page_width, page_height = page_size

    margin = 36
    title_height = 42
    max_width = page_width - 2 * margin
    max_height = page_height - 2 * margin - title_height
    scale = min(max_width / image_width, max_height / image_height)
    draw_width = image_width * scale
    draw_height = image_height * scale
    x = (page_width - draw_width) / 2
    y = margin + (max_height - draw_height) / 2

    canvas.setPageSize(page_size)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawCentredString(page_width / 2, page_height - margin, title)
    canvas.drawImage(
        image,
        x,
        y,
        width=draw_width,
        height=draw_height,
        preserveAspectRatio=True,
        mask="auto",
    )
    canvas.showPage()


def build(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="prolog-diagrams-") as temporary_directory:
        temporary = Path(temporary_directory)
        canvas = Canvas(str(output), pagesize=A4)
        canvas.setTitle("Anexo de autómatas - analizador léxico de Prolog")

        canvas.setFont("Helvetica-Bold", 18)
        canvas.drawCentredString(A4[0] / 2, A4[1] - 72, "Anexo A. Diagramas de autómatas")
        canvas.setFont("Helvetica", 11)
        canvas.drawCentredString(
            A4[0] / 2,
            A4[1] - 100,
            "Analizador léxico de un subconjunto de Prolog",
        )
        canvas.drawCentredString(
            A4[0] / 2,
            A4[1] - 124,
            "Fuentes editables: docs/automatas/diagramas/*.mmd",
        )
        canvas.showPage()

        for title, filename in DIAGRAMS:
            source = DIAGRAM_DIR / filename
            if not source.is_file():
                raise FileNotFoundError(source)
            png = temporary / f"{source.stem}.png"
            render_mermaid(source, png)
            draw_diagram_page(canvas, title, png)

        canvas.save()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="ruta del PDF de diagramas (por defecto: %(default)s)",
    )
    args = parser.parse_args()
    build(args.output)
    print(f"PDF de diagramas generado: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

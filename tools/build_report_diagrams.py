"""Construye un anexo PDF vectorial con los autómatas del informe.

Las fuentes Mermaid se conservan como especificación editable de la estructura,
pero la composición del PDF se dibuja de forma explícita. Así se evitan los
cruces, curvas y rótulos superpuestos del diseño automático.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "informe" / "automatas_appendix.pdf"

NAVY = colors.HexColor("#183B56")
DARK_BLUE = colors.HexColor("#183B56")
BLUE = colors.HexColor("#007DB3")
YELLOW = colors.HexColor("#FDC400")
PALE_BLUE = colors.HexColor("#E8F3F8")
INK = colors.HexColor("#20252B")
MUTED = colors.HexColor("#5E6A73")
RULE = colors.HexColor("#C9D7DE")
PAPER = colors.white
SINK_FILL = colors.HexColor("#F2F4F5")
LIGHT_PANEL = colors.HexColor("#F4F5F5")


def register_fonts() -> tuple[str, str, str]:
    directory = Path("/usr/share/fonts/truetype/dejavu")
    paths = [directory / name for name in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSansMono.ttf")]
    if all(path.is_file() for path in paths):
        pdfmetrics.registerFont(TTFont("DiagramSans", paths[0]))
        pdfmetrics.registerFont(TTFont("DiagramSans-Bold", paths[1]))
        pdfmetrics.registerFont(TTFont("DiagramMono", paths[2]))
        return "DiagramSans", "DiagramSans-Bold", "DiagramMono"
    return "Helvetica", "Helvetica-Bold", "Courier"


REGULAR, BOLD, MONO = register_fonts()


@dataclass(frozen=True)
class Node:
    key: str
    x: float
    y: float
    output: str = ""
    accepting: bool = False
    sink: bool = False


def page_header(c: Canvas, number: int, title: str, subtitle: str) -> None:
    width, height = landscape(A4)
    c.setPageSize((width, height))
    c.setFillColor(PAPER)
    c.rect(0, 0, width, height, stroke=0, fill=1)
    c.setFillColor(BLUE)
    c.setFont(MONO, 8)
    c.drawString(34, height - 30, f"FIGURA {number:02d}  |  AUTÓMATAS DEL ANALIZADOR LÉXICO")
    c.setFillColor(NAVY)
    c.setFont(BOLD, 17)
    c.drawString(34, height - 54, title)
    c.setFillColor(MUTED)
    c.setFont(REGULAR, 8.5)
    c.drawString(34, height - 69, subtitle)
    c.setStrokeColor(RULE)
    c.setLineWidth(0.6)
    c.line(34, height - 80, width - 34, height - 80)


def footer(c: Canvas, note: str = "") -> None:
    width, _ = landscape(A4)
    c.setStrokeColor(RULE)
    c.setLineWidth(0.5)
    c.line(34, 28, width - 34, 28)
    c.setFillColor(MUTED)
    c.setFont(REGULAR, 7.2)
    c.drawString(34, 16, note or "Convención: doble círculo = estado de aceptación; SINK = estado sumidero.")
    c.drawRightString(width - 34, 16, "INFO1148 · Teoría de la Computación")


def arrow_head(c: Canvas, x: float, y: float, angle: float, size: float = 6) -> None:
    c.saveState()
    c.translate(x, y)
    c.rotate(math.degrees(angle))
    path = c.beginPath()
    path.moveTo(0, 0)
    path.lineTo(-size, size * 0.48)
    path.lineTo(-size, -size * 0.48)
    path.close()
    c.setFillColor(INK)
    c.drawPath(path, stroke=0, fill=1)
    c.restoreState()


def state(c: Canvas, node: Node, radius: float = 23) -> None:
    c.setFillColor(SINK_FILL if node.sink else PALE_BLUE if node.accepting else PAPER)
    c.setStrokeColor(MUTED if node.sink else NAVY)
    c.setLineWidth(1.25)
    c.circle(node.x, node.y, radius, stroke=1, fill=1)
    if node.accepting:
        c.circle(node.x, node.y, radius - 4, stroke=1, fill=0)
    c.setFillColor(INK)
    c.setFont(BOLD, 9.2)
    c.drawCentredString(node.x, node.y - 3.2, node.key)
    if node.output:
        c.setFillColor(NAVY)
        c.setFont(MONO, 7.1)
        c.drawCentredString(node.x, node.y - radius - 13, node.output)


def start_arrow(c: Canvas, node: Node, radius: float = 23) -> None:
    x1, x2 = node.x - radius - 30, node.x - radius
    c.setStrokeColor(INK)
    c.setLineWidth(1.1)
    c.line(x1, node.y, x2, node.y)
    arrow_head(c, x2, node.y, 0)


def label_box(c: Canvas, x: float, y: float, text: str) -> None:
    c.setFont(MONO, 7.2)
    width = c.stringWidth(text, MONO, 7.2) + 8
    c.setFillColor(PAPER)
    c.rect(x - width / 2, y - 5, width, 11, stroke=0, fill=1)
    c.setFillColor(INK)
    c.drawCentredString(x, y - 2.2, text)


def transition(c: Canvas, a: Node, b: Node, label: str, *, radius: float = 23, label_offset: float = 10, dashed: bool = False) -> None:
    dx, dy = b.x - a.x, b.y - a.y
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    x1, y1 = a.x + ux * radius, a.y + uy * radius
    x2, y2 = b.x - ux * radius, b.y - uy * radius
    c.setStrokeColor(INK)
    c.setLineWidth(1.0)
    if dashed:
        c.setDash(4, 3)
    c.line(x1, y1, x2, y2)
    c.setDash()
    arrow_head(c, x2, y2, math.atan2(dy, dx))
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    nx, ny = -uy, ux
    label_box(c, mx + nx * label_offset, my + ny * label_offset, label)


def poly_transition(c: Canvas, points: list[tuple[float, float]], label: str, lx: float, ly: float, dashed: bool = False) -> None:
    c.setStrokeColor(INK)
    c.setLineWidth(1.0)
    if dashed:
        c.setDash(4, 3)
    path = c.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    c.drawPath(path, stroke=1, fill=0)
    c.setDash()
    x1, y1 = points[-2]
    x2, y2 = points[-1]
    arrow_head(c, x2, y2, math.atan2(y2 - y1, x2 - x1))
    label_box(c, lx, ly, label)


def loop(c: Canvas, node: Node, label: str, radius: float = 23, above: bool = True) -> None:
    # El arco nace y termina en puntos diagonales de la circunferencia. La
    # punta queda exactamente sobre el borde y apunta hacia el estado, de modo
    # que el bucle no parece flotar ni terminar dentro del círculo.
    direction = 1 if above else -1
    angle_start = math.radians(135 if above else 225)
    angle_end = math.radians(45 if above else 315)
    start_x = node.x + radius * math.cos(angle_start)
    start_y = node.y + radius * math.sin(angle_start)
    end_x = node.x + radius * math.cos(angle_end)
    end_y = node.y + radius * math.sin(angle_end)
    control_y = node.y + direction * radius * 2.25
    c.setStrokeColor(INK)
    c.setLineWidth(1.0)
    path = c.beginPath()
    path.moveTo(start_x, start_y)
    path.curveTo(node.x - radius * 1.30, control_y, node.x + radius * 1.30, control_y, end_x, end_y)
    c.drawPath(path, stroke=1, fill=0)
    tangent_angle = math.radians(-135 if above else 135)
    arrow_head(c, end_x, end_y, tangent_angle, size=5.5)
    label_box(c, node.x, node.y + direction * (radius + 37), label)


def legend(c: Canvas, items: list[tuple[str, str]], x: float = 45, y: float = 48) -> None:
    for index, (symbol, text) in enumerate(items):
        px = x + index * 190
        c.setFillColor(PALE_BLUE if symbol == "aceptación" else SINK_FILL)
        c.setStrokeColor(NAVY if symbol == "aceptación" else MUTED)
        c.circle(px, y, 7, stroke=1, fill=1)
        if symbol == "aceptación":
            c.circle(px, y, 4.5, stroke=1, fill=0)
        c.setFillColor(MUTED)
        c.setFont(REGULAR, 7.4)
        c.drawString(px + 13, y - 2.5, text)


def diagram_1(c: Canvas) -> None:
    page_header(c, 1, "AFD para átomos no entrecomillados", "Reconoce LOWER (LOWER U DIGIT U {_})* mediante máxima coincidencia.")
    a0 = Node("a0", 205, 300); a1 = Node("a1", 420, 300, "ATOM", True); dead = Node("SINK", 635, 180, sink=True)
    start_arrow(c, a0); transition(c, a0, a1, "LOWER"); loop(c, a1, "LOWER U DIGIT U {_}")
    transition(c, a0, dead, "otro", label_offset=-12, dashed=True); transition(c, a1, dead, "otro", label_offset=12, dashed=True); loop(c, dead, "SIGMA", above=False)
    for n in (a0, a1, dead): state(c, n)
    legend(c, [("aceptación", "Estado aceptor y token emitido"), ("sumidero", "Estado sumidero")]); footer(c)


def diagram_2(c: Canvas) -> None:
    page_header(c, 2, "AFD para variables", "Distingue variables con nombre de la variable anónima `_`.")
    v0=Node("v0",175,300); vu=Node("vU",385,370,"VARIABLE",True); va=Node("v_",385,205,"ANONYMOUS_VARIABLE",True); vn=Node("vN",625,205,"VARIABLE",True)
    start_arrow(c,v0); transition(c,v0,vu,"UPPER"); transition(c,v0,va,"_"); loop(c,vu,"ID_CONT"); transition(c,va,vn,"ID_CONT"); loop(c,vn,"ID_CONT")
    for n in (v0,vu,va,vn): state(c,n)
    footer(c,"ID_CONT = letras, dígitos o `_`. La variable anónima solo acepta exactamente un guion bajo.")


def diagram_3(c: Canvas) -> None:
    page_header(c,3,"AFD para números","Reconoce enteros y reales sin signo; el punto decimal exige un dígito posterior.")
    n0=Node("n0",135,285); ni=Node("nI",330,285,"INTEGER",True); np=Node("nP",515,285); nr=Node("nR",705,285,"REAL",True)
    start_arrow(c,n0); transition(c,n0,ni,"DIGIT"); loop(c,ni,"DIGIT"); transition(c,ni,np,"."); transition(c,np,nr,"DIGIT"); loop(c,nr,"DIGIT")
    for n in (n0,ni,np,nr): state(c,n)
    footer(c,"nP no es aceptor: una entrada como `5.` se diagnostica como número mal formado.")


def diagram_4(c: Canvas) -> None:
    page_header(c,4,"AFD para literales entrecomillados","Esquema parametrizado por delimitador D: comilla simple o comilla doble.")
    l0=Node("l0",110,300); lb=Node("lB",285,300); le=Node("lE",465,405); lf=Node("lF",650,300,"QUOTED_ATOM / STRING",True); err=Node("ERR",650,145,sink=True)
    start_arrow(c,l0); transition(c,l0,lb,"D"); loop(c,lb,"SAFE_D",above=False); transition(c,lb,le,"\\",label_offset=12); transition(c,le,lb,"VALID_ESCAPE_D",label_offset=12); transition(c,lb,lf,"D"); transition(c,le,err,"otro",label_offset=-12,dashed=True)
    for n in (l0,lb,le,lf,err): state(c,n)
    footer(c,"SAFE_D excluye el delimitador, la barra inversa y los saltos de línea.")


def diagram_5(c: Canvas) -> None:
    page_header(c,5,"AFD para comentarios","Ramas independientes para comentario de línea y comentario de bloque.")
    c0=Node("c0",95,300); cl=Node("cL",315,410,"COMENTARIO DE LÍNEA",True); cs=Node("c/",235,205); cb=Node("cB",420,205); ct=Node("c*",585,205); cf=Node("cF",740,205,"COMENTARIO DE BLOQUE",True)
    start_arrow(c,c0); transition(c,c0,cl,"%",radius=20); loop(c,cl,"excepto CR/LF",radius=20); transition(c,c0,cs,"/",radius=20,label_offset=-10); transition(c,cs,cb,"*",radius=20); loop(c,cb,"excepto *",radius=20,above=False); transition(c,cb,ct,"*",radius=20); loop(c,ct,"*",radius=20); transition(c,ct,cb,"excepto * y /",radius=20,label_offset=-12); transition(c,ct,cf,"/",radius=20)
    for n in (c0,cl,cs,cb,ct,cf): state(c,n,20)
    footer(c,"El fin de línea cierra la rama cL. Solo la secuencia `*/` cierra la rama de bloque.")


def small_node(c: Canvas, x: float, y: float, label: str, accepting: bool = False) -> None:
    c.setFillColor(PALE_BLUE if accepting else PAPER); c.setStrokeColor(NAVY); c.setLineWidth(0.9); c.circle(x,y,12,stroke=1,fill=1)
    if accepting: c.circle(x,y,9,stroke=1,fill=0)
    c.setFillColor(INK); c.setFont(BOLD,6.5); c.drawCentredString(x,y-2.3,label)


def trie_edge(c: Canvas, a: tuple[float,float], b: tuple[float,float], label: str) -> None:
    ax,ay=a; bx,by=b; dx,dy=bx-ax,by-ay; length=math.hypot(dx,dy); ux,uy=dx/length,dy/length
    x1,y1=ax+ux*12,ay+uy*12; x2,y2=bx-ux*12,by-uy*12
    c.setStrokeColor(MUTED); c.setLineWidth(0.75); c.line(x1,y1,x2,y2); arrow_head(c,x2,y2,math.atan2(dy,dx),4); label_box(c,(x1+x2)/2,(y1+y2)/2+7,label)


def trie_panel(
    c: Canvas,
    title: str,
    bottom: float,
    height: float,
    nodes: dict[str, tuple[float, float, bool]],
    edges: list[tuple[str, str, str]],
) -> None:
    c.setFillColor(SINK_FILL)
    c.roundRect(38, bottom, 765, height, 5, stroke=0, fill=1)
    c.setFillColor(MUTED)
    c.setFont(MONO, 6.5)
    c.drawString(48, bottom + height - 13, title)
    absolute = {key: (x, bottom + y) for key, (x, y, _) in nodes.items()}
    for source, target, label in edges:
        trie_edge(c, absolute[source], absolute[target], label)
    for key, (x, y, accepting) in nodes.items():
        small_node(c, x, bottom + y, key, accepting)


def diagram_6(c: Canvas) -> None:
    page_header(c,6,"Trie de operadores","Organización por prefijo para aplicar máxima coincidencia antes de emitir el token.")
    trie_panel(c,"OPERADORES DE UN CARÁCTER",420,70,
        {"o0":(75,30,False),",":(300,46,True),"OP1":(550,22,True)},
        [("o0",",",","),("o0","OP1","{+, !, ;, <}")])
    trie_panel(c,"PREFIJOS ARITMÉTICOS",320,88,
        {"o0":(75,37,False),"-":(235,62,True),"--":(400,62,False),"-->":(565,62,True),"*":(235,37,True),"**":(400,37,True),"/":(235,14,True),"//":(400,14,True)},
        [("o0","-","-"),("-","--","-"),("--","-->",">"),("o0","*","*"),("*","**","*"),("o0","/","/"),("/","//","/")])
    trie_panel(c,"COMPARACIÓN Y UNIFICACIÓN",188,120,
        {"o0":(75,50,False),"=":(210,88,True),"==":(365,102,True),"=.":(365,78,False),"=..":(520,78,True),"=<":(365,57,True),">":(210,42,True),">=":(365,40,True),"\\":(210,14,False),"\\=":(365,8,True),"\\==":(520,8,True),"\\+":(365,24,True)},
        [("o0","=","="),("=","==","="),("=","=.","."),("=.","=..","."),("=","=<","<"),("o0",">",">"),(">",">=","="),("o0","\\","\\"),("\\","\\=","="),("\\=","\\==","="),("\\","\\+","+")])
    trie_panel(c,"CLÁUSULAS Y PALABRAS RESERVADAS",68,108,
        {"o0":(75,43,False),":":(205,78,False),":-":(350,78,True),"?":(205,55,False),"?-":(350,55,True),"i":(205,32,False),"is":(350,32,True),"m":(205,9,False),"mo":(350,9,False),"mod":(500,9,True)},
        [("o0",":",":"), (":",":-","-"),("o0","?","?"),("?","?-","-"),("o0","i","i"),("i","is","s"),("o0","m","m"),("m","mo","o"),("mo","mod","d")])
    c.setFillColor(MUTED); c.setFont(REGULAR,7.2); c.drawRightString(795,52,"`is` y `mod` requieren frontera de palabra.")
    footer(c,"Vista compacta por familias de prefijos. Cada banda parte del estado inicial o0.")


def diagram_7(c: Canvas) -> None:
    page_header(c,7,"AFN representativo de operadores","Lenguaje restringido a {=, ==, \\=, \\==} para mostrar la construcción formal.")
    q0=Node("q0",100,290); q1=Node("q1",260,380); q2=Node("q2",445,380,"OP_EQ",True); q3=Node("q3",650,380,"OP_EQEQ",True); q4=Node("q4",260,190); q5=Node("q5",390,190); q6=Node("q6",535,190,"OP_NEQ",True); q7=Node("q7",700,190,"OP_NEQEQ",True)
    start_arrow(c,q0); transition(c,q0,q1,"eps",radius=20); transition(c,q0,q4,"eps",radius=20); transition(c,q1,q2,"=",radius=20); transition(c,q2,q3,"=",radius=20); transition(c,q4,q5,"\\",radius=20); transition(c,q5,q6,"=",radius=20); transition(c,q6,q7,"=",radius=20)
    for n in (q0,q1,q2,q3,q4,q5,q6,q7): state(c,n,20)
    footer(c,"Las transiciones eps separan las dos ramas del AFN sin consumir entrada.")


def appendix_overview(c: Canvas) -> None:
    """Página de orientación para leer el anexo antes de entrar en las figuras."""
    page_header(c, 0, "Anexo A · guía de lectura", "Secuencia de modelos que sostiene la especificación y la implementación del lexer.")
    c.setFillColor(DARK_BLUE if 'DARK_BLUE' in globals() else NAVY)
    c.setFont(BOLD, 13)
    c.drawString(52, 480, "Qué se modela")
    c.setFillColor(INK)
    c.setFont(REGULAR, 9)
    lines = [
        "Cada figura representa una decisión léxica concreta. Las cinco primeras",
        "describen categorías y elementos ignorables; la sexta integra el despacho",
        "por primera clase y máxima coincidencia; las dos últimas documentan la",
        "determinización y la minimización de un subconjunto de operadores.",
    ]
    for index, line in enumerate(lines):
        c.drawString(52, 458 - index * 15, line)

    c.setFillColor(DARK_BLUE if 'DARK_BLUE' in globals() else NAVY)
    c.setFont(BOLD, 13)
    c.drawString(52, 375, "Convenciones de lectura")
    conventions = [
        ("Estado", "círculo con nombre ASCII estable, por ejemplo n0 o q2"),
        ("Aceptación", "doble círculo; el rótulo inferior indica el token producido"),
        ("Transición", "flecha etiquetada con el símbolo o clase consumida"),
        ("Bucle", "transición que vuelve al mismo estado; la punta toca la circunferencia"),
        ("Sumidero", "estado gris para recorridos que no producen un token válido"),
    ]
    y = 350
    for label, description in conventions:
        c.setFillColor(BLUE)
        c.setFont(BOLD, 8.5)
        c.drawString(58, y, label.upper())
        c.setFillColor(INK)
        c.setFont(REGULAR, 8.5)
        c.drawString(165, y, description)
        y -= 24

    c.setFillColor(LIGHT_PANEL)
    c.roundRect(52, 108, 745, 104, 8, stroke=0, fill=1)
    c.setFillColor(DARK_BLUE if 'DARK_BLUE' in globals() else NAVY)
    c.setFont(BOLD, 11)
    c.drawString(70, 188, "Ruta de lectura recomendada")
    steps = [
        ("01", "Categorías", "átomos, variables, números, literales y comentarios"),
        ("02", "Operadores", "prefijos comunes, máxima coincidencia y prioridades"),
        ("03", "Construcción", "AFN, subconjuntos, estado sumidero y AFD mínimo"),
    ]
    x = 72
    for number, title, description in steps:
        c.setFillColor(YELLOW if 'YELLOW' in globals() else colors.HexColor("#FDC400"))
        c.circle(x + 10, 153, 13, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont(BOLD, 7)
        c.drawCentredString(x + 10, 150, number)
        c.setFillColor(DARK_BLUE if 'DARK_BLUE' in globals() else NAVY)
        c.setFont(BOLD, 8.5)
        c.drawString(x + 31, 157, title)
        c.setFillColor(MUTED)
        c.setFont(REGULAR, 7.3)
        c.drawString(x + 31, 144, description)
        x += 247
    footer(c, "Las figuras son vectoriales y mantienen la misma convención de estados, etiquetas y colores.")


def subset_diagram(c: Canvas, number: int, title: str, subtitle: str) -> None:
    page_header(c,number,title,subtitle)
    A=Node("A",105,320); B=Node("B",280,405,"OP_EQ",True); C=Node("C",475,405,"OP_EQEQ",True); D=Node("D",280,245); E=Node("E",475,245,"OP_NEQ",True); F=Node("F",660,245,"OP_NEQEQ",True); Z=Node("Z",660,105,sink=True)
    start_arrow(c,A); transition(c,A,B,"="); transition(c,A,D,"\\"); transition(c,B,C,"="); transition(c,D,E,"="); transition(c,E,F,"=")
    poly_transition(c,[(280,382),(280,130),(637,130)],"\\",315,141,True); poly_transition(c,[(475,382),(520,345),(637,128)],"=, \\",540,276,True); poly_transition(c,[(280,222),(280,105),(637,105)],"\\",350,116,True); poly_transition(c,[(475,222),(475,155),(641,120)],"\\",520,162,True); poly_transition(c,[(660,222),(660,128)],"=, \\",695,170,True); loop(c,Z,"=, \\",above=False)
    for n in (A,B,C,D,E,F,Z): state(c,n)
    c.setFillColor(MUTED); c.setFont(REGULAR,7.2); c.drawString(46,54,"Las líneas discontinuas llevan al sumidero Z; las rutas válidas permanecen en la zona superior."); footer(c)


def build(output: Path) -> None:
    output.parent.mkdir(parents=True,exist_ok=True)
    c=Canvas(str(output),pagesize=landscape(A4),pageCompression=1); c.setTitle("Anexo de autómatas - analizador léxico de Prolog"); c.setAuthor("Fernando Valdés, Juan Muñoz y Vicente Rivera")
    appendix_overview(c); c.showPage()
    for draw in (diagram_1,diagram_2,diagram_3,diagram_4,diagram_5,diagram_6,diagram_7): draw(c); c.showPage()
    subset_diagram(c,8,"AFD obtenido por construcción de subconjuntos","Cada estado representa un conjunto de estados del AFN; las salidas conservan la clasificación léxica."); c.showPage()
    subset_diagram(c,9,"AFD mínimo etiquetado","La partición estable separa A, D y Z y conserva cuatro clases de aceptación observables."); c.showPage(); c.save()


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("-o","--output",type=Path,default=DEFAULT_OUTPUT); args=parser.parse_args(); build(args.output); print(f"PDF vectorial de diagramas generado: {args.output}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Convierte las diapositivas HTML de la presentación en frames de Beamer.

Lee fuente_html/deck.json y fuente_html/slides/<id>.html y escribe
diapositivas.tex y colores.tex, que presentacion.tex incluye.

Uso, desde la carpeta presentacion_latex/:
    python3 herramientas/html_a_beamer.py

Las diapositivas HTML están en un lienzo de 1920 × 1080 px con estilos en
línea. Aquí cada px se pasa a puntos de una página Beamer 16:9 (160 × 90 mm),
cada caja con fondo pasa a un tcolorbox, cada fila flex a una fila de
minipages y cada <aside> a una nota del orador.
"""
import json
import re
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = RAIZ / "fuente_html"

PT = 455.24 / 1920        # puntos por px: 160 mm de ancho son 455,24 pt
ANCHO = 1664              # px útiles entre los márgenes de 128 px
TAM_DEF = {"p": 32, "li": 32, "h1": 96, "h2": 64, "h3": 44}
INTERLINEA_DEF = {"p": 1.4, "li": 1.4, "h1": 1.1, "h2": 1.15, "h3": 1.2}
VACIOS = {"br", "hr", "img", "x-icon", "x-shape", "x-connector"}

colores = set()
grupos = [0]


# --- Lectura del HTML ---------------------------------------------------------

class Nodo:
    def __init__(self, tag, attrs):
        self.tag = tag
        self.attrs = dict(attrs)
        self.hijos = []
        self.estilo = leer_estilo(self.attrs.get("style", ""))


class Texto:
    tag = "#texto"

    def __init__(self, texto):
        self.texto = texto


class Lector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.raiz = Nodo("raiz", [])
        self.pila = [self.raiz]

    def handle_starttag(self, tag, attrs):
        nodo = Nodo(tag, attrs)
        self.pila[-1].hijos.append(nodo)
        if tag not in VACIOS:
            self.pila.append(nodo)

    def handle_startendtag(self, tag, attrs):
        self.pila[-1].hijos.append(Nodo(tag, attrs))

    def handle_endtag(self, tag):
        if tag in VACIOS:
            return
        for i in range(len(self.pila) - 1, 0, -1):
            if self.pila[i].tag == tag:
                del self.pila[i:]
                return

    def handle_data(self, datos):
        self.pila[-1].hijos.append(Texto(datos))


def leer_estilo(texto):
    estilo = {}
    for parte in texto.split(";"):
        if ":" in parte:
            clave, valor = parte.split(":", 1)
            estilo[clave.strip()] = valor.strip()
    return estilo


def elementos(nodo):
    return [h for h in nodo.hijos if isinstance(h, Nodo)]


def flujo(nodo):
    """Hijos que ocupan sitio: fuera notas y elementos fijados al lienzo."""
    return [h for h in elementos(nodo)
            if h.tag != "aside" and h.estilo.get("position") != "absolute"]


def texto_plano(nodo):
    if isinstance(nodo, Texto):
        return nodo.texto
    return "".join(texto_plano(h) for h in nodo.hijos)


# --- Unidades y colores -------------------------------------------------------

def px(valor):
    m = re.match(r"(-?[\d.]+)(px)?$", valor.strip()) if valor else None
    return float(m.group(1)) if m else None


def lista_px(valor):
    return [float(v) for v in re.findall(r"-?[\d.]+", valor or "")]


def relleno(estilo):
    v = lista_px(estilo.get("padding", "0"))
    if not v:
        v = [0]
    if len(v) == 1:
        v = v * 4
    elif len(v) == 2:
        v = [v[0], v[1], v[0], v[1]]
    elif len(v) == 3:
        v = [v[0], v[1], v[2], v[1]]
    return v  # arriba, derecha, abajo, izquierda


def color(valor):
    m = re.search(r"#([0-9a-fA-F]{6})", valor or "")
    if not m:
        return None
    nombre = "c" + m.group(1).upper()
    colores.add(m.group(1).upper())
    return nombre


def borde(estilo):
    m = re.match(r"(\d+)px solid (#[0-9a-fA-F]{6})", estilo.get("border", ""))
    return (float(m.group(1)), color(m.group(2))) if m else None


def pt(valor_px):
    return f"{valor_px * PT:.2f}pt"


# --- Texto --------------------------------------------------------------------

ESCAPES = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
           "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "\xa0": "~"}


def escapar(texto):
    return "".join(ESCAPES.get(c, c) for c in texto)


def colapsar(texto):
    return re.sub(r"[ \t\r\n]+", " ", texto)


def fuente(tam_px, interlinea):
    return rf"\fontsize{{{tam_px * PT:.2f}}}{{{tam_px * PT * interlinea:.2f}}}\selectfont"


def en_linea(nodo, ctx):
    partes = []
    for h in nodo.hijos:
        if isinstance(h, Texto):
            partes.append(escapar(colapsar(h.texto)))
        elif h.tag == "br":
            partes.append(r"\newline ")
        elif h.tag in ("b", "strong"):
            partes.append(r"\textbf{" + en_linea(h, ctx) + "}")
        elif h.tag in ("i", "em"):
            partes.append(r"\textit{" + en_linea(h, ctx) + "}")
        elif h.tag == "u":
            partes.append(r"\underline{" + en_linea(h, ctx) + "}")
        elif h.tag == "a":
            url = h.attrs.get("href", "").replace("%", r"\%").replace("#", r"\#")
            visible = texto_plano(h).strip()
            if "/" in visible and " " not in visible:
                cuerpo = escapar(visible).replace("/", r"/\allowbreak{}")
            else:
                cuerpo = en_linea(h, ctx)
            partes.append(rf"\href{{{url}}}{{\textcolor{{c1F5FAE}}{{{cuerpo}}}}}")
            colores.add("1F5FAE")
        elif h.tag == "span":
            s = en_linea(h, ctx)
            if "Mono" in h.estilo.get("font-family", ""):
                s = r"\texttt{" + s + "}"
            c = color(h.estilo.get("color"))
            if c:
                s = rf"\textcolor{{{c}}}{{{s}}}"
            partes.append(s)
        elif h.tag == "x-icon":
            partes.append(icono(h, ctx))
        else:
            partes.append(en_linea(h, ctx))
    return "".join(partes)


def heredar(ctx, estilo):
    nuevo = dict(ctx)
    if "color" in estilo and color(estilo["color"]):
        nuevo["color"] = color(estilo["color"])
    if "font-size" in estilo:
        nuevo["tam"] = px(estilo["font-size"])
    if "font-family" in estilo:
        nuevo["mono"] = "Mono" in estilo["font-family"]
    if "line-height" in estilo and re.match(r"[\d.]+$", estilo["line-height"]):
        nuevo["interlinea"] = float(estilo["line-height"])
    return nuevo


def formato_texto(nodo, ctx):
    """Tamaño, interlínea, negrita y familia de un bloque de texto."""
    e = nodo.estilo
    tag = nodo.tag
    if "font-size" in e:
        tam = px(e["font-size"])
    elif tag in ("h1", "h2", "h3"):
        tam = TAM_DEF[tag]
    else:
        tam = ctx["tam"]
    if "line-height" in e and re.match(r"[\d.]+$", e["line-height"]):
        inter = float(e["line-height"])
    elif tag in INTERLINEA_DEF and tag != "li":
        inter = INTERLINEA_DEF[tag]
    else:
        inter = ctx["interlinea"]
    peso = e.get("font-weight")
    negrita = (int(peso) >= 600 if peso.isdigit() else peso == "bold") if peso else tag in ("h1", "h2", "h3")
    mono = "Mono" in e["font-family"] if "font-family" in e else ctx["mono"]
    c = color(e.get("color")) or ctx["color"]
    orden = fuente(tam, inter)
    if negrita:
        orden += r"\bfseries"
    if mono:
        orden += r"\ttfamily"
    if e.get("font-style") == "italic":
        orden += r"\itshape"
    return orden + rf"\color{{{c}}}"


# --- Bloques ------------------------------------------------------------------

def bloque(nodo, ancho, ctx, grupo=None, id_diapo=""):
    if nodo.tag == "aside" or nodo.estilo.get("position") == "absolute":
        return ""
    if nodo.tag in ("p", "h1", "h2", "h3"):
        return parrafo(nodo, ancho, ctx, grupo)
    if nodo.tag in ("ul", "ol"):
        return lista(nodo, ancho, ctx)
    if nodo.tag == "table":
        return tabla(nodo, ancho, ctx)
    if nodo.tag == "svg":
        return grafica(nodo, ancho, ctx)
    if nodo.tag == "x-shape":
        return flecha(nodo)
    if nodo.tag == "x-icon":
        return icono(nodo, ctx)
    if nodo.tag == "div":
        return division(nodo, ancho, ctx, grupo)
    return ""


def alineacion(estilo):
    return {"center": r"\centering", "right": r"\raggedleft"}.get(
        estilo.get("text-align"), r"\raggedright")


def parrafo(nodo, ancho, ctx, grupo=None):
    e = nodo.estilo
    texto = en_linea(nodo, heredar(ctx, e)).strip()
    if e.get("text-transform") == "uppercase":
        texto = r"\MakeUppercase{" + texto + "}"
    cuerpo = "{" + formato_texto(nodo, ctx) + alineacion(e) + " " + texto + r"\par}"
    propio = px(e.get("width", "")) or ancho
    if es_caja(e):
        return caja(e, propio, cuerpo, grupo)
    if propio < ancho - 1:
        return rf"\begin{{minipage}}[t]{{{pt(propio)}}}{cuerpo}\end{{minipage}}\par"
    return cuerpo


def es_caja(estilo):
    return bool(color(estilo.get("background")) or borde(estilo))


def caja(estilo, ancho, contenido, grupo=None):
    fondo = color(estilo.get("background"))
    b = borde(estilo)
    arriba, derecha, abajo, izquierda = relleno(estilo)
    radio = (lista_px(estilo.get("border-radius", "0")) or [0])[0]
    radio = min(radio, 60)
    opciones = [f"width={pt(ancho)}", "boxsep=0pt",
                f"left={pt(izquierda)}", f"right={pt(derecha)}",
                f"top={pt(arriba)}", f"bottom={pt(abajo)}",
                f"arc={pt(radio)}" if radio else "sharp corners",
                f"boxrule={pt(b[0]) if b else '0pt'}",
                f"colback={fondo or 'white'}", f"colframe={b[1] if b else (fondo or 'white')}",
                "before skip=0pt", "after skip=0pt", "nobeforeafter"]
    if not fondo:
        opciones.append("opacityback=0")
    alto = px(estilo.get("height", ""))
    if alto:
        opciones += [f"height={pt(alto)}"]
    if alto or grupo:
        if estilo.get("align-items") == "center" or estilo.get("justify-content") == "center" or alto:
            opciones.append("valign=center")
    if estilo.get("justify-content") == "center" and estilo.get("display") == "flex" \
            and estilo.get("flex-direction", "row") == "row":
        opciones.append("halign=center")
    if grupo:
        opciones.append(f"equal height group={grupo}")
    return r"\begin{tcolorbox}[" + ",".join(opciones) + "]" + contenido + r"\end{tcolorbox}"


def es_barra(nodo):
    e = nodo.estilo
    return nodo.tag == "div" and not flujo(nodo) and color(e.get("background")) and px(e.get("height", ""))


def barra(nodo, ancho):
    e = nodo.estilo
    fondo = color(e.get("background"))
    alto = px(e["height"])
    b = borde(e)
    if b:
        return (r"{\setlength\fboxsep{0pt}\setlength\fboxrule{" + pt(b[0]) + "}"
                rf"\fcolorbox{{{b[1]}}}{{{fondo}}}{{\rule{{0pt}}{{{pt(alto - 2 * b[0])}}}\rule{{{pt(ancho - 2 * b[0])}}}{{0pt}}}}}}")
    return rf"\textcolor{{{fondo}}}{{\rule{{{pt(ancho)}}}{{{pt(alto)}}}}}"


def es_pista(nodo):
    """Una barra de fondo (el 100 %) con barras dentro (la parte llena)."""
    hijos = flujo(nodo)
    e = nodo.estilo
    return (hijos and color(e.get("background")) and px(e.get("width", "")) and px(e.get("height", ""))
            and all(es_barra(h) for h in hijos))


def pista(nodo):
    e = nodo.estilo
    ancho, alto = px(e["width"]), px(e["height"])
    lleno = "".join(barra(h, px(h.estilo.get("width", "0")) or 0) for h in flujo(nodo))
    return (rf"\makebox[{pt(ancho)}][l]{{\makebox[0pt][l]{{\textcolor{{{color(e['background'])}}}"
            rf"{{\rule{{{pt(ancho)}}}{{{pt(alto)}}}}}}}{lleno}}}")


def division(nodo, ancho, ctx, grupo=None):
    e = nodo.estilo
    c = heredar(ctx, e)
    if es_barra(nodo):
        return barra(nodo, px(e.get("width", "")) or ancho) + r"\par"
    if es_pista(nodo):
        return pista(nodo) + r"\par"
    propio = px(e.get("width", "")) or ancho
    hay_caja = es_caja(e)
    interior = propio
    if hay_caja:
        arriba, derecha, abajo, izquierda = relleno(e)
        b = borde(e)
        interior = propio - izquierda - derecha - (2 * b[0] if b else 0)
    hijos = flujo(nodo)
    pantalla = e.get("display")
    direccion = e.get("flex-direction", "row" if pantalla == "flex" else "column")
    if pantalla == "grid":
        contenido = rejilla(hijos, interior, e, c)
    elif pantalla == "flex" and direccion == "row":
        contenido = fila(hijos, interior, e, c)
    else:
        contenido = columna(hijos, interior, e, c)
    if hay_caja:
        return caja(e, propio, contenido, grupo)
    if propio < ancho - 1:
        return rf"\begin{{minipage}}[t]{{{pt(propio)}}}{contenido}\end{{minipage}}\par"
    return contenido


def huecos(estilo):
    v = lista_px(estilo.get("gap", "0")) or [0]
    return v[0], (v[1] if len(v) > 1 else v[0])  # entre filas, entre columnas


def columna(hijos, ancho, estilo, ctx):
    hueco_fila, _ = huecos(estilo)
    partes = [p for p in (bloque(h, ancho, ctx) for h in hijos) if p]
    return (r"\par\vspace{" + pt(hueco_fila) + "}").join(partes)


def ancho_propio(nodo):
    return px(nodo.estilo.get("width", "")) if "%" not in nodo.estilo.get("width", "") else None


def es_flexible(nodo):
    return nodo.estilo.get("flex", "").startswith("1")


def estimar(nodo):
    """Ancho natural en px, si se puede saber sin componer el texto."""
    w = ancho_propio(nodo)
    if w:
        return w
    if nodo.tag != "div":
        return None
    hijos = flujo(nodo)
    if not hijos:
        return None
    medidas = [estimar(h) for h in hijos]
    e = nodo.estilo
    if e.get("display") == "flex" and e.get("flex-direction", "row") == "row":
        if None in medidas:
            return None
        return sum(medidas) + huecos(e)[1] * (len(medidas) - 1)
    # En una columna, el texto sin ancho se adapta al hijo más ancho
    conocidas = [m for m in medidas if m is not None]
    return max(conocidas) if conocidas else None


def natural(nodo, ctx):
    """Un elemento de fila sin ancho: se compone con su ancho natural."""
    if nodo.tag in ("p", "h3"):
        lineas = []
        actual = Nodo("p", [])
        for h in nodo.hijos:
            if isinstance(h, Nodo) and h.tag == "br":
                lineas.append(actual)
                actual = Nodo("p", [])
            else:
                actual.hijos.append(h)
        lineas.append(actual)
        c = heredar(ctx, nodo.estilo)
        textos = [en_linea(l, c).strip() for l in lineas]
        if nodo.estilo.get("text-transform") == "uppercase":
            textos = [r"\MakeUppercase{" + t + "}" for t in textos]
        formato = formato_texto(nodo, ctx)
        if len(textos) == 1:
            return "{" + formato + r"\mbox{" + textos[0] + "}}"
        return "{" + formato + r"\begin{tabular}[c]{@{}l@{}}" + r"\\".join(textos) + r"\end{tabular}}"
    if nodo.tag == "x-icon":
        return icono(nodo, ctx)
    if nodo.tag == "div":
        e = nodo.estilo
        c = heredar(ctx, e)
        hijos = flujo(nodo)
        if e.get("display") == "flex" and e.get("flex-direction", "row") == "row":
            sep = r"\hspace{" + pt(huecos(e)[1]) + "}"
            return r"\mbox{" + sep.join(
                barra(h, px(h.estilo["width"])) if es_barra(h) else natural(h, c) for h in hijos) + "}"
        return r"\begin{tabular}[c]{@{}l@{}}" + r"\\".join(natural(h, c) for h in hijos) + r"\end{tabular}"
    return ""


def fila(hijos, ancho, estilo, ctx, anchos=None):
    _, hueco = huecos(estilo)
    reparto = estilo.get("justify-content", "start")
    alinear = estilo.get("align-items", "stretch")
    pos = {"center": "c", "end": "b"}.get(alinear, "t")
    if anchos is None:
        fijos, flexibles, anchos = 0, 0, []
        for h in hijos:
            w = ancho_propio(h)
            if w is None and es_flexible(h):
                flexibles += 1
                anchos.append("flex")
            elif w is not None:
                fijos += w
                anchos.append(w)
            else:
                est = estimar(h)
                fijos += est or 0
                anchos.append(est)
        libre = ancho - fijos - hueco * (len(hijos) - 1)
        anchos = [libre / flexibles if a == "flex" else a for a in anchos]
    grupo = None
    if alinear == "stretch" and sum(1 for h in hijos if es_caja(h.estilo)) > 1:
        grupos[0] += 1
        grupo = f"g{grupos[0]}"
    partes = []
    for h, w in zip(hijos, anchos):
        if es_barra(h):
            partes.append(barra(h, w))
        elif es_pista(h):
            partes.append(pista(h))
        elif w is None:
            partes.append(natural(h, ctx))
        elif h.tag in ("x-shape", "x-icon"):
            partes.append(bloque(h, w, ctx))
        else:
            arranque = r"\vspace{0pt}" if pos == "t" else ""
            partes.append(rf"\begin{{minipage}}[{pos}]{{{pt(w)}}}{arranque}"
                          + bloque(h, w, ctx, grupo if es_caja(h.estilo) else None)
                          + r"\end{minipage}")
    if reparto == "space-between":
        cuerpo = r"\hfill".join(partes)
    else:
        cuerpo = (r"\hspace{" + pt(hueco) + "}").join(partes)
        if reparto == "center":
            cuerpo = r"\hfil" + cuerpo + r"\hfil"
        elif reparto == "end":
            cuerpo = r"\hfil" + cuerpo
        else:
            cuerpo += r"\hfil"
    return r"\noindent\hbox to\linewidth{" + cuerpo + r"}\par"


def rejilla(hijos, ancho, estilo, ctx):
    pistas = estilo.get("grid-template-columns", "1fr").split()
    hueco_fila, hueco_col = huecos(estilo)
    fijos = sum(px(p) or 0 for p in pistas if p.endswith("px"))
    fracciones = sum(float(p[:-2]) for p in pistas if p.endswith("fr"))
    libre = ancho - fijos - hueco_col * (len(pistas) - 1)
    anchos = [px(p) if p.endswith("px") else float(p[:-2]) * libre / fracciones for p in pistas]
    estilo_fila = dict(estilo, gap=f"{hueco_col}px")
    filas = []
    for i in range(0, len(hijos), len(pistas)):
        trozo = hijos[i:i + len(pistas)]
        filas.append(fila(trozo, ancho, estilo_fila, ctx, anchos[:len(trozo)]))
    return (r"\vspace{" + pt(hueco_fila) + "}").join(filas)


def lista(nodo, ancho, ctx):
    e = nodo.estilo
    c = heredar(ctx, e)
    sangria = (relleno(e)[3] or 40) * PT
    entorno = "itemize" if nodo.tag == "ul" else "enumerate"
    elementos_lista = [r"\item " + en_linea(li, c).strip() for li in elementos(nodo) if li.tag == "li"]
    formato = fuente(c["tam"], c["interlinea"]) + rf"\color{{{c['color']}}}"
    return ("{" + formato + rf"\setlength{{\leftmargini}}{{{sangria:.2f}pt}}\begin{{{entorno}}}"
            r"\setlength{\itemsep}{0.25em}" + "".join(elementos_lista) + rf"\end{{{entorno}}}\par}}")


def tabla(nodo, ancho, ctx):
    e = nodo.estilo
    c = heredar(ctx, e)
    total = ancho_propio(nodo) or ancho
    filas = [tr for tr in elementos(nodo) if tr.tag == "tr"]
    primera = elementos(filas[0])
    porcentajes = []
    for celda in primera:
        m = re.match(r"([\d.]+)%", celda.estilo.get("width", ""))
        porcentajes.append(float(m.group(1)) if m else None)
    if None in porcentajes:
        porcentajes = [100 / len(primera)] * len(primera)
    separacion = 0.6 * c["tam"]
    columnas = []
    for celda, porc in zip(primera, porcentajes):
        w = total * porc / 100 - 2 * separacion
        alin = {"right": r"\raggedleft", "center": r"\centering"}.get(
            celda.estilo.get("text-align"), r"\raggedright")
        columnas.append(rf">{{{alin}\arraybackslash}}p{{{pt(w)}}}")
    lineas = []
    for tr in filas:
        prefijo = ""
        fondo = color(tr.estilo.get("background"))
        if fondo:
            prefijo = rf"\rowcolor{{{fondo}}}"
        celdas = []
        for celda in elementos(tr):
            texto = en_linea(celda, heredar(c, celda.estilo)).strip()
            if celda.tag == "th":
                texto = r"\textbf{" + texto + "}" if texto else ""
            cc = color(celda.estilo.get("color"))
            if cc and texto:
                texto = rf"\textcolor{{{cc}}}{{{texto}}}"
            celdas.append(texto)
        lineas.append(prefijo + " & ".join(celdas) + r"\\\hline" + "\n")
    formato = fuente(c["tam"], 1.25) + rf"\color{{{c['color']}}}"
    colores.add("E2DCCB")
    return ("{" + formato + rf"\setlength{{\tabcolsep}}{{{separacion * PT:.2f}pt}}"
            r"\renewcommand{\arraystretch}{1.45}\arrayrulecolor{cE2DCCB}\noindent"
            r"\begin{tabular}{" + "".join(columnas) + "}" + "".join(lineas) + r"\end{tabular}\par}")


def flecha(nodo):
    e = nodo.estilo
    w, h = px(e.get("width", "120")) * PT, px(e.get("height", "60")) * PT
    c = color(e.get("background")) or "c14213D"
    return (rf"\tikz[baseline={{(0,{h / 2:.2f}pt)}}]\fill[{c}] (0,{0.25 * h:.2f}pt)--({0.6 * w:.2f}pt,{0.25 * h:.2f}pt)"
            rf"--({0.6 * w:.2f}pt,0)--({w:.2f}pt,{h / 2:.2f}pt)--({0.6 * w:.2f}pt,{h:.2f}pt)"
            rf"--({0.6 * w:.2f}pt,{0.75 * h:.2f}pt)--(0,{0.75 * h:.2f}pt)--cycle;")


def icono(nodo, ctx):
    e = nodo.estilo
    alto = px(e.get("height", "40")) or 40
    c = color(e.get("color")) or ctx["color"]
    if nodo.attrs.get("name") == "Check":
        return rf"\textcolor{{{c}}}{{\resizebox{{!}}{{{pt(alto * 0.75)}}}{{$\checkmark$}}}}"
    return ""


# --- Gráfica de líneas (la única que en HTML era un SVG) ---------------------

HILOS = [1, 3, 6, 9, 12, 18, 24, 30, 36]
CURVAS = [
    {   # n = 1, u = 1 %
        "ymax": 100, "yticks": "0,50,100",
        "series": {
            "Libstdc++": [58.47, 7.34, 3.12, 2.29, 1.69, 1.36, 1.19, 1.0, 0.87],
            "Williams": [27.93, 6.92, 6.94, 6.81, 6.41, 5.42, 4.83, 4.84, 4.79],
            "Folly": [80.86, 13.69, 12.56, 13.12, 12.36, 10.25, 9.11, 9.24, 9.34],
            "Anderson": [80.3, 20.62, 19.98, 20.81, 21.56, 20.02, 18.64, 18.64, 17.1],
            "Autores": [94.22, 23.71, 19.58, 19.78, 19.44, 21.38, 19.81, 19.81, 19.95]},
        "notas": [(25, 95, "c5F6B7A", "24 hilos = toda la máquina"),
                  (5, 70, "cB04A06", "Autores: de 94 a 24 Mop/s\\\\al pasar de 1 a 3 hilos")]},
    {   # n = 10⁶, u = 50 %
        "ymax": 60, "yticks": "0,30,60",
        "series": {
            "Libstdc++": [4.7, 13.66, 25.89, 36.66, 43.92, 53.88, 56.34, 56.13, 56.26],
            "Williams": [2.28, 6.75, 13.14, 19.31, 24.89, 35.3, 40.39, 41.07, 41.35],
            "Folly": [4.23, 12.4, 23.77, 33.37, 41.25, 51.62, 53.39, 53.52, 54.89],
            "Anderson": [4.79, 13.67, 26.11, 36.54, 43.93, 55.27, 56.5, 57.05, 56.83],
            "Autores": [3.27, 9.91, 19.23, 27.84, 35.55, 47.12, 55.37, 56.29, 56.12]},
        "notas": [(20, 18, "c3D4A5C", "Cuatro algoritmos se juntan\\\\en 53-57 Mop/s")]},
]
COLOR_SERIE = {"Libstdc++": "cC2477D", "Williams": "c6250D6", "Folly": "c12907F",
               "Anderson": "c2A78D6", "Autores": "cD9620B"}
svg_vistos = [0]


def grafica(nodo, ancho, ctx):
    datos = CURVAS[svg_vistos[0] % len(CURVAS)]
    svg_vistos[0] += 1
    for c in list(COLOR_SERIE.values()) + ["c5F6B7A", "cB04A06", "c3D4A5C", "cE2DCCB"]:
        colores.add(c[1:])
    letra = fuente(24, 1.2)
    lineas = [r"\begin{tikzpicture}\begin{axis}[scale only axis, width=" + pt(700) + ", height=" + pt(380)
              + f", xmin=0, xmax=36, ymin=0, ymax={datos['ymax']}, xtick={{1,12,24,36}}, ytick={{{datos['yticks']}}},"
              r" axis line style={draw=none}, tick style={draw=none}, ymajorgrids, grid style={cE2DCCB, line width=0.5pt},"
              r" tick label style={font=" + letra + r", color=c5F6B7A}, clip=false]"]
    for nombre, valores in datos["series"].items():
        puntos = " ".join(f"({t},{v})" for t, v in zip(HILOS, valores))
        c = COLOR_SERIE[nombre]
        lineas.append(rf"\addplot[color={c}, line width=1pt, mark=*, mark size=1.1pt, mark options={{fill={c}, draw={c}, solid}}] coordinates {{{puntos}}};")
    lineas.append(rf"\draw[c5F6B7A, dashed, line width=0.5pt] (axis cs:24,0) -- (axis cs:24,{datos['ymax']});")
    for x, y, c, texto in datos["notas"]:
        lineas.append(rf"\node[anchor=north west, align=left, font={letra}, text={c}] at (axis cs:{x},{y}) {{{texto}}};")
    lineas.append(r"\end{axis}\end{tikzpicture}")
    colores.add("F7F4EC")
    return "\n".join(lineas) + r"\par"


# --- Diapositivas -------------------------------------------------------------

def nota(aside):
    if aside is None:
        return ""
    parrafos = [escapar(colapsar(l)).strip() for l in texto_plano(aside).split("\n")]
    return r"\par ".join(p for p in parrafos if p)


def diapositiva(id_diapo, html):
    lector = Lector()
    lector.feed(html)
    seccion = next(h for h in elementos(lector.raiz) if h.tag == "section")
    e = seccion.estilo
    fondo = color(e.get("background")) or "cF7F4EC"
    oscuro = fondo in ("c14213D",)
    ctx = {"tam": 32, "interlinea": 1.4, "mono": False,
           "color": color(e.get("color")) or "c14213D"}
    hijos = flujo(seccion)
    pie = next((h for h in elementos(seccion) if h.tag == "p"
                and h.estilo.get("position") == "absolute" and "bottom" in h.estilo), None)
    aside = next((h for h in elementos(seccion) if h.tag == "aside"), None)
    titulo_nodo = next((h for h in hijos if h.tag in ("h1", "h2")), None)
    titulo = escapar(colapsar(texto_plano(titulo_nodo)).strip()) if titulo_nodo else ""
    reparto = e.get("justify-content")
    cuerpo = columna(hijos, ANCHO, e, ctx)
    if reparto == "space-between":
        hueco = huecos(e)[0]
        partes = [p for p in (bloque(h, ANCHO, ctx) for h in hijos) if p]
        cuerpo = (r"\par\vspace{" + pt(hueco) + r"}\vfill ").join(partes)
        modo = "s"
    else:
        modo = "c" if reparto == "center" else "t"
    texto_pie = en_linea(pie, ctx).strip() if pie else ""
    color_pie = "cC9D3E3" if oscuro else ("c14213D" if fondo == "cD9620B" else "c5F6B7A")
    colores.update({"C9D3E3", "5F6B7A", "14213D"})
    partes = [f"% --- {id_diapo} ---",
              r"{\fondo{" + fondo + r"}\renewcommand\colorpie{" + color_pie + "}"
              r"\renewcommand\piediapo{" + texto_pie + "}"
              r"\renewcommand\titulonota{" + titulo + "}",
              r"\begin{frame}[plain]",
              r"\colocar{" + modo + "}{" + cuerpo + "}",
              r"\note{" + nota(aside) + "}",
              r"\end{frame}}"]
    codigo = "\n".join(partes) + "\n"
    if "hidden" in seccion.attrs:
        # Oculta al presentar: solo va en la versión con notas, sin contar en la numeración
        codigo = codigo.replace(r"\begin{frame}[plain]", r"\begin{frame}[plain,noframenumbering]")
        codigo = "\\ifnum\\connotas=1\n" + codigo + "\\fi\n"
    return codigo, len(texto_plano(aside)) if aside else 0


FIGURAS = [
    ("topologia.png", "Latencia entre cada par de núcleos", "5.2"),
    ("fig5_replica.png", "Rendimiento de las 5 implementaciones en los 6 escenarios", "6.1"),
    ("fig5_paper_frente_a_replica.png", "Cuánto rinde cada rival respecto a Autores, en el paper y en la réplica", "6.1"),
    ("memoria_ram.png", "Tráfico real de RAM", "6.1"),
    ("fig6_replica.png", "Latencia de cada operación con y sin contención", "6.2"),
    ("nativo_oficial_fig6.png", "Latencia sin Docker con los programas oficiales", "6.2"),
    ("memoria_retenida.png", "Pico de bloques de memoria vivos", "6.3"),
    ("nativo_oficial_memoria_retenida.png", "Pico de bloques de memoria vivos, sin Docker", "6.3"),
    ("afinidad_dosis_respuesta.png", "Rendimiento con 4 hilos a distancia creciente", "6.4"),
    ("afinidad_mapa_4hilos.png", "Cambio de rendimiento al separar 4 hilos", "6.4"),
    ("nativo_oficial_dosis_respuesta.png", "Rendimiento con 4 hilos a distancia creciente, sin Docker y con los programas oficiales", "6.4"),
    ("afinidad_mapa_8hilos.png", "Cambio de rendimiento al separar 8 hilos", "6.4"),
    ("miniatura_frente_a_paper.png", "Paper y réplica según el porcentaje de núcleos en uso", "6.4"),
    ("docker_frente_a_nativo_oficial.png", "Cada punto de la figura 5 con los programas oficiales, con Docker y sin Docker", "6.6"),
    ("nativo_oficial_fig5.png", "Rendimiento sin Docker con los programas oficiales", "6.6"),
    ("nativo_fig5.png", "Rendimiento sin Docker con bench.cpp del equipo", "6.6"),
    ("nativo_alineado_fig5.png", "Rendimiento sin Docker con bench.cpp y las pilas alineadas", "6.6"),
    ("docker_frente_a_nativo.png", "Cada punto de la figura 5, con Docker y sin Docker", "6.6"),
    ("nativo_dosis_respuesta.png", "Rendimiento con 4 hilos, de más cerca a más lejos, sin Docker", "6.6"),
    ("nativo_fig6.png", "Latencia sin Docker con bench.cpp del equipo", "6.6"),
]


def anexo():
    salida = [r"\section{Anexo: figuras originales}"]
    for i, (archivo, titulo, parte) in enumerate(FIGURAS, 1):
        cuerpo = (r"{\fontsize{5.69}{7}\selectfont\bfseries\color{cB04A06}\MakeUppercase{Anexo · figura "
                  + f"{i} de {len(FIGURAS)}" + r"}\par}\vspace{6pt}"
                  r"{\fontsize{11.4}{13.1}\selectfont\bfseries\color{c14213D}\raggedright " + escapar(titulo) + r"\par}"
                  r"\vspace{8pt}{\centering\includegraphics[width=\anchodisponible,height=148pt,keepaspectratio]{figuras/"
                  + archivo + r"}\par}")
        pie = (r"\texttt{figuras/" + escapar(archivo) + r"} · generada por analizar.py · se explica en EXPLICACION.md, Parte "
               + parte)
        texto_nota = ("Figura original de la réplica, tal como la genera analizar.py a partir de los CSV de "
                      f"resultados/david-ultra9-285/. Se explica en la Parte {parte} de EXPLICACION.md, donde viene "
                      "también cómo leerla. Úsenla de respaldo en el turno de preguntas.")
        salida.append(r"{\fondo{cF7F4EC}\renewcommand\colorpie{c5F6B7A}\renewcommand\piediapo{" + pie + "}"
                      r"\renewcommand\titulonota{" + escapar(titulo) + "}"
                      "\n" r"\begin{frame}[plain]" "\n" r"\colocar{t}{" + cuerpo + "}\n"
                      r"\note{" + texto_nota + "}\n" r"\end{frame}}" "\n")
    colores.update({"B04A06", "14213D", "F7F4EC", "5F6B7A"})
    return "\n".join(salida)


def titulo_seccion(seccion, html_inicio, id_inicio):
    if id_inicio.startswith("div-"):
        lector = Lector()
        lector.feed(html_inicio)
        h1 = next(h for h in _todos(lector.raiz) if h.tag == "h1")
        return colapsar(texto_plano(h1)).strip()
    return seccion["description"].split(":")[0]


def _todos(nodo):
    for h in elementos(nodo):
        yield h
        yield from _todos(h)


def main():
    indice = json.loads((FUENTE / "deck.json").read_text(encoding="utf-8"))
    inicios = {s["start"]: s for s in indice["sections"].values()}
    salida = ["% Generado por herramientas/html_a_beamer.py a partir de fuente_html/. No editar a mano.\n"]
    notas_largas = []
    for id_diapo in indice["order"]:
        html = (FUENTE / "slides" / f"{id_diapo}.html").read_text(encoding="utf-8")
        if id_diapo in inicios:
            salida.append(r"\section{" + escapar(titulo_seccion(inicios[id_diapo], html, id_diapo)) + "}\n")
        codigo, largo = diapositiva(id_diapo, html)
        salida.append(codigo)
        notas_largas.append((largo, id_diapo))
    salida.append(anexo())
    (RAIZ / "diapositivas.tex").write_text("\n".join(salida), encoding="utf-8")
    definiciones = [rf"\definecolor{{c{h}}}{{HTML}}{{{h}}}" for h in sorted(colores)]
    (RAIZ / "colores.tex").write_text("% Generado por herramientas/html_a_beamer.py\n" + "\n".join(definiciones) + "\n",
                                      encoding="utf-8")
    print(f"{len(indice['order'])} diapositivas y {len(FIGURAS)} figuras de anexo; {len(colores)} colores")
    print("Notas más largas:", sorted(notas_largas, reverse=True)[:3])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Gráficas de la presentación de resultados de la réplica.

Uso: python3 herramientas/figuras.py
Lee datos/ (copias de los CSV de la réplica) y escribe figuras/*.pdf al tamaño exacto en que van en la
diapositiva, con una letra de las mismas medidas que la del PDF, para que nada se escale.

Paleta de los algoritmos, comprobada con validate_palette.js sobre blanco y con todos los pares: ΔE normal
≥ 19,8 entre los cinco del paper; el peor par con daltonismo (Autores frente a Williams, 7,1) lleva siempre
marcador distinto. Mutex es la referencia del equipo: gris oscuro y línea discontinua.
Máquinas: Core Ultra 9 con línea continua y marcador relleno; i5-10400 con línea discontinua y marcador hueco.
"""
import csv
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, NullFormatter, LogLocator

RAIZ = Path(__file__).resolve().parent.parent
DAT = RAIZ / "datos"
U9 = DAT / "ultra9"
I5 = DAT / "i5_10400"
FIG = RAIZ / "figuras"
FIG.mkdir(exist_ok=True)

TINTA, TINTA2, REJILLA, FONDO = "#1b2433", "#5b6472", "#e3e6ea", "#ffffff"
COL = {"Autores": "#c8232c", "Anderson": "#8e44ad", "Folly": "#c98500", "Williams": "#0f7f52",
       "Libstdc++": "#2b8fd6", "Mutex": "#4d4f54"}
MARCA = {"Autores": "o", "Anderson": "D", "Folly": "P", "Williams": "X", "Libstdc++": "s", "Mutex": "^"}
MAQ = {"Core Ultra 9 285": "#1f4e79", "Core i5-10400": "#9dbfe0"}
PAPER5 = ["Autores", "Anderson", "Folly", "Williams", "Libstdc++"]
EQUIPO = ["Autores", "Williams", "Libstdc++", "Mutex"]
PANELES = [("1", "1"), ("1", "10"), ("1", "50"), ("10", "1"), ("10", "10"), ("1000000", "50")]
PANELES_RAPIDA = [(n if n != "1000000" else "100000", u) for n, u in PANELES]
OPS = [("load", "load"), ("store", "store"), ("store-del", "store & reclaim")]
# medianas impresas en la figura 6 del paper, en ns (las mismas que usa analizar.py)
PAPER_FIG6 = {
    ("load", 1): {"Autores": 23, "Libstdc++": 29, "Folly": 24, "Anderson": 28},
    ("store", 1): {"Autores": 33, "Libstdc++": 36, "Folly": 37, "Anderson": 28},
    ("store-del", 1): {"Autores": 44, "Libstdc++": 41, "Folly": 49, "Anderson": 44},
    ("load", 56): {"Autores": 1140, "Libstdc++": 99700, "Folly": 11600, "Anderson": 2580},
    ("store", 56): {"Autores": 1470, "Libstdc++": 111000, "Folly": 2620, "Anderson": 2840},
    ("store-del", 56): {"Autores": 1570, "Libstdc++": 59300, "Folly": 5060, "Anderson": 1250},
}
ANCHO = 5.75  # pulgadas: el ancho de texto de la diapositiva


def letra():
    """Liberation Sans: TrueType con las medidas de Helvetica, así se incrusta limpia en el PDF y casa con tgheros.
    TeX Gyre Heros no sirve aquí: es OpenType CFF y matplotlib la incrusta mal. Si no está, la de matplotlib."""
    nombres = {f.name for f in font_manager.fontManager.ttflist}
    return "Liberation Sans" if "Liberation Sans" in nombres else "DejaVu Sans"


FAMILIA = letra()
plt.rcParams.update({
    "font.family": FAMILIA, "font.size": 7.5, "axes.titlesize": 7.8, "axes.titleweight": "bold", "axes.titlepad": 4,
    "axes.labelsize": 7.2, "xtick.labelsize": 6.8, "ytick.labelsize": 6.8, "legend.fontsize": 7,
    "text.color": TINTA, "axes.labelcolor": TINTA2, "axes.edgecolor": "#b9c0c8", "axes.linewidth": 0.6,
    "xtick.color": TINTA2, "ytick.color": TINTA2, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.minor.size": 1.5, "ytick.minor.size": 1.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": REJILLA,
    "grid.linewidth": 0.5, "axes.axisbelow": True, "figure.facecolor": FONDO, "axes.facecolor": FONDO,
    "savefig.facecolor": FONDO, "legend.frameon": False, "lines.linewidth": 1.3, "lines.markersize": 3.6,
    "pdf.fonttype": 42, "mathtext.fontset": "custom", "mathtext.rm": FAMILIA, "mathtext.it": FAMILIA + ":italic",
    "mathtext.bf": FAMILIA + ":bold", "mathtext.cal": FAMILIA, "mathtext.sf": FAMILIA, "mathtext.tt": FAMILIA, "figure.constrained_layout.h_pad": 0.03, "figure.constrained_layout.w_pad": 0.03,
})


# ---------- lectura y cálculo ----------

def leer(ruta):
    if not ruta.exists():
        return []
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def filtrar(filas, **f):
    return [r for r in filas if all(r.get(k) == str(v) for k, v in f.items())]


def vals(filas, campo="mops", **f):
    return [float(r[campo]) for r in filtrar(filas, **f) if r.get(campo) not in ("", None)]


def med(filas, campo="mops", **f):
    v = vals(filas, campo, **f)
    return st.median(v) if v else None


def num(v, dec=None):
    """Número con coma decimal y espacio de miles, como en el resto del documento."""
    if v is None or v != v:
        return "—"
    if dec is None:
        dec = 0 if abs(v) >= 100 or float(v).is_integer() else (1 if abs(v) >= 10 else 2)
    s = f"{v:,.{dec}f}".replace(",", " ").replace(".", ",")
    return s


def eje_num(ax, eje="y"):
    fmt = FuncFormatter(lambda v, _: num(v, 0) if float(v).is_integer() else (num(v, 1) if abs(v) >= 1 else corto(abs(v))))
    (ax.yaxis if eje == "y" else ax.xaxis).set_major_formatter(fmt)


def corto(v):
    """Número de menos de 1 con dos cifras significativas: 0,19 · 0,021 · 0,0026."""
    if v >= 1:
        return num(v, 0 if v >= 10 else 1)
    d = max(1, -int(math.floor(math.log10(v))) + 1)
    return f"{v:.{d}f}".rstrip("0").rstrip(",.").replace(".", ",")


def eje_log(ax, eje="y"):
    a = ax.yaxis if eje == "y" else ax.xaxis
    (ax.set_yscale if eje == "y" else ax.set_xscale)("log")
    a.set_major_locator(LogLocator(base=10, numticks=12))
    a.set_minor_formatter(NullFormatter())
    a.set_major_formatter(FuncFormatter(lambda v, _: num(v, 0) if v >= 1 else corto(v)))


def titulo(n, u):
    return f"n = {'10$^6$' if n == '1000000' else ('10$^5$' if n == '100000' else n)} · u = {u} %"


# Alto en milímetros con que cada gráfica entra en su diapositiva (\\grafica[alto]{...}). La gráfica se
# genera a ese tamaño exacto para que la letra no se encoja al colocarla.
ALTOS_MM = {
    "tandas.pdf": 49, "topologia.pdf": 47, "boceto.pdf": 49, "cota_cas.pdf": 43,
    "fig5_paper.pdf": 60, "fig5_docker.pdf": 60, "fig5_nativo_oficial.pdf": 60, "fig5_benchcpp.pdf": 60,
    "rapida_i5.pdf": 60, "rapida_u9.pdf": 60, "relativo_paper_replica.pdf": 58, "un_hilo.pdf": 37,
    "memoria_ram.pdf": 39, "docker_frente_a_nativo.pdf": 50, "maquinas_orden.pdf": 46,
    "maquinas_cociente.pdf": 50, "maquinas_latencia.pdf": 45, "mutex.pdf": 37,
    "alineado.pdf": 50, "alineado_ram.pdf": 44, "fig6_docker.pdf": 60, "latencia_relativa.pdf": 58,
    "williams_candado.pdf": 54, "colas.pdf": 46, "variabilidad.pdf": 44, "bimodal.pdf": 54,
    "memoria_retenida.pdf": 50, "dosis_respuesta.pdf": 60, "mapa_4hilos.pdf": 44, "mapa_8hilos.pdf": 44,
    "pares.pdf": 47, "williams_pares.pdf": 56, "miniatura.pdf": 57, "paridad.pdf": 49,
}


def guardar(fig, nombre):
    if nombre in ALTOS_MM:
        alto = ALTOS_MM[nombre] / 25.4
        fig.set_size_inches(fig.get_size_inches()[0], alto)
        if getattr(fig, "franja", False):
            fig.get_layout_engine().set(rect=(0, 0, 1, 1 - 0.19 / alto))
    fig.savefig(FIG / nombre)
    plt.close(fig)
    print("  ", nombre)


def estilo(impl, maquina="u9", banda=False):
    e = dict(color=COL[impl], marker=MARCA[impl], ms=3.6, lw=1.3)
    if impl == "Mutex":
        e["ls"] = (0, (4, 2))
    if maquina == "i5":
        e.update(ls=(0, (2.2, 1.6)), mfc=FONDO, mec=COL[impl], mew=0.9, lw=1.0)
    else:
        e.update(mec=FONDO, mew=0.4)
    return e


def arriba(fig, manijas, ncol=None):
    """Leyenda en una franja reservada arriba: constrained_layout de matplotlib 3.6 no deja sitio a fig.legend."""
    alto = fig.get_size_inches()[1]
    fig.franja = True
    fig.get_layout_engine().set(rect=(0, 0, 1, 1 - 0.19 / alto))
    fig.legend(handles=manijas, loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=ncol or len(manijas), handlelength=2.0,
               columnspacing=1.4, borderaxespad=0.15)


def leyenda_algoritmos(fig, impls, extra=()):
    arriba(fig, [Line2D([], [], label=i, **estilo(i)) for i in impls] + list(extra))


def rejilla(alto=2.6, compartir_y=False):
    fig, ejes = plt.subplots(2, 3, figsize=(ANCHO, alto), constrained_layout=True, sharey=compartir_y)
    return fig, ejes


# ---------- datos ----------

DOCKER = leer(U9 / "docker" / "rendimiento.csv")
NAT_OF = leer(U9 / "nativo_oficial" / "rendimiento.csv")
NAT_EQ = leer(U9 / "nativo" / "rendimiento.csv")
NAT_AL = leer(U9 / "nativo_alineado" / "rendimiento.csv")
LAT_DOCKER = leer(U9 / "docker" / "latencia.csv")
LAT_NAT_OF = leer(U9 / "nativo_oficial" / "latencia.csv")
LAT_CANDADO = leer(U9 / "docker" / "latencia_williams_con_candado.csv")
RAPIDA_U9 = leer(U9 / "correccion" / "rendimiento.csv")
RAPIDA_I5 = leer(I5 / "rendimiento.csv")
LATR_U9 = leer(U9 / "correccion" / "latencia.csv")
LATR_I5 = leer(I5 / "latencia.csv")
PAPER = leer(DAT / "paper" / "paper_fig5.csv")
RAM = leer(U9 / "memoria_ram.csv")
RAM_AL = leer(U9 / "nativo_alineado" / "memoria_alineado.csv")
BASURA_D = leer(U9 / "docker" / "basura.csv")
BASURA_N = leer(U9 / "nativo_oficial" / "basura.csv")
PARIDAD_D = leer(U9 / "docker" / "paridad.csv")
PARIDAD_N = leer(U9 / "nativo_oficial" / "paridad.csv")
COTA = leer(U9 / "correccion" / "cota_cas.csv")
MATRIZ = leer(U9 / "topologia" / "matriz_nucleos.csv")


# ---------- 1. diseño experimental ----------

def fig_tandas():
    u9 = [("Docker · binarios oficiales", 3720), ("Sin Docker · binarios oficiales", 4660),
          ("Sin Docker · bench.cpp del equipo", 2976), ("Sin Docker · bench.cpp con pilas alineadas", 2160),
          ("Controles", 546), ("Tráfico real de RAM", 70), ("Detectores en los rivales", 26),
          ("Pasada rápida de bench.cpp", 168)]
    i5 = [("Pasada rápida de bench.cpp", 168)]
    fig, (a, b) = plt.subplots(2, 1, figsize=(ANCHO, 2.45), constrained_layout=True, sharex=True,
                               gridspec_kw={"height_ratios": [len(u9), len(i5) + 0.6]})
    for ax, filas, maq in ((a, u9, "Core Ultra 9 285"), (b, i5, "Core i5-10400")):
        y = range(len(filas))
        ax.barh(y, [v for _, v in filas], color=MAQ[maq], height=0.62, edgecolor=MAQ["Core Ultra 9 285"] if maq != "Core Ultra 9 285" else "none", lw=0.6)
        ax.set_yticks(list(y), [t for t, _ in filas])
        ax.invert_yaxis()
        for i, (_, v) in enumerate(filas):
            ax.text(v + 40, i, num(v), va="center", fontsize=6.8, color=TINTA)
        ax.grid(axis="y", visible=False)
        ax.set_title(maq, loc="left", fontsize=7.6)
        ax.tick_params(axis="y", length=0)
    b.set_xlabel("mediciones (todas terminaron sin fallos)")
    b.set_xlim(0, 5200)
    eje_num(b, "x")
    guardar(fig, "tandas.pdf")


def clases_topologia():
    grupo = {c: ("P", c) for c in range(8)}
    for i, base in enumerate((8, 12, 16, 20)):
        grupo.update({c: ("E", i) for c in range(base, base + 4)})
    clases = defaultdict(list)
    for r in MATRIZ:
        a, b = grupo[int(r["a"])], grupo[int(r["b"])]
        if a[0] == b[0] == "P":
            k = "P ↔ P"
        elif a[0] != b[0]:
            k = "P ↔ E"
        else:
            k = "E, mismo clúster" if a[1] == b[1] else "E, clústeres distintos"
        clases[k].append(float(r["ns"]))
    return {k: st.median(v) for k, v in clases.items()}


def fig_topologia():
    m = [[float("nan")] * 24 for _ in range(24)]
    for r in MATRIZ:
        m[int(r["a"])][int(r["b"])] = float(r["ns"])
    tonos = LinearSegmentedColormap.from_list("azul", ["#eef4fb", "#a9c8ea", "#4f8fd1", "#1f4e79", "#0e2a47"])
    fig = plt.figure(figsize=(ANCHO, 2.55), constrained_layout=True)
    izq, der = fig.subplots(1, 2, gridspec_kw={"width_ratios": [1.05, 1]})
    im = izq.imshow(m, cmap=tonos, vmin=30, vmax=95)
    izq.grid(False)
    for corte in (7.5, 11.5, 15.5, 19.5):
        izq.axhline(corte, color=FONDO, lw=1.2)
        izq.axvline(corte, color=FONDO, lw=1.2)
    izq.set_xticks([3.5, 9.5, 13.5, 17.5, 21.5], ["8 P", "E0", "E1", "E2", "E3"])
    izq.set_yticks([3.5, 9.5, 13.5, 17.5, 21.5], ["8 P", "E0", "E1", "E2", "E3"])
    izq.tick_params(length=0)
    izq.set_title("Latencia de un viaje de línea de caché", loc="left")
    barra = fig.colorbar(im, ax=izq, shrink=0.82, pad=0.02)
    barra.set_label("ns", fontsize=6.8)
    barra.ax.tick_params(labelsize=6.3)
    cl = clases_topologia()
    orden = ["E, mismo clúster", "E, clústeres distintos", "P ↔ E", "P ↔ P"]
    rot = ["E, mismo\nclúster", "E, clústeres\ndistintos", "P–E", "P–P"]
    v = [cl[k] for k in orden]
    der.bar(range(4), v, color=["#a9c8ea", "#4f8fd1", "#2f6aa8", "#1f4e79"], width=0.6)
    for i, x in enumerate(v):
        der.text(i, x + 1.5, f"{num(x, 0)} ns\n{num(x / v[0], 2)}×", ha="center", va="bottom", fontsize=6.6, color=TINTA)
    der.set_xticks(range(4), rot)
    der.set_ylim(0, 112)
    der.set_ylabel("mediana por clase (ns)")
    der.grid(axis="x", visible=False)
    der.set_title("Cuatro distancias reales en un solo chip", loc="left")
    guardar(fig, "topologia.pdf")


# ---------- 2. corrección ----------

def fig_boceto():
    variantes = ["Versión ingenua", "C = P (rompe R-1)", "Sin salida temprana", "Algoritmo del paper"]
    errores = {"Core i5-10400": [632125, 63101, 0, 0], "Core Ultra 9 285": [227031, 42348, 0, 0]}
    intentos = {"Core i5-10400": [None, 8, 55, 8], "Core Ultra 9 285": [None, 7, 45, 6]}
    fig, (a, b) = plt.subplots(1, 2, figsize=(ANCHO, 2.25), constrained_layout=True)
    ancho = 0.36
    for k, (maq, desp) in enumerate((("Core i5-10400", -ancho / 2), ("Core Ultra 9 285", ancho / 2))):
        borde = MAQ["Core Ultra 9 285"]
        for i, e in enumerate(errores[maq]):
            if e:
                a.bar(i + desp, e, ancho, color=MAQ[maq], edgecolor=borde, lw=0.6)
                a.text(i + desp, e / 1.6, num(e), ha="center", va="top", fontsize=6, rotation=90,
                       color=FONDO if maq == "Core Ultra 9 285" else TINTA)
            else:
                a.text(i + desp, 1.4, "0", ha="center", va="bottom", fontsize=7, color=TINTA, fontweight="bold")
        for i, e in enumerate(intentos[maq]):
            if e is not None:
                b.bar(i + desp, e, ancho, color=MAQ[maq], edgecolor=borde, lw=0.6)
                b.text(i + desp, e + 1, str(e), ha="center", va="bottom", fontsize=6.4)
    eje_log(a)
    a.set_ylim(1, 4e6)
    a.set_xticks(range(4), ["Ingenua", "C = P", "Sin salida\ntemprana", "Paper"])
    a.set_ylabel("errores detectados (escala log.)")
    a.set_title("Errores de memoria en el boceto (8 hilos)", loc="left")
    b.axhline(8, color=TINTA, ls="--", lw=0.9)
    b.text(3.58, 12.5, "cota: P = 8", ha="right", fontsize=6.6, color=TINTA)
    b.set_xticks(range(1, 4), ["C = P", "Sin salida\ntemprana", "Paper"])
    b.set_xlim(0.4, 3.6)
    b.set_ylim(0, 64)
    b.set_ylabel("máximo de intentos de CAS por recarga")
    b.set_title("¿Se respeta la cota de intentos?", loc="left")
    for ax in (a, b):
        ax.grid(axis="x", visible=False)
    manijas = [Patch(facecolor=MAQ[m], edgecolor=MAQ["Core Ultra 9 285"], lw=0.6, label=m) for m in ("Core i5-10400", "Core Ultra 9 285")]
    arriba(fig, manijas, 2)
    guardar(fig, "boceto.pdf")


def fig_cota():
    def suma(variante):
        filas = filtrar(COTA, variante=variante)
        dist = [sum(int(r[f"i{k}"]) for r in filas) for k in range(1, 9)]
        return dist, max(int(r["max_intentos"]) for r in filas), sum(int(r["recargas"]) for r in filas)
    fig, (a, b) = plt.subplots(1, 2, figsize=(ANCHO, 2.2), constrained_layout=True, gridspec_kw={"width_ratios": [1, 1.25]})
    casos = [("Real\nP = 65 536", "cota_real", 65536), ("Forzada\nP = 32, C = 64", "cota_p32", 32), ("Límite\nC = P = 32", "cota_p32_c32", 32)]
    for i, (rot, var, cota) in enumerate(casos):
        _, maximo, _ = suma(var)
        a.bar(i - 0.18, maximo, 0.34, color="#1f4e79")
        a.bar(i + 0.18, cota, 0.34, color="#d5dde6", edgecolor="#8a96a3", lw=0.6)
        a.text(i - 0.18, maximo * 1.15, str(maximo), ha="center", fontsize=6.5, fontweight="bold")
        a.text(i + 0.18, cota * 1.15, num(cota), ha="center", fontsize=6.2, color=TINTA2)
    eje_log(a)
    a.set_ylim(1, 5e5)
    a.set_xticks(range(3), [c[0] for c in casos], fontsize=6.4)
    a.set_ylabel("intentos (escala log.)")
    a.set_title("Máximo observado frente a la cota", loc="left")
    a.legend(handles=[Patch(color="#1f4e79", label="máximo observado"), Patch(facecolor="#d5dde6", edgecolor="#8a96a3", label="cota P")],
             loc="upper right", fontsize=6.3)
    a.grid(axis="x", visible=False)
    dist, _, recargas = suma("cota_p32")
    total = sum(dist)
    pct = [100 * d / total for d in dist]
    b.bar(range(1, 9), pct, color="#1f4e79", width=0.62)
    for k, p in enumerate(pct, 1):
        if p > 0:
            b.text(k, p * 1.35, corto(p) + " %", ha="center", fontsize=5.8)
    eje_log(b)
    b.set_ylim(2e-7, 600)
    b.set_xticks(range(1, 9))
    b.set_xlabel("intentos de CAS en una recarga")
    b.set_ylabel("% de las recargas (escala log.)")
    b.set_title(f"Forzada: {num(recargas / 1e6, 1)} millones de recargas en total", loc="left")
    b.grid(axis="x", visible=False)
    guardar(fig, "cota_cas.pdf")


# ---------- 3. rendimiento ----------

def curva(ax, filas, impl, n, u, extra=None, banda=True, maquina="u9"):
    extra = extra or {}
    hilos = sorted({int(r["hilos"]) for r in filtrar(filas, impl=impl, n=n, u=u, **extra)})
    if not hilos:
        return
    m, lo, hi = [], [], []
    for h in hilos:
        v = vals(filas, impl=impl, n=n, u=u, hilos=h, **extra)
        m.append(st.median(v)), lo.append(min(v)), hi.append(max(v))
    if banda and len(vals(filas, impl=impl, n=n, u=u, hilos=hilos[0], **extra)) > 1:
        ax.fill_between(hilos, lo, hi, color=COL[impl], alpha=0.14, lw=0)
    ax.plot(hilos, m, **estilo(impl, maquina))


def fig_rendimiento(filas, impls, nombre, extra, todos, xticks, paneles=PANELES, rotulo_todos="todos los núcleos",
                    ylims=None, maquina="u9", alto=2.62, extra_leyenda=()):
    fig, ejes = rejilla(alto)
    for k, (ax, (n, u)) in enumerate(zip(ejes.flat, paneles)):
        for impl in impls:
            curva(ax, filas, impl, n, u, extra, maquina=maquina)
        if todos:
            ax.axvline(todos, color=TINTA2, ls=":", lw=0.9)
        ax.set_title(titulo(n, u), loc="left")
        ax.set_xticks(xticks)
        ax.set_ylim(0, ylims[k] if ylims else None)
        eje_num(ax)
    if todos:
        ejes[0, 2].text(todos, 0.98, " " + rotulo_todos, transform=ejes[0, 2].get_xaxis_transform(), fontsize=6, color=TINTA2, va="top")
    for ax in ejes[1]:
        ax.set_xlabel("hilos")
    for ax in ejes[:, 0]:
        ax.set_ylabel("Mop/s")
    arriba(fig, [Line2D([], [], label=i, **estilo(i, maquina)) for i in impls] + list(extra_leyenda))
    guardar(fig, nombre)


def fig_rendimiento_paper():
    fig, ejes = rejilla(2.62)
    for ax, (n, u) in zip(ejes.flat, PANELES):
        for impl in PAPER5:
            hilos = sorted({int(r["hilos"]) for r in filtrar(PAPER, impl=impl, n=n, u=u)})
            ax.plot(hilos, [med(PAPER, impl=impl, n=n, u=u, hilos=h) for h in hilos], **estilo(impl))
        ax.axvline(144, color=TINTA2, ls=":", lw=0.9)
        ax.set_title(titulo(n, u), loc="left")
        ax.set_xticks([1, 72, 144, 216])
        ax.set_ylim(bottom=0)
        eje_num(ax)
    ejes[0, 2].text(144, 0.98, " 144 hilos", transform=ejes[0, 2].get_xaxis_transform(), fontsize=6, color=TINTA2, va="top")
    for ax in ejes[1]:
        ax.set_xlabel("hilos")
    for ax in ejes[:, 0]:
        ax.set_ylabel("Mop/s")
    leyenda_algoritmos(fig, PAPER5)
    guardar(fig, "fig5_paper.pdf")


def relativo(filas, impl, n, u, hilos, extra=None):
    extra = extra or {}
    a = med(filas, impl="Autores", n=n, u=u, hilos=hilos, **extra)
    b = med(filas, impl=impl, n=n, u=u, hilos=hilos, **extra)
    return b / a if a and b else None


def fig_relativo():
    rivales = ["Anderson", "Folly", "Williams", "Libstdc++"]
    fig, ejes = plt.subplots(2, 3, figsize=(ANCHO, 2.6), constrained_layout=True, sharex=True, sharey=True)
    for ax, (n, u) in zip(ejes.flat, PANELES):
        for y, impl in enumerate(rivales):
            p = relativo(PAPER, impl, n, u, 144)
            d = relativo(DOCKER, impl, n, u, 24, {"experimento": "fig5"})
            s = relativo(NAT_OF, impl, n, u, 24, {"experimento": "fig5"})
            ax.plot([p, d], [y, y], color=COL[impl], lw=1.2, alpha=0.4)
            ax.plot(p, y, ls="", marker="o", ms=4.6, mfc=FONDO, mec=COL[impl], mew=1.1)
            ax.plot(d, y, ls="", marker="o", ms=4.6, color=COL[impl], mec=FONDO, mew=0.4)
            ax.plot(s, y + 0.28, ls="", marker="|", ms=4.5, color=COL[impl], mew=1.1)
        ax.axvline(1, color=TINTA, lw=0.8)
        ax.set_xscale("log")
        ax.set_xlim(0.03, 3)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v, 0 if v >= 1 else (1 if v >= 0.1 else 2)) + "×"))
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_yticks(range(len(rivales)), rivales)
        ax.set_ylim(len(rivales) - 0.4, -0.6)
        ax.set_title(titulo(n, u), loc="left")
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", length=0)
    fig.supxlabel("rendimiento del rival ÷ el de Autores, con toda la máquina (a la izquierda de 1, gana Autores)", fontsize=6.8, color=TINTA2)
    manijas = [Line2D([], [], ls="", marker="o", ms=4.6, mfc=FONDO, mec=TINTA2, mew=1.1, label="paper, 144 hilos"),
               Line2D([], [], ls="", marker="o", ms=4.6, color=TINTA2, label="réplica con Docker, 24 hilos"),
               Line2D([], [], ls="", marker="|", ms=5, color=TINTA2, mew=1.1, label="réplica sin Docker, 24 hilos")]
    arriba(fig, manijas, 3)
    guardar(fig, "relativo_paper_replica.pdf")


def fig_un_hilo():
    fig, ejes = plt.subplots(1, 2, figsize=(ANCHO, 2.05), constrained_layout=True, sharey=True)
    for ax, impl in zip(ejes, ("Folly", "Williams")):
        for y, (n, u) in enumerate(PANELES):
            p = relativo(PAPER, impl, n, u, 1)
            d = relativo(DOCKER, impl, n, u, 1, {"experimento": "fig5"})
            ax.plot([p, d], [y, y], color=COL[impl], lw=1.2, alpha=0.4)
            ax.plot(p, y, ls="", marker="o", ms=4.6, mfc=FONDO, mec=COL[impl], mew=1.1)
            ax.plot(d, y, ls="", marker="o", ms=4.6, color=COL[impl], mec=FONDO, mew=0.4)
            ax.text(max(p, d) * 1.12, y, f"{num(p, 2)}× → {num(d, 2)}×", va="center", fontsize=6, color=TINTA)
        ax.axvline(1, color=TINTA, lw=0.8)
        ax.set_xscale("log")
        ax.set_xlim(0.1, 4)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v, 0 if v >= 1 else 1) + "×"))
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_yticks(range(6), [titulo(*p) for p in PANELES])
        ax.set_ylim(5.5, -0.5)
        ax.set_title(f"{impl} ÷ Autores, con 1 hilo", loc="left")
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", length=0)
    manijas = [Line2D([], [], ls="", marker="o", ms=4.6, mfc=FONDO, mec=TINTA2, mew=1.1, label="paper"),
               Line2D([], [], ls="", marker="o", ms=4.6, color=TINTA2, label="réplica (Docker)")]
    arriba(fig, manijas, 2)
    guardar(fig, "un_hilo.pdf")


def trafico(filas, **f):
    return med(filas, "gbs_lectura", **f) + med(filas, "gbs_escritura", **f)


def fig_ram():
    reposo = trafico(RAM, prueba="reposo")
    techo = max(trafico(RAM, prueba="lectura", hilos=h) for h in {r["hilos"] for r in filtrar(RAM, prueba="lectura")})
    azar = max(trafico(RAM, prueba="azar", hilos=h) for h in {r["hilos"] for r in filtrar(RAM, prueba="azar")})
    hilos = sorted({int(r["hilos"]) for r in filtrar(RAM, prueba="pila")})
    fig, (a, b) = plt.subplots(1, 2, figsize=(ANCHO, 2.25), constrained_layout=True)
    for impl in PAPER5:
        g = [trafico(RAM, prueba="pila", impl=impl, hilos=h) for h in hilos]
        m = [med(RAM, prueba="pila", impl=impl, hilos=h) for h in hilos]
        a.plot(hilos, g, **estilo(impl))
        b.plot(hilos, [1000 * (x - reposo) / y for x, y in zip(g, m)], **estilo(impl))
    a.axhline(techo, color=TINTA2, ls="--", lw=0.8)
    a.text(hilos[0], techo + 0.6, f"techo leyendo en orden: {num(techo, 0)} GB/s", fontsize=6, color=TINTA2)
    a.axhline(azar, color=TINTA2, ls=":", lw=0.9)
    a.text(hilos[0], azar + 0.6, f"techo con accesos al azar: {num(azar, 0)} GB/s", fontsize=6, color=TINTA2)
    a.set_ylim(0, techo * 1.13)
    a.set_ylabel("tráfico de RAM (GB/s)")
    a.set_title("Cuánto se acercan al techo de la RAM", loc="left")
    b.set_ylim(0, None)
    b.set_ylabel("bytes de RAM por operación")
    b.set_title("Cuánta RAM gasta cada operación", loc="left")
    for ax in (a, b):
        ax.set_xlabel("hilos (n = 10$^6$, u = 50 %)")
        ax.set_xticks(hilos)
        eje_num(ax)
    leyenda_algoritmos(fig, PAPER5)
    guardar(fig, "memoria_ram.pdf")


def fig_docker_nativo():
    fig, (a, b) = plt.subplots(1, 2, figsize=(ANCHO, 2.45), constrained_layout=True, gridspec_kw={"width_ratios": [1, 1.15]})
    cocientes = {}
    for impl in PAPER5:
        px, py = [], []
        for n, u in PANELES:
            for h in (1, 3, 6, 9, 12, 18, 24, 30, 36):
                x = med(DOCKER, experimento="fig5", impl=impl, n=n, u=u, hilos=h)
                y = med(NAT_OF, experimento="fig5", impl=impl, n=n, u=u, hilos=h)
                if x and y:
                    px.append(x), py.append(y)
        cocientes[impl] = [y / x for x, y in zip(px, py)]
        a.plot(px, py, ls="", marker=MARCA[impl], ms=3.2, color=COL[impl], mec=FONDO, mew=0.3, alpha=0.85)
    lim = (0.08, 200)
    a.plot(lim, lim, color=TINTA, lw=0.8, ls="--")
    for ax_ in ("x", "y"):
        eje_log(a, ax_)
    a.set_xlim(lim), a.set_ylim(lim)
    a.set_xlabel("con Docker (Mop/s)")
    a.set_ylabel("sin Docker (Mop/s)")
    a.set_title("Los 270 puntos de la figura 5", loc="left")
    b.axhspan(0.9, 1.1, color="#eef1f4", lw=0)
    b.axhspan(0.95, 1.05, color="#dfe5eb", lw=0)
    for k, impl in enumerate(PAPER5):
        c = sorted(cocientes[impl])
        xs = [k + (j / max(len(c) - 1, 1) - 0.5) * 0.5 for j in range(len(c))]
        b.plot(xs, c, ls="", marker=MARCA[impl], ms=2.8, color=COL[impl], alpha=0.75, mec=FONDO, mew=0.2)
        mm = st.median(c)
        b.plot([k - 0.32, k + 0.32], [mm, mm], color=TINTA, lw=1.2)
        b.text(k, 1.165, f"{num(mm, 2)}×", ha="center", fontsize=6.4, color=TINTA)
    b.axhline(1, color=TINTA, lw=0.7)
    b.set_ylim(0.84, 1.19)
    b.set_xticks(range(5), PAPER5, fontsize=6.4)
    b.yaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v, 2) + "×"))
    b.set_ylabel("sin Docker ÷ con Docker")
    b.set_title("Cociente por algoritmo (bandas: ±5 % y ±10 %)", loc="left")
    b.grid(axis="x", visible=False)
    leyenda_algoritmos(fig, PAPER5)
    guardar(fig, "docker_frente_a_nativo.pdf")
    todos = [c for v in cocientes.values() for c in v]
    print(f"     Docker/nativo: {len(todos)} puntos, <5 %: {sum(abs(c - 1) < 0.05 for c in todos)}, <10 %: {sum(abs(c - 1) < 0.10 for c in todos)}")


# ---------- 4. dos máquinas, mismo programa ----------

def ylims_comunes(filas_a, filas_b, impls, paneles):
    out = []
    for n, u in paneles:
        m = max(float(r["mops"]) for f in (filas_a, filas_b) for r in f if r["n"] == n and r["u"] == u and r["impl"] in impls)
        out.append(m * 1.08)
    return out


def fig_maquinas():
    lims = ylims_comunes(RAPIDA_I5, RAPIDA_U9, EQUIPO, PANELES_RAPIDA)
    xt = [1, 4, 8, 12, 18]
    fig_rendimiento(RAPIDA_I5, EQUIPO, "rapida_i5.pdf", {}, 12, xt, PANELES_RAPIDA, "12 hilos de hardware", lims, maquina="i5")
    fig_rendimiento(RAPIDA_U9, EQUIPO, "rapida_u9.pdf", {}, None, xt, PANELES_RAPIDA, "", lims)


def fig_maquinas_cociente():
    fig, ejes = rejilla(2.55, compartir_y=True)
    for ax, (n, u) in zip(ejes.flat, PANELES_RAPIDA):
        for impl in EQUIPO:
            hilos = sorted({int(r["hilos"]) for r in filtrar(RAPIDA_I5, impl=impl, n=n, u=u)})
            c = [med(RAPIDA_U9, impl=impl, n=n, u=u, hilos=h) / med(RAPIDA_I5, impl=impl, n=n, u=u, hilos=h) for h in hilos]
            ax.plot(hilos, c, **estilo(impl))
        ax.axhline(1, color=TINTA, lw=0.8)
        ax.axhspan(0.1, 1, color="#f4f6f8", lw=0, zorder=0)
        eje_log(ax)
        ax.set_ylim(0.3, 6)
        ax.set_yticks([0.5, 1, 2, 4])
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v, 0 if v >= 1 else 1) + "×"))
        ax.set_title(titulo(n, u), loc="left")
        ax.set_xticks([1, 4, 8, 12, 18])
    ejes[0, 0].text(18, 0.36, "gana el i5 ", ha="right", fontsize=6, color=TINTA2)
    ejes[0, 0].text(18, 4.6, "gana el Ultra 9 ", ha="right", fontsize=6, color=TINTA2)
    for ax in ejes[1]:
        ax.set_xlabel("hilos")
    for ax in ejes[:, 0]:
        ax.set_ylabel("Ultra 9 ÷ i5")
    leyenda_algoritmos(fig, EQUIPO)
    guardar(fig, "maquinas_cociente.pdf")


def fig_maquinas_orden():
    rivales = ["Williams", "Libstdc++", "Mutex"]
    fig, ejes = plt.subplots(1, 2, figsize=(ANCHO, 2.2), constrained_layout=True, sharey=True, sharex=True)
    for ax, (filas, maq, h) in zip(ejes, ((RAPIDA_I5, "Core i5-10400 · 12 hilos (toda la máquina)", 12),
                                          (RAPIDA_U9, "Core Ultra 9 285 · 12 hilos", 12))):
        for y, (n, u) in enumerate(PANELES_RAPIDA):
            for k, impl in enumerate(rivales):
                r = relativo(filas, impl, n, u, h)
                e = {**estilo(impl), "ms": 4.2, "ls": ""}
                ax.plot(r, y + (k - 1) * 0.2, **e)
        ax.axvline(1, color=TINTA, lw=0.8)
        ax.set_xscale("log")
        ax.set_xlim(0.025, 2)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v, 0 if v >= 1 else (1 if v >= 0.1 else 2)) + "×"))
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_yticks(range(6), [titulo(*p) for p in PANELES_RAPIDA])
        ax.set_ylim(5.5, -0.5)
        ax.set_title(maq, loc="left")
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", length=0)
        ax.set_xlabel("rival ÷ Autores (a la izquierda de 1, gana Autores)")
    leyenda_algoritmos(fig, rivales)
    guardar(fig, "maquinas_orden.pdf")


def fig_maquinas_latencia():
    fig, ejes = plt.subplots(2, 3, figsize=(ANCHO, 2.75), constrained_layout=True)
    for fila, (pi5, pu9, escala) in enumerate(((1, 1, "linear"), (12, 24, "log"))):
        for ax, (op_csv, rot) in zip(ejes[fila], (("load", "load"), ("store", "store"), ("store&reclaim", "store & reclaim"))):
            for k, impl in enumerate(EQUIPO):
                for j, (filas, p, maq) in enumerate(((LATR_I5, pi5, "i5"), (LATR_U9, pu9, "u9"))):
                    r = filtrar(filas, impl=impl, op=op_csv, p=p)
                    if not r:
                        continue
                    m, p99 = float(r[0]["p50"]), float(r[0]["p99"])
                    x = k + (j - 0.5) * 0.36
                    ax.bar(x, m, 0.34, color=COL[impl] if maq == "u9" else FONDO, edgecolor=COL[impl], lw=0.8,
                           hatch=None)
                    if escala == "log":
                        ax.plot([x, x], [m, p99], color=COL[impl], lw=0.7)
                        ax.plot([x - 0.08, x + 0.08], [p99, p99], color=COL[impl], lw=0.7)
            ax.set_xticks(range(4), ["Aut.", "Will.", "Libs.", "Mutex"], fontsize=6.4)
            ax.grid(axis="x", visible=False)
            if escala == "log":
                eje_log(ax)
                ax.set_ylim(30, 1e5)
            else:
                eje_num(ax)
            ax.set_title(f"{rot} · " + ("p = 1" if fila == 0 else "p = 12 / 24"), loc="left", fontsize=7.0)
    ejes[0, 0].set_ylabel("mediana (ns)")
    ejes[1, 0].set_ylabel("mediana y p99 (ns, log.)")
    manijas = [Patch(facecolor=FONDO, edgecolor=TINTA2, lw=0.8, label="i5-10400 (p = 1 y p = 12)"),
               Patch(facecolor=TINTA2, edgecolor=TINTA2, lw=0.8, label="Ultra 9 (p = 1 y p = 24)"),
               Line2D([], [], color=TINTA2, lw=0.7, marker="_", ms=5, label="raya: hasta el p99")]
    arriba(fig, manijas, 3)
    guardar(fig, "maquinas_latencia.pdf")


def fig_mutex():
    fig, (a, b) = plt.subplots(1, 2, figsize=(ANCHO, 2.15), constrained_layout=True)
    for impl in ("Autores", "Mutex"):
        curva(a, NAT_EQ, impl, "1", "50", {"experimento": "fig5"})
        curva(b, RAPIDA_I5, impl, "1", "50", maquina="i5")
        curva(b, RAPIDA_U9, impl, "1", "50")
    a.set_title("Core Ultra 9 · batería sin Docker (5 rondas de 2 s)", loc="left")
    b.set_title("Pasada rápida (1 s): i5 frente a Ultra 9", loc="left")
    a.set_xticks([1, 6, 12, 18, 24, 30, 36])
    b.set_xticks([1, 4, 8, 12, 18])
    for ax in (a, b):
        ax.set_xlabel("hilos (n = 1, u = 50 %)")
        ax.set_ylabel("Mop/s")
        eje_log(ax)
        ax.set_ylim(0.8, 120)
    manijas = [Line2D([], [], label=i, **estilo(i)) for i in ("Autores", "Mutex")] + \
              [Line2D([], [], color=TINTA2, lw=1.3, label="Ultra 9"), Line2D([], [], color=TINTA2, lw=1.0, ls=(0, (2.2, 1.6)), marker="o", mfc=FONDO, mec=TINTA2, ms=3.6, label="i5-10400")]
    arriba(fig, manijas, 4)
    guardar(fig, "mutex.pdf")


# ---------- 5. compartición falsa ----------

def fig_alineado():
    fig, (a, b) = plt.subplots(1, 2, figsize=(ANCHO, 2.3), constrained_layout=True, gridspec_kw={"width_ratios": [1.45, 1]})
    for k, (n, u) in enumerate(PANELES):
        for j, impl in enumerate(EQUIPO):
            x0 = med(NAT_EQ, experimento="fig5", impl=impl, n=n, u=u, hilos=24)
            x1 = med(NAT_AL, experimento="fig5", impl=impl, n=n, u=u, hilos=24)
            x = k + (j - 1.5) * 0.19
            a.bar(x, x1 / x0, 0.17, color=COL[impl])
            if impl == "Autores" and n == "10":
                a.text(x, x1 / x0 + 0.08, f"{num(x1 / x0, 2)}×", ha="center", fontsize=6.2, fontweight="bold")
    a.axhline(1, color=TINTA, lw=0.8)
    a.set_xticks(range(6), [titulo(*p).replace(" · ", "\n") for p in PANELES], fontsize=6.2)
    a.set_ylabel("alineado ÷ sin alinear (24 hilos)")
    a.yaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v, 0 if float(v).is_integer() else 1) + "×"))
    a.set_ylim(0, 3.9)
    a.grid(axis="x", visible=False)
    a.set_title("Una palabra, alignas(128), en una copia de bench.cpp", loc="left")
    for impl, filas, extra, rot, ls in (("Autores", NAT_EQ, {"experimento": "fig5"}, "bench.cpp sin alinear", (0, (2.2, 1.6))),
                                        ("Autores", NAT_AL, {"experimento": "fig5"}, "bench.cpp alineado", "-"),
                                        ("Autores", NAT_OF, {"experimento": "fig5"}, "binario oficial", ":")):
        hilos = sorted({int(r["hilos"]) for r in filtrar(filas, impl=impl, n="10", u="1", **extra)})
        m = [med(filas, impl=impl, n="10", u="1", hilos=h, **extra) for h in hilos]
        e = estilo(impl)
        e["ls"] = ls
        if ls != "-":
            e.update(mfc=FONDO, mec=COL[impl], mew=0.8)
        b.plot(hilos, m, label=rot, **e)
    b.set_xticks([1, 6, 12, 18, 24, 30, 36])
    b.set_xlabel("hilos")
    b.set_ylabel("Mop/s")
    b.set_ylim(0, 150)
    b.set_title("Autores con n = 10 · u = 1 %", loc="left")
    b.legend(loc="center right", bbox_to_anchor=(1.0, 0.52), fontsize=6.2, handlelength=2.6)
    leyenda_algoritmos(fig, EQUIPO)
    guardar(fig, "alineado.pdf")


def fig_alineado_ram():
    reposo = trafico(RAM, prueba="reposo")
    fig, (a, b) = plt.subplots(1, 2, figsize=(ANCHO, 2.15), constrained_layout=True)
    for j, impl in enumerate(EQUIPO):
        for k, n in enumerate(("1000000", "100000")):
            f = dict(impl=impl, n=n)
            ms = {v: med(RAM_AL, version=v, **f) for v in ("sin_alinear", "alineado")}
            g = {v: trafico(RAM_AL, version=v, **f) for v in ("sin_alinear", "alineado")}
            bpo = {v: 1000 * (g[v] - reposo) / ms[v] for v in ms}
            if n == "1000000":
                x = j
                a.bar(x - 0.18, bpo["sin_alinear"], 0.34, color=FONDO, edgecolor=COL[impl], lw=0.9)
                a.bar(x + 0.18, bpo["alineado"], 0.34, color=COL[impl])
                a.text(x + 0.18, bpo["alineado"] + 15, num(bpo["alineado"], 0), ha="center", fontsize=6)
                a.text(x - 0.18, bpo["sin_alinear"] + 15, num(bpo["sin_alinear"], 0), ha="center", fontsize=6, color=TINTA2)
            rondas = sorted({r["ronda"] for r in RAM_AL})
            cs = [med(RAM_AL, version="alineado", ronda=r, **f) / med(RAM_AL, version="sin_alinear", ronda=r, **f) for r in rondas]
            x = j + (k - 0.5) * 0.36
            b.plot([x] * len(cs), cs, ls="", marker="o" if n == "1000000" else "s", ms=3.4,
                   color=COL[impl] if n == "1000000" else FONDO, mec=COL[impl], mew=0.8)
    a.set_xticks(range(4), EQUIPO, fontsize=6.6)
    a.set_ylabel("bytes de RAM por operación")
    a.set_ylim(0, 1050)
    a.set_title("n = 10$^6$: hueco = sin alinear, relleno = alineado", loc="left", fontsize=7.2)
    a.grid(axis="x", visible=False)
    b.axhline(1, color=TINTA, lw=0.8)
    b.set_xticks(range(4), EQUIPO, fontsize=6.6)
    b.set_ylim(0.65, 1.08)
    b.yaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v, 2) + "×"))
    b.set_ylabel("alineado ÷ sin alinear, por ronda")
    b.set_title("Rendimiento: n = 10$^6$ (●) frente a n = 10$^5$ (□)", loc="left", fontsize=7.2)
    b.grid(axis="x", visible=False)
    guardar(fig, "alineado_ram.pdf")


# ---------- 6. latencia ----------

def percentiles(filas, **f):
    claves = ("p1", "p25", "p50", "p75", "p99")
    return {k: st.median(vals(filas, k, **f) or [float("nan")]) for k in claves}


def fig_latencia(filas, impls, p_alto, nombre):
    fig, ejes = plt.subplots(2, 3, figsize=(ANCHO, 2.85), constrained_layout=True)
    for fila_ejes, p, escala in ((ejes[0], 1, "linear"), (ejes[1], p_alto, "log")):
        for ax, (op, rot) in zip(fila_ejes, OPS):
            cajas, etiquetas = [], []
            for impl in impls:
                q = percentiles(filas, experimento="fig6", impl=impl, op=op, p=p)
                if q["p50"] == q["p50"]:
                    cajas.append({"label": impl, "whislo": q["p1"], "q1": q["p25"], "med": q["p50"], "q3": q["p75"], "whishi": q["p99"], "fliers": []})
                    etiquetas.append(impl)
            b = ax.bxp(cajas, showfliers=False, patch_artist=True, widths=0.42, medianprops={"color": TINTA, "lw": 1.2},
                       whiskerprops={"lw": 0.7}, capprops={"lw": 0.7}, boxprops={"lw": 0.7})
            for caja, impl in zip(b["boxes"], etiquetas):
                caja.set_facecolor(COL[impl] + "38")
                caja.set_edgecolor(COL[impl])
            for tipo in ("whiskers", "caps"):
                for linea, impl in zip(b[tipo], [i for i in etiquetas for _ in (0, 1)]):
                    linea.set_color(COL[impl])
            for x, c in enumerate(cajas, 1):
                m = c["med"]
                ax.text(x + 0.25, m, num(m, 0) if m < 1000 else num(m / 1000, 1) + " µs", ha="left", va="center", fontsize=5.6, color=TINTA)
            ax.set_xticks(range(1, len(etiquetas) + 1), [{"Libstdc++": "Libs.", "Williams": "Will.", "Anderson": "Ander.", "Autores": "Aut."}.get(i, i) for i in etiquetas], fontsize=6.2)
            ax.set_xlim(0.5, len(cajas) + 0.9)
            if escala == "log":
                eje_log(ax)
            else:
                ax.set_ylim(bottom=0)
                eje_num(ax)
            ax.set_title(f"{rot} · p = {p}", loc="left", fontsize=7.2)
            ax.grid(axis="x", visible=False)
    ejes[0, 0].set_ylabel("ns")
    ejes[1, 0].set_ylabel("ns (escala log.)")
    guardar(fig, nombre)


def fig_latencia_relativa():
    rivales = ["Anderson", "Folly", "Williams", "Libstdc++"]
    fig, ejes = plt.subplots(2, 3, figsize=(ANCHO, 2.6), constrained_layout=True, sharex=True, sharey=True)
    for fila, (pp, pr) in enumerate(((1, 1), (56, 56))):
        for ax, (op, rot) in zip(ejes[fila], OPS):
            pap = PAPER_FIG6[(op, pp)]
            for y, impl in enumerate(rivales):
                d = med(LAT_DOCKER, "p50", experimento="fig6", impl=impl, op=op, p=pr) / med(LAT_DOCKER, "p50", experimento="fig6", impl="Autores", op=op, p=pr)
                s = med(LAT_NAT_OF, "p50", experimento="fig6", impl=impl, op=op, p=pr) / med(LAT_NAT_OF, "p50", experimento="fig6", impl="Autores", op=op, p=pr)
                if impl in pap:
                    p = pap[impl] / pap["Autores"]
                    ax.plot([p, d], [y, y], color=COL[impl], lw=1.1, alpha=0.4)
                    ax.plot(p, y, ls="", marker="o", ms=4.4, mfc=FONDO, mec=COL[impl], mew=1.1)
                ax.plot(d, y, ls="", marker="o", ms=4.4, color=COL[impl], mec=FONDO, mew=0.4)
                ax.plot(s, y + 0.28, ls="", marker="|", ms=4.5, color=COL[impl], mew=1.1)
            ax.axvline(1, color=TINTA, lw=0.8)
            ax.set_xscale("log")
            ax.set_xlim(0.4, 120)
            ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v, 0 if v >= 1 else 1) + "×"))
            ax.xaxis.set_minor_formatter(NullFormatter())
            ax.set_yticks(range(4), rivales)
            ax.set_ylim(3.6, -0.6)
            ax.set_title(f"{rot} · p = {pr}", loc="left", fontsize=7.2)
            ax.grid(axis="y", visible=False)
            ax.tick_params(axis="y", length=0)
    fig.supxlabel("latencia mediana del rival ÷ la de Autores (a la derecha de 1, Autores es más rápido)", fontsize=6.8, color=TINTA2)
    manijas = [Line2D([], [], ls="", marker="o", ms=4.4, mfc=FONDO, mec=TINTA2, mew=1.1, label="paper"),
               Line2D([], [], ls="", marker="o", ms=4.4, color=TINTA2, label="réplica con Docker (5 rondas)"),
               Line2D([], [], ls="", marker="|", ms=5, color=TINTA2, mew=1.1, label="réplica sin Docker (15 rondas)")]
    arriba(fig, manijas, 3)
    guardar(fig, "latencia_relativa.pdf")


def fig_candado():
    casos = [("load", 1), ("load", 24), ("load", 56), ("store", 24), ("store-del", 24)]
    fig, ax = plt.subplots(figsize=(2.85, 2.2), constrained_layout=True)
    for k, (op, p) in enumerate(casos):
        a = med(LAT_CANDADO, "p50", experimento="fig6", impl="Williams", op=op, p=p)
        b = med(LAT_DOCKER, "p50", experimento="fig6", impl="Williams", op=op, p=p)
        ax.bar(k - 0.19, a, 0.36, color=FONDO, edgecolor=COL["Williams"], lw=0.9, hatch="////")
        ax.bar(k + 0.19, b, 0.36, color=COL["Williams"])
        ax.text(k - 0.19, a * 1.2, num(a, 0) if a < 1000 else num(a / 1000, 1) + " µs", ha="center", fontsize=5.2)
        ax.text(k + 0.19, b * 1.2, num(b, 0) if b < 1000 else num(b / 1000, 1) + " µs", ha="center", fontsize=5.2)
    eje_log(ax)
    ax.set_ylim(10, 3e5)
    ax.set_xticks(range(len(casos)), [f"{'s&r' if o == 'store-del' else o}\np={p}" for o, p in casos], fontsize=6)
    ax.set_ylabel("mediana (ns, log.)")
    ax.grid(axis="x", visible=False)
    ax.legend(handles=[Patch(facecolor=FONDO, edgecolor=COL["Williams"], hatch="////", label="sin -mcx16 (candado)"),
                       Patch(color=COL["Williams"], label="con -mcx16")], loc="upper left", fontsize=6)
    guardar(fig, "williams_candado.pdf")


def fig_colas():
    fig, (a, b) = plt.subplots(1, 2, figsize=(ANCHO, 2.15), constrained_layout=True, sharey=False)
    for ax, (op, p, tit) in zip((a, b), (("store-del", 1, "store & reclaim · p = 1"), ("load", 24, "load · p = 24"))):
        for k, impl in enumerate(PAPER5):
            q = [med(LAT_DOCKER, c, experimento="fig6", impl=impl, op=op, p=p) for c in ("p50", "p99", "p9995")]
            for j, v in enumerate(q):
                x = k + (j - 1) * 0.26
                ax.bar(x, v, 0.24, color=COL[impl], alpha=(0.35, 0.65, 1.0)[j], lw=0)
            ax.text(k + 0.26, q[2] * 1.25, num(q[2], 0) if q[2] < 1000 else num(q[2] / 1000, 1) + " µs", ha="center", fontsize=5.6)
        eje_log(ax)
        ax.set_xticks(range(5), ["Aut.", "Ander.", "Folly", "Will.", "Libs."], fontsize=6.4)
        ax.set_title(tit, loc="left")
        ax.grid(axis="x", visible=False)
        ax.set_ylabel("ns (escala log.)")
    a.set_ylim(10, 3e4)
    b.set_ylim(100, 3e5)
    manijas = [Patch(color=TINTA2, alpha=al, label=l) for al, l in ((0.35, "mediana"), (0.65, "p99"), (1.0, "p99,95: 1 de cada 2 000"))]
    arriba(fig, manijas, 3)
    guardar(fig, "colas.pdf")


def cocientes_rondas(filas):
    grupos = defaultdict(list)
    for r in filtrar(filas, experimento="fig6"):
        grupos[(r["impl"], r["op"], int(r["p"]))].append(float(r["p50"]))
    return {k: max(v) / min(v) for k, v in grupos.items() if min(v) > 0}


def fig_variabilidad():
    d, n = cocientes_rondas(LAT_DOCKER), cocientes_rondas(LAT_NAT_OF)
    fig, ax = plt.subplots(figsize=(ANCHO, 2.05), constrained_layout=True)
    for k, p in enumerate((1, 24, 56)):
        for j, (datos, rot) in enumerate(((d, "Docker, 5 rondas"), (n, "sin Docker, 15 rondas"))):
            for impl in PAPER5:
                v = [c for (i, o, pp), c in datos.items() if pp == p and i == impl]
                x = k + (j - 0.5) * 0.38 + (PAPER5.index(impl) - 2) * 0.05
                ax.plot([x] * len(v), v, ls="", marker=MARCA[impl], ms=3.2, color=COL[impl] if j == 0 else FONDO, mec=COL[impl], mew=0.7)
            todos = [c for (i, o, pp), c in datos.items() if pp == p]
            mm = st.median(todos)
            ax.plot([k + (j - 0.5) * 0.38 - 0.15, k + (j - 0.5) * 0.38 + 0.15], [mm, mm], color=TINTA, lw=1.2)
    eje_log(ax)
    ax.set_ylim(0.8, 80)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v, 0) + "×"))
    ax.set_xticks(range(3), ["p = 1 (sin contención)", "p = 24 (todos los núcleos)", "p = 56 (más hilos que núcleos)"])
    ax.set_ylabel("ronda más lenta ÷ más rápida")
    ax.grid(axis="x", visible=False)
    leyenda_algoritmos(fig, PAPER5, extra=(Line2D([], [], ls="", marker="o", ms=3.4, color=TINTA2, label="Docker, 5 rondas"),
                                          Line2D([], [], ls="", marker="o", ms=3.4, mfc=FONDO, mec=TINTA2, label="sin Docker, 15 rondas")))
    guardar(fig, "variabilidad.pdf")


def fig_bimodal():
    fig, ax = plt.subplots(figsize=(2.85, 2.2), constrained_layout=True)
    for k, impl in enumerate(PAPER5):
        v = sorted(vals(LAT_NAT_OF, "p50", experimento="fig6", impl=impl, op="load", p=24))
        xs = [k + ((j % 5) - 2) * 0.06 for j in range(len(v))]
        ax.plot(xs, v, ls="", marker=MARCA[impl], ms=3.2, color=COL[impl], mec=FONDO, mew=0.3)
    ax.axhspan(520, 1000, color="#f4f6f8", lw=0, zorder=0)
    ax.text(4.45, 720, "hueco entre\nlos dos grupos", ha="right", va="center", fontsize=5.6, color=TINTA2)
    eje_log(ax)
    ax.set_ylim(250, 3e4)
    ax.set_xticks(range(5), ["Aut.", "Ander.", "Folly", "Will.", "Libs."], fontsize=6.4)
    ax.set_ylabel("mediana de cada ronda (ns)")
    ax.set_title("load · p = 24 · 15 rondas", loc="left")
    ax.grid(axis="x", visible=False)
    guardar(fig, "bimodal.pdf")


# ---------- 7. memoria retenida ----------

def fig_basura():
    fig, ejes = plt.subplots(1, 2, figsize=(ANCHO, 2.15), constrained_layout=True, sharey=True)
    for ax, (filas, tit) in zip(ejes, ((BASURA_D, "Con Docker"), (BASURA_N, "Sin Docker"))):
        hilos = sorted({int(r["hilos"]) for r in filas})
        for impl in PAPER5:
            ax.plot(hilos, [med(filas, "pico_bloques", impl=impl, hilos=h) for h in hilos], **estilo(impl))
        lim = [med(filas, "limite_bloques", impl="Autores", hilos=h) for h in hilos]
        ax.plot(hilos, lim, color=TINTA, ls="--", lw=0.9)
        ax.text(4.5, 95, "límite si todo se libera en el acto", ha="left", va="bottom", fontsize=5.8, color=TINTA)
        a24 = med(filas, "pico_bloques", impl="Anderson", hilos=24)
        ax.text(23.4, a24 * 1.35, f"Anderson: {num(a24, 0)} bloques", ha="right", fontsize=6, color=TINTA)
        eje_log(ax)
        ax.set_ylim(4, 1e5)
        ax.set_xticks(hilos)
        ax.set_xlabel("hilos (la mitad escribe, la otra mitad lee)")
        ax.set_title(tit, loc="left")
    ejes[0].set_ylabel("pico de bloques vivos (log.)")
    leyenda_algoritmos(fig, PAPER5)
    guardar(fig, "memoria_retenida.pdf")


# ---------- 8. topología y afinidad ----------

def fig_dosis():
    cl = clases_topologia()
    x = ["E4-compacto", "E4-disperso", "P4"]
    rot = [f"1 clúster\n{num(cl['E, mismo clúster'], 0)} ns", f"4 clústeres\n{num(cl['E, clústeres distintos'], 0)} ns", f"4 núcleos P\n{num(cl['P ↔ P'], 0)} ns"]
    fig, ejes = rejilla(2.7)
    for ax, (n, u) in zip(ejes.flat, PANELES):
        for impl in PAPER5:
            y = [med(DOCKER, experimento="afinidad", impl=impl, n=n, u=u, colocacion=c) for c in x]
            ax.plot(range(3), y, **estilo(impl))
        ax.set_xticks(range(3), rot, fontsize=6)
        ax.set_xlim(-0.25, 2.25)
        ax.set_ylim(bottom=0)
        ax.set_title(titulo(n, u), loc="left")
        ax.grid(axis="x", visible=False)
        eje_num(ax)
    for ax in ejes[:, 0]:
        ax.set_ylabel("Mop/s, 4 hilos")
    leyenda_algoritmos(fig, PAPER5)
    guardar(fig, "dosis_respuesta.pdf")


def fig_mapas(h, nombre):
    tonos = LinearSegmentedColormap.from_list("div", ["#1f4e79", "#7fa9d6", "#eceae6", "#e9a77c", "#a3471a"])
    fig, ejes = plt.subplots(1, 2, figsize=(ANCHO, 1.95), constrained_layout=True, sharey=True)
    for ax, (filas, tit) in zip(ejes, ((DOCKER, "Con Docker"), (NAT_OF, "Sin Docker"))):
        m = []
        for impl in PAPER5:
            fila = []
            for n, u in PANELES:
                c = med(filas, experimento="afinidad", impl=impl, n=n, u=u, colocacion=f"E{h}-compacto")
                d = med(filas, experimento="afinidad", impl=impl, n=n, u=u, colocacion=f"E{h}-disperso")
                fila.append(100 * (d / c - 1))
            m.append(fila)
        im = ax.imshow(m, cmap=tonos, norm=TwoSlopeNorm(vcenter=0, vmin=-60, vmax=60), aspect="auto")
        ax.grid(False)
        ax.set_xticks(range(6), [titulo(*p).replace(" · ", "\n") for p in PANELES], fontsize=5.8)
        ax.set_yticks(range(5), PAPER5)
        ax.tick_params(length=0)
        for i in range(5):
            for j in range(6):
                v = m[i][j]
                texto = f"{v:+.0f} %" if abs(v) < 100 else f"{v:+.0f}%"
                ax.text(j, i, texto.replace("-", "−"), ha="center", va="center", fontsize=6, color=FONDO if abs(v) > 38 else TINTA)
        ax.set_title(f"{tit} · {h} hilos", loc="left")
    barra = fig.colorbar(im, ax=ejes, shrink=0.9, pad=0.01)
    barra.set_label("cambio al separar (%)", fontsize=6.4)
    barra.ax.tick_params(labelsize=6)
    guardar(fig, nombre)


def fig_pares():
    clases = ["mismo clúster", "clústeres distintos", "P ↔ P", "P ↔ E"]
    fig, ejes = plt.subplots(1, 2, figsize=(ANCHO, 2.2), constrained_layout=True, sharey=True)
    for ax, (filas, tit) in zip(ejes, ((DOCKER, "Con Docker · 3 rondas por par"), (NAT_OF, "Sin Docker · 10 rondas por par"))):
        for k, clase in enumerate(clases):
            for j, impl in enumerate(PAPER5):
                v = med(filas, experimento="pares", impl=impl, familia=clase)
                x = k + (j - 2) * 0.16
                ax.bar(x, v, 0.15, color=COL[impl])
                if impl == "Williams" and clase == "clústeres distintos":
                    ax.text(x, v + 0.35, num(v, 2), ha="center", fontsize=6, fontweight="bold", color=TINTA)
        ax.set_xticks(range(4), ["mismo\nclúster", "clústeres\ndistintos", "P–P", "P–E"], fontsize=6.4)
        ax.set_title(tit, loc="left")
        ax.grid(axis="x", visible=False)
        eje_num(ax)
    ejes[0].set_ylabel("Mop/s, 2 hilos, n = 1, u = 50 %")
    leyenda_algoritmos(fig, PAPER5)
    guardar(fig, "pares.pdf")


def fig_williams_pares():
    clases = ["mismo clúster", "clústeres distintos", "P ↔ P", "P ↔ E"]
    fig, ax = plt.subplots(figsize=(2.85, 2.2), constrained_layout=True)
    for j, (filas, rot, relleno) in enumerate(((DOCKER, "Docker", True), (NAT_OF, "sin Docker", False))):
        for k, clase in enumerate(clases):
            v = vals(filas, experimento="pares", impl="Williams", familia=clase)
            x0 = k + (j - 0.5) * 0.34
            xs = [x0 + ((i % 7) - 3) * 0.025 for i in range(len(v))]
            ax.plot(xs, v, ls="", marker="X" if relleno else "o", ms=3, color=COL["Williams"] if relleno else FONDO, mec=COL["Williams"], mew=0.6, alpha=0.9)
    eje_log(ax)
    ax.set_ylim(0.01, 40)
    ax.set_xticks(range(4), ["mismo\nclúster", "clúst.\ndistintos", "P–P", "P–E"], fontsize=6.2)
    ax.set_ylabel("Mop/s de cada ronda (log.)")
    ax.set_title("Williams, ronda a ronda", loc="left")
    ax.grid(axis="x", visible=False)
    ax.legend(handles=[Line2D([], [], ls="", marker="X", ms=3.4, color=COL["Williams"], label="Docker"),
                       Line2D([], [], ls="", marker="o", ms=3.4, mfc=FONDO, mec=COL["Williams"], label="sin Docker")],
              loc="upper right", ncol=2, fontsize=6)
    guardar(fig, "williams_pares.pdf")


def fig_miniatura():
    paneles = [("1", "1"), ("10", "1"), ("1000000", "50")]
    fig, ejes = plt.subplots(2, 3, figsize=(ANCHO, 2.75), constrained_layout=True)
    for col, (n, u) in enumerate(paneles):
        ax = ejes[0, col]
        for impl in PAPER5:
            hs = [1, 18, 36, 54, 72]
            y = [med(PAPER, impl=impl, n=n, u=u, hilos=h) for h in hs]
            if all(v is not None for v in y):
                ax.plot([100 * h / 72 for h in hs], y, **estilo(impl))
        ax.set_title(titulo(n, u), loc="left")
        ax = ejes[1, col]
        for impl in PAPER5:
            hs = [(1, "E1"), (4, "E4-compacto"), (8, "E8-compacto"), (12, "E12-compacto"), (16, "E16")]
            y = [med(DOCKER, experimento="afinidad", impl=impl, n=n, u=u, colocacion=c) for _, c in hs]
            if all(v is not None for v in y):
                ax.plot([100 * h / 16 for h, _ in hs], y, **estilo(impl))
        ax.set_xlabel("% de los núcleos en uso")
    for ax in ejes.flat:
        ax.set_ylim(bottom=0)
        ax.set_xticks([0, 25, 50, 75, 100])
        eje_num(ax)
    ejes[0, 0].set_ylabel("Paper · 4 Xeon\nMop/s")
    ejes[1, 0].set_ylabel("Réplica · 4 clústeres E\nMop/s")
    leyenda_algoritmos(fig, PAPER5)
    guardar(fig, "miniatura.pdf")


# ---------- 9. validación de los recortes ----------

def fig_paridad():
    puntos = []
    for r in PARIDAD_N:
        corta = med(NAT_OF, experimento="fig5", impl=r["impl"], n=r["n"], u=r["u"], hilos=24)
        larga = float(r["mediana_7x10s"])
        puntos.append((PANELES.index((r["n"], r["u"])), r["impl"], 100 * (corta / larga - 1)))
    fig, ax = plt.subplots(figsize=(ANCHO, 2.2), constrained_layout=True)
    for k in range(6):
        sub = [p for p in puntos if p[0] == k]
        for j, (_, impl, d) in enumerate(sorted(sub, key=lambda p: PAPER5.index(p[1]))):
            x = k + (j - 2) * 0.15
            ax.bar(x, d, 0.13, color=COL[impl])
    ax.axhline(0, color=TINTA, lw=0.8)
    ax.axhspan(-5, 5, color="#f1f3f6", lw=0, zorder=0)
    ax.set_xticks(range(6), [titulo(*p) for p in PANELES], fontsize=6.4)
    ax.set_ylabel("2 s × 5 frente a 10 s × 7 (%)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0f} %".replace("-", "−")))
    ax.set_ylim(-14, 24)
    ax.grid(axis="x", visible=False)
    ax.axvline(4.5, color=TINTA2, lw=0.6, ls=":")
    ax.text(2.0, 21.5, "con contención: la versión corta da más (23 de 25)", ha="center", fontsize=6.2, color=TINTA)
    ax.text(4.6, 21.5, "n = 10$^6$: da menos (5 de 5)", ha="left", fontsize=6.2, color=TINTA)
    leyenda_algoritmos(fig, PAPER5)
    guardar(fig, "paridad.pdf")
    con = [p for p in puntos if p[0] < 5]
    print(f"     paridad: con contención, más en la corta {sum(p[2] > 0 for p in con)}/{len(con)}; n=1e6 menos {sum(p[2] < 0 for p in puntos if p[0] == 5)}/5")


# ---------- tablas del anexo ----------

TAB = RAIZ / "tablas"


def escribir(nombre, filas):
    TAB.mkdir(exist_ok=True)
    (TAB / nombre).write_text("% Generado por herramientas/figuras.py: no editar a mano\n" + "\n".join(filas) + "\n", encoding="utf-8")
    print("  ", "tablas/" + nombre)


def titulo_tex(n, u):
    return f"n = {({'1000000': '10⁶', '100000': '10⁵'}).get(n, n)} · u = {u}\\,\\%"


def tablas_anexo():
    f = ["\\begin{tabularx}{\\linewidth}{@{}p{24mm}" + "C" * 5 + "@{}}", "\\toprule",
         "\\textbf{24 hilos, Mop/s} & " + " & ".join(f"\\textbf{{{i}}}" for i in PAPER5) + "\\\\", "\\midrule"]
    for n, u in PANELES:
        d = [med(DOCKER, experimento="fig5", impl=i, n=n, u=u, hilos=24) for i in PAPER5]
        s_ = [med(NAT_OF, experimento="fig5", impl=i, n=n, u=u, hilos=24) for i in PAPER5]
        f.append(titulo_tex(n, u) + " & " + " & ".join(f"{num(a, 2)} / {num(b, 2)}" for a, b in zip(d, s_)) + "\\\\")
    f += ["\\bottomrule", "\\end{tabularx}"]
    escribir("fig5_24hilos.tex", f)

    f = ["\\begin{tabularx}{\\linewidth}{@{}p{30mm}" + "C" * 5 + "@{}}", "\\toprule",
         "\\textbf{Mediana, ns} & " + " & ".join(f"\\textbf{{{i}}}" for i in PAPER5) + "\\\\", "\\midrule"]
    for op, rot in OPS:
        for p in (1, 24, 56):
            v = {i: med(LAT_NAT_OF, "p50", experimento="fig6", impl=i, op=op, p=p) for i in PAPER5}
            mejor = min(v.values())
            f.append(f"\\cod{{{rot.replace('&', '\\&')}}}, p = {p} & " + " & ".join(
                (f"\\textbf{{{num(x, 0)}}}" if x == mejor else num(x, 0)) for x in v.values()) + "\\\\")
    f += ["\\bottomrule", "\\end{tabularx}"]
    escribir("latencia_nativo.tex", f)

    for h in (1, 12):
        f = ["\\begin{tabularx}{\\linewidth}{@{}p{24mm}" + "C" * 8 + "@{}}", "\\toprule",
             "& " + " & ".join(f"\\multicolumn{{2}}{{c}}{{\\textbf{{{i}}}}}" for i in EQUIPO) + "\\\\",
             "".join(f"\\cmidrule(lr){{{2 + 2 * k}-{3 + 2 * k}}}" for k in range(4)),
             f"\\textbf{{{h} hilo{'s' if h > 1 else ''}, Mop/s}} & " + " & ".join(["i5", "U9"] * 4) + "\\\\", "\\midrule"]
        for n, u in PANELES_RAPIDA:
            celdas = []
            for i in EQUIPO:
                celdas += [num(med(RAPIDA_I5, impl=i, n=n, u=u, hilos=h), 1), num(med(RAPIDA_U9, impl=i, n=n, u=u, hilos=h), 1)]
            f.append(titulo_tex(n, u) + " & " + " & ".join(celdas) + "\\\\")
        f += ["\\bottomrule", "\\end{tabularx}"]
        escribir(f"maquinas_{h}hilos.tex", f)

    f = ["\\begin{tabularx}{\\linewidth}{@{}p{30mm}" + "C" * 8 + "@{}}", "\\toprule",
         "& " + " & ".join(f"\\multicolumn{{2}}{{c}}{{\\textbf{{{i}}}}}" for i in EQUIPO) + "\\\\",
         "".join(f"\\cmidrule(lr){{{2 + 2 * k}-{3 + 2 * k}}}" for k in range(4)),
         "\\textbf{Mediana (p99), ns} & " + " & ".join(["i5", "U9"] * 4) + "\\\\", "\\midrule"]
    for op, rot in (("load", "load"), ("store", "store"), ("store&reclaim", "store \\& reclaim")):
        for pi5, pu9, rp in ((1, 1, "p = 1"), (12, 24, "p = 12 / 24")):
            celdas = []
            for i in EQUIPO:
                for filas, p in ((LATR_I5, pi5), (LATR_U9, pu9)):
                    r = filtrar(filas, impl=i, op=op, p=p)[0]
                    m, q = float(r["p50"]), float(r["p99"])
                    celdas.append(num(m, 1 if m < 100 else 0) + (f" ({num(q, 1 if q < 100 else 0)})" if p > 1 else ""))
            f.append(f"\\cod{{{rot}}}, {rp} & " + " & ".join(celdas) + "\\\\")
    f += ["\\bottomrule", "\\end{tabularx}"]
    escribir("latencia_maquinas.tex", f)


def resumen():
    """Cifras que cita el texto de las diapositivas, para comprobarlas contra los CSV."""
    print("  cifras:")
    for n, u in PANELES:
        print("   ", titulo(n, u), "Docker 24h:", {i: num(med(DOCKER, experimento='fig5', impl=i, n=n, u=u, hilos=24), 2) for i in PAPER5})
    for n, u in PANELES_RAPIDA:
        print("   rápida 1h/12h", titulo(n, u), "i5:", num(med(RAPIDA_I5, impl='Autores', n=n, u=u, hilos=1), 1), num(med(RAPIDA_I5, impl='Autores', n=n, u=u, hilos=12), 1),
              "U9:", num(med(RAPIDA_U9, impl='Autores', n=n, u=u, hilos=1), 1), num(med(RAPIDA_U9, impl='Autores', n=n, u=u, hilos=12), 1))


def main():
    print(f"letra: {FAMILIA}")
    for f in (fig_tandas, fig_topologia, fig_boceto, fig_cota, fig_rendimiento_paper, fig_relativo, fig_un_hilo, fig_ram,
              fig_docker_nativo, fig_maquinas, fig_maquinas_cociente, fig_maquinas_orden, fig_maquinas_latencia, fig_mutex,
              fig_alineado, fig_alineado_ram, fig_latencia_relativa, fig_candado, fig_colas, fig_variabilidad, fig_bimodal,
              fig_basura, fig_dosis, fig_pares, fig_williams_pares, fig_miniatura, fig_paridad):
        f()
    fig_rendimiento(DOCKER, PAPER5, "fig5_docker.pdf", {"experimento": "fig5"}, 24, [1, 6, 12, 18, 24, 30, 36])
    fig_rendimiento(NAT_EQ, EQUIPO, "fig5_benchcpp.pdf", {"experimento": "fig5"}, 24, [1, 6, 12, 18, 24, 30, 36])
    fig_rendimiento(NAT_OF, PAPER5, "fig5_nativo_oficial.pdf", {"experimento": "fig5"}, 24, [1, 6, 12, 18, 24, 30, 36])
    fig_latencia(LAT_DOCKER, PAPER5, 24, "fig6_docker.pdf")
    fig_mapas(4, "mapa_4hilos.pdf")
    fig_mapas(8, "mapa_8hilos.pdf")
    tablas_anexo()
    resumen()


if __name__ == "__main__":
    main()

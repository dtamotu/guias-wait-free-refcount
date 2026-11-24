"""Recorta, como PDF vectorial, los gráficos de la presentación original.

Uso:  python herramientas/extraer_graficos.py ../presentacion_con_notas.pdf
Cada diapositiva N está en la página 2N-1 del PDF con notas. Las zonas están en
puntos (la página mide 453,5 x 255,1). Las salidas van a figuras/sNN.pdf.
"""
import sys
from pathlib import Path

import pymupdf

ZONAS = {
    9: (20, 57, 434, 198), 10: (20, 60, 434, 203), 16: (20, 57, 434, 192),
    26: (20, 57, 434, 195), 27: (20, 57, 434, 180), 32: (20, 57, 434, 230),
    33: (20, 57, 434, 230), 36: (20, 57, 434, 222), 38: (20, 57, 434, 188),
    40: (20, 57, 434, 163), 43: (20, 70, 434, 179), 48: (20, 57, 434, 200),
    49: (20, 57, 434, 230), 54: (20, 57, 434, 230), 55: (20, 57, 434, 230),
    56: (20, 57, 434, 188), 57: (20, 57, 434, 200), 60: (20, 57, 434, 186),
    61: (20, 57, 434, 163), 65: (20, 57, 434, 146), 66: (20, 57, 434, 200),
    67: (20, 71, 434, 240), 68: (20, 57, 434, 155), 71: (230, 76, 434, 170),
    72: (20, 57, 434, 228), 74: (20, 57, 434, 222), 76: (20, 60, 228, 218),
    77: (20, 57, 434, 155), 78: (0, 57, 453.5, 168), 79: (20, 60, 228, 218),
}


def main(pdf):
    src = pymupdf.open(pdf)
    dest = Path(__file__).resolve().parent.parent / "figuras"
    dest.mkdir(exist_ok=True)
    for n, z in ZONAS.items():
        zona = pymupdf.Rect(z)
        out = pymupdf.open()
        pag = out.new_page(width=zona.width, height=zona.height)
        pag.show_pdf_page(pag.rect, src, 2 * n - 2, clip=zona)
        out.set_metadata({})
        out.save(dest / f"s{n:02d}.pdf", garbage=4, deflate=True)
    print(len(ZONAS), "gráficos en", dest)


if __name__ == "__main__":
    main(sys.argv[1])

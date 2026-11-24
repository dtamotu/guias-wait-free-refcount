"""Saca el texto completo de las notas del PDF original (en él se salían por la derecha).

Uso:  python herramientas/extraer_notas.py ../presentacion_con_notas.pdf
Escribe notas/sNN.tex, un archivo por diapositiva, con el texto escapado para LaTeX.
"""
import re
import sys
from pathlib import Path

import pymupdf

ESCAPES = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
           "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}"}


def escapar(t):
    t = "".join(ESCAPES.get(c, c) for c in t)
    t = re.sub(r"(\d) (\d{3})(?!\d)", r"\1~\2", t)      # no partir «14 158» entre líneas
    return t


def main(pdf):
    d = pymupdf.open(pdf)
    dest = Path(__file__).resolve().parent.parent / "notas"
    dest.mkdir(exist_ok=True)
    for n in range(1, d.page_count // 2 + 1):
        pag = d[2 * n - 1]
        bloques = [b[4].strip() for b in pag.get_text("blocks", clip=pymupdf.INFINITE_RECT())
                   if b[6] == 0 and b[4].strip()]
        bloques = [re.sub(r"^Diapositiva \d+\s*", "", b) for b in bloques]
        bloques = [b for b in bloques if b]
        # El primer bloque repite el título de la diapositiva (salvo en las portadas de parte).
        titulo = " ".join(" ".join(d[2 * n - 2].get_text().split("\n")[:4]).split())
        if bloques and " ".join(bloques[0].split()) in titulo:
            bloques = bloques[1:]
        parrafos = [escapar(" ".join(b.split())) for b in bloques]
        (dest / f"s{n:02d}.tex").write_text("\n\n".join(parrafos) + "\n", encoding="utf-8")
    print(d.page_count // 2, "notas en", dest)


if __name__ == "__main__":
    main(sys.argv[1])

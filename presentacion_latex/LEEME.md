# Presentación en LaTeX (Beamer)

Versión en PDF de la presentación de la réplica de **«A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting»** (Euro-Par 2024). Son 105 diapositivas y unas 2 h 30 min, más el turno de preguntas, con notas del orador en todas.

## Los dos PDF

| Archivo | Qué es | Páginas |
|---|---|---|
| [`presentacion.pdf`](presentacion.pdf) | Para proyectar: 104 diapositivas y un anexo con las 20 figuras originales de la réplica | 124 |
| [`presentacion_con_notas.pdf`](presentacion_con_notas.pdf) | Para ensayar o imprimir: detrás de cada diapositiva va una página con su guion. Incluye la diapositiva oculta «Lo que no hay que decir», con la lista de tareas antes de exponer | 250 |

La agenda, el reparto sugerido entre David, Jheremy y Diego y los tiempos de cada parte están en las diapositivas 2 y 3.

## Qué hay en la carpeta

| Archivo o carpeta | Para qué sirve |
|---|---|
| `presentacion.tex` | Documento principal: preámbulo, colores, tamaños y cómo se colocan las diapositivas |
| `presentacion_con_notas.tex` | Activa las notas del orador e incluye `presentacion.tex` |
| `diapositivas.tex` | Las 105 diapositivas y el anexo. **Se genera**: no lo edites a mano |
| `colores.tex` | Los colores que usan las diapositivas. También se genera |
| `figuras/` | Las 20 gráficas PNG de `replica/resultados/david-ultra9-285/figuras/`, para el anexo |
| `fuente_html/` | La presentación original en HTML (`deck.json` y una diapositiva por archivo), de la que sale todo |
| `herramientas/html_a_beamer.py` | Convierte `fuente_html/` en `diapositivas.tex` y `colores.tex` |

## Cómo compilar

Hace falta TeX Live con `beamer`, `tcolorbox`, `pgfplots` y `babel-spanish`. Se compila con `pdflatex`, dos veces, porque la colocación de cada diapositiva necesita una segunda pasada:

```bash
cd presentacion_latex
latexmk -pdf presentacion.tex presentacion_con_notas.tex
# o, sin latexmk:
pdflatex presentacion.tex && pdflatex presentacion.tex
pdflatex presentacion_con_notas.tex && pdflatex presentacion_con_notas.tex
```

## Cómo cambiar una diapositiva

1. Edita su archivo en `fuente_html/slides/` (el orden está en `fuente_html/deck.json`). Las notas del orador son el `<aside>` del final.
2. Regenera y compila:

   ```bash
   python3 herramientas/html_a_beamer.py
   latexmk -pdf presentacion.tex presentacion_con_notas.tex
   ```

Si una diapositiva no cabe, se reduce sola y el registro lo avisa con una línea `AJUSTE: diapositiva N reducida`. Ahora pasa en 6, y ninguna se reduce más de un 9 %.

## De dónde sale cada dato

Cada diapositiva lleva al pie su fuente: `EXPLICACION.md`, `DEFENSA.md`, `tablas.md` o un CSV de `replica/resultados/david-ultra9-285/`, en el repositorio de la réplica. Las gráficas de barras y la de líneas están dibujadas con esos mismos números; las figuras originales están en el anexo.

Si una cifra de aquí no coincide con `EXPLICACION.md`, manda `EXPLICACION.md`.

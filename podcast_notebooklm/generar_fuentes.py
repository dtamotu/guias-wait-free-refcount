#!/usr/bin/env python3
"""Genera las fuentes del podcast para NotebookLM a partir de EXPLICACION.md y DEFENSA.md de la réplica.

Escribe, junto a este archivo:
  fuentes_md/   un .md por episodio, más el mapa de la serie y el glosario. Son los que se suben a NotebookLM.
  fuentes_pdf/  los mismos en PDF, con las figuras dentro, para leerlos o por si NotebookLM no acepta el .md.
  00_COMO_GENERAR_EL_PODCAST.md   los pasos y el prompt de cada episodio. Ese no se sube.

Si cambia EXPLICACION.md o DEFENSA.md, basta con volver a ejecutarlo:  python3 generar_fuentes.py
Necesita pandoc y Google Chrome (o Chromium) para los PDF; sin ellos, escribe solo los .md.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPLICA = Path("/home/alumno16/Documentos/Davichi/proyecto/replica-wait-free-refcount/replica/completa")
FUENTES = {"EXP": REPLICA / "EXPLICACION.md", "DEF": REPLICA / "DEFENSA.md"}
SERIE = "Leer sin que te quiten el libro"
LIMITE_PROMPT = 500   # NotebookLM no publica el límite del cuadro de instrucciones; 500 caracteres es prudente

# (número, archivo, título, tramos [(fuente, encabezado inicial, encabezado final)], formato, duración, lo esencial, prompt)
EPISODIOS = [
    (1, "presentacion", "Qué hicimos y qué salió",
     [("EXP", "## Parte 0.", "## Parte 1.")], "Análisis en profundidad", "Predeterminada",
     ["El equipo repitió el paper con los programas oficiales de los autores en un PC con un Intel Core Ultra 9 285, con y sin Docker: más de 14 000 mediciones, ninguna fallida.",
      "De las 15 afirmaciones del paper, 9 se reproducen, 2 en parte, 3 no y 1 no se confirma.",
      "Lo central sale bien parado: es correcto, cumple su cota wait-free, no acumula basura y lee rápido. No se sostiene la superioridad frente a Folly ni la ventaja con un millón de pilas."],
     "Episodio 1 de 14. Presenta el paper (Euro-Par 2024), al equipo y qué significa reproducir un experimento. Cuenta qué se hizo y el marcador: de 15 afirmaciones, 9 se reproducen, 2 en parte, 3 no y 1 no se confirma. Sin detalles técnicos: llegan después. Cierra anunciando el episodio 2, la carrera entre leer y liberar."),
    (2, "el_problema", "La carrera entre leer y liberar",
     [("EXP", "## Parte 1.", "## Parte 3.")], "Análisis en profundidad", "Más larga",
     ["Leer un puntero compartido y apuntarse como usuario son dos pasos. Entre los dos, otro hilo puede liberar el objeto: es la carrera read-reclaim, que acaba en un use-after-free.",
      "El procesador solo hace una operación indivisible sobre un sitio de la memoria, y el tablón y la libreta están en dos sitios distintos.",
      "Hay tres familias de solución: poner un candado, retrasar la trituradora o pagar por adelantado en el propio tablón."],
     "Episodio 2 de 14. Explica la carrera read-reclaim con la historia de Marta y Beto en la biblioteca, paso a paso. Luego el vocabulario: operaciones atómicas, CAS, fetch_add, wait-free frente a lock-free y por qué compartir una línea de caché es caro. Termina con las tres familias de solución. Cierra anunciando el episodio 3, los rivales."),
    (3, "los_rivales", "Los rivales: candados, cuentas dobles y basura retrasada",
     [("EXP", "## Parte 3.", "### 3.6"), ("EXP", "### 3.7", "## Parte 4.")], "Análisis en profundidad", "Más larga",
     ["Mutex y Libstdc++ usan un candado: es simple, pero forma colas.",
      "Williams y Folly guardan una cuenta junto al puntero, pero usan bucles de CAS que pueden fallar y reintentar.",
      "Anderson retrasa la liberación con hazard pointers: es rápido, pero retiene algo de memoria un rato."],
     "Episodio 3 de 14. Presenta uno a uno a los rivales del paper: la versión ingenua, Mutex, Libstdc++, Williams, Folly y Anderson. De cada uno: la idea en una frase, su analogía, cómo lee y cómo escribe, y su punto débil. Termina con la tabla que los compara. Cierra anunciando el episodio 4, la solución del paper."),
    (4, "la_solucion", "La solución del paper: el taco de vales",
     [("EXP", "### 3.6", "### 3.7")], "Análisis en profundidad", "Más larga",
     ["El tablón guarda un taco de vales prepagados. Arrancar un vale lee la dirección y reserva el libro en un solo gesto: un fetch_add que nunca falla.",
      "La regla de oro: libreta = vales en el taco + vales en manos de la gente.",
      "Por eso la lectura es wait-free: termina siempre en un número acotado de pasos, y recargar el taco reintenta como mucho P veces."],
     "Episodio 4 de 14, el central. Explica el algoritmo del paper con la historia del taco de vales: la regla de oro, cómo caben dirección y vales en 64 bits, qué pasa al recargar el taco y por qué la cota es de P intentos. Repite la idea de varias formas. Cierra anunciando el episodio 5, cómo se hizo la réplica."),
    (5, "el_metodo", "Cómo se hizo la réplica, y cuánto fiarse",
     [("EXP", "## Parte 4.", "## Parte 5."), ("EXP", "### 6.7", "## Parte 7.")], "Análisis en profundidad", "Predeterminada",
     ["Se usaron los programas oficiales del artefacto de Zenodo, con su MD5 comprobado: es el código de los autores, no una copia.",
      "Adaptaciones: los hilos se dividieron entre 6 (24 son toda la máquina, como 144 en el paper) y se midieron 5 rondas de 2 s, en orden aleatorio, en vez de 7 de 10 s.",
      "El recorte se validó con la receta exacta: sin Docker se desvía de −10 % a +19 %, y el orden se mantiene en 4 de 6 escenarios. Por eso las diferencias pequeñas se tratan como empate."],
     "Episodio 5 de 14. Explica qué midieron los autores, qué se usó aquí y cada adaptación con su porqué: hilos divididos entre 6, 2 s en vez de 10 y orden aleatorio. Después, cómo se comprobó que recortar no cambia las conclusiones y por qué una diferencia pequeña es un empate. Cierra anunciando el episodio 6, simular 4 procesadores."),
    (6, "simular_4_xeon", "Simular 4 procesadores con un solo PC",
     [("EXP", "## Parte 5.", "## Parte 6."), ("EXP", "### 6.4", "### 6.5")], "Análisis en profundidad", "Más larga",
     ["Una máquina virtual con 4 nodos NUMA sería un decorado. Se usaron distancias reales: 35 ns dentro de un clúster, 47 entre clústeres y 86 entre núcleos P.",
      "Separar 4 hilos cuesta mucho donde hay contención (Autores pierde entre un 32 % y un 54 %) y nada donde no la hay (±2 % con un millón de pilas).",
      "Lo que importa es compartir la caché L2, no los nanosegundos. Y el castigo aquí es mucho más suave que entre sockets reales: 1,35× frente a unas 3×."],
     "Episodio 6 de 14. Explica por qué no se usó una máquina virtual, cómo se midieron las distancias entre núcleos y el experimento de dosis-respuesta con 4 hilos. Cuenta la rareza de Williams entre clústeres como una historia de detectives. Deja claro qué demuestra la simulación y qué no. Cierra anunciando el episodio 7, el rendimiento."),
    (7, "rendimiento", "Rendimiento: quién gana, y el misterio de Folly",
     [("EXP", "## Parte 6.", "### 6.2")], "Análisis en profundidad", "Más larga",
     ["Autores gana a Libstdc++ y a Williams. Anderson gana cuando hay muchas escrituras sobre una sola pila (de 1,87× a 1,99×). El mejor caso de Autores se reproduce casi exacto.",
      "Folly rinde aquí mucho mejor que en el paper, y la diferencia ya existe con un solo hilo: no es contención ni un fallo del montaje. La causa sigue abierta.",
      "Con un millón de pilas, cuatro algoritmos empatan entre 53 y 57 Mop/s. Los contadores muestran que tres llegan al 89-93 % del techo de la RAM de este PC, que tiene un solo módulo."],
     "Episodio 7 de 14. Explica la figura 5: qué son n y u, por qué con más hilos casi todo se desploma y escenario por escenario quién gana. Dedica tiempo al misterio de Folly y al argumento del hilo único. Luego el empate con un millón de pilas y cómo se midió la RAM. Cierra anunciando el episodio 8, latencia y memoria."),
    (8, "latencia_y_memoria", "Latencia y memoria retenida",
     [("EXP", "### 6.2", "### 6.4")], "Análisis en profundidad", "Predeterminada",
     ["El load de Autores es el de menor latencia en los tres casos, aunque con contención gana por poco.",
      "Con contención, la latencia cambia mucho de una ronda a otra. Con 15 rondas, la afirmación 11 del paper dejó de confirmarse.",
      "El programa oficial de latencia se compila sin -mcx16, y así Williams lleva un candado escondido; corregido eso, con contención no es el peor. Anderson retiene hasta 19 960 bloques (469 KB) con 24 hilos; los demás no pasan del límite."],
     "Episodio 8 de 14. Explica la figura 6: qué miden load, store y store que libera, y qué cambia con contención. Cuenta cómo se descubrió el candado escondido de Williams y por qué cambió el veredicto. Insiste en que la latencia con contención es muy variable. Después, quién deja basura y cuánta. Cierra anunciando el episodio 9, la corrección."),
    (9, "correccion", "¿Es correcto? Detectores y la cota wait-free",
     [("EXP", "### 6.5", "### 6.6")], "Análisis en profundidad", "Predeterminada",
     ["ASan y TSan no encontraron errores en Autores. La versión ingenua los dispara enseguida, lo que demuestra que los detectores funcionaban.",
      "Romper a propósito las reglas del paper produce errores: con C = P aparecieron 42 348.",
      "La cota se cumple con margen: en 8 061 142 recargas forzadas hubo como mucho 8 intentos, con una cota de 32. Aun así, encontrar 0 errores no demuestra que no existan."],
     "Episodio 9 de 14. Explica qué vigilan ASan, UBSan y TSan con ejemplos sencillos, por qué la versión ingenua sirve de prueba del detector y qué pasa al romper las reglas del paper. Luego cómo se contaron los intentos de recarga. Recalca la diferencia entre no encontrar errores y demostrar que no los hay. Cierra anunciando el episodio 10."),
    (10, "sin_docker", "Sin Docker: el error escondido y la caché que se llena",
     [("EXP", "### 6.6", "### 6.7")], "Análisis en profundidad", "Más larga",
     ["Con los mismos programas oficiales, Docker no cambia nada: de 270 puntos, 259 cambian menos de un 10 %.",
      "El programa del equipo, bench.cpp, tenía compartición falsa: sus 10 pilas cabían en 2 líneas de caché. Al alinearlas, Autores pasa de 35 a 120 Mop/s.",
      "Con un millón de pilas, alinear frena entre un 24 % y un 27 %, porque las pilas dejan de caber en la caché L3: cada operación saca de la RAM entre 207 y 265 bytes más."],
     "Episodio 10 de 14. Cuenta cómo se midió sin Docker y la conclusión: Docker no cambia los resultados. Luego, como un caso de detectives, el hallazgo de la compartición falsa en el programa del equipo, y la sorpresa de que alinear frena con un millón de pilas, con la analogía del cajón y el almacén. Cierra anunciando el episodio 11, el veredicto."),
    (11, "veredicto", "El veredicto y los límites",
     [("EXP", "## Parte 7.", "## Parte 9.")], "Análisis en profundidad", "Predeterminada",
     ["Veredicto: de 15 afirmaciones, 9 se reproducen, 2 en parte, 3 no y 1 no se confirma.",
      "No se reproducen: que Autores gane a Folly, que gane a Anderson con muchas pilas y que su store sea el segundo con un hilo.",
      "Los límites: sin 4 sockets ni NUMA, recortes con sesgo, latencia ruidosa con contención, un solo módulo de RAM y preguntas abiertas como Folly o Williams entre clústeres."],
     "Episodio 11 de 14. Recorre las 15 afirmaciones del paper una por una con su veredicto, agrupando las que se reproducen, las de en parte y las que no. Luego las limitaciones, sin rodeos: máquina, método y conclusiones. El tono es de rendir cuentas con honestidad. Cierra anunciando los episodios 12 y 13, el juicio a la réplica."),
    (12, "juicio_1", "Juicio a la réplica (1): escala, método y Folly",
     [("DEF", "## 2.", "### Cargo 8.")], "Debate", "Predeterminada",
     ["En el lenguaje de la ACM, esto es una reproducción: otro equipo, con los artefactos de los autores.",
      "Cargos 1 a 7: la escala sin 4 sockets, la simulación de sockets, los recortes, Folly, la latencia ruidosa, Docker y los propios errores.",
      "Lo más fuerte de la defensa: la diferencia de Folly ya existe con un hilo, y Docker, los recortes y la distancia se midieron en vez de suponerse."],
     "Episodio 12 de 14, formato juicio. Una voz es el juez escéptico y la otra defiende la réplica con los datos. Empieza aclarando réplica frente a reproducción. Recorre los cargos 1 a 7 en orden: acusación, defensa y fallo del tribunal. Concede lo que la fuente concede. Cierra anunciando el episodio 13, la segunda parte del juicio."),
    (13, "juicio_2", "Juicio a la réplica (2): corrección, RAM, estadística y sentencia",
     [("DEF", "### Cargo 8.", "## 6.")], "Debate", "Predeterminada",
     ["Cargos 8 a 14: la corrección, la RAM, la selección de resultados, la estadística, la máquina sin controlar, el uso de IA y las erratas del informe.",
      "La sentencia: es una reproducción válida y honesta a escala de un PC; confirma la idea central y discute con datos lo que no reproduce.",
      "Mejoras por orden: corregir las erratas antes de exponer; luego un segundo módulo de RAM, intervalos de confianza y la figura 5 con la receta exacta; y más lejos, una máquina de varios sockets."],
     "Episodio 13 de 14, formato juicio. Una voz es el juez escéptico y la otra defiende la réplica. Recorre los cargos 8 a 14: acusación, defensa y fallo. Después lee la sentencia y el plan de mejoras por orden de prioridad. Concede lo que la fuente concede. Cierra anunciando el episodio 14, el ensayo para la exposición."),
    (14, "ensayo", "Ensayo para la exposición: las preguntas del jurado",
     [("DEF", "## 1.", "## 2."), ("DEF", "## 6.", "## 9.")], "Análisis en profundidad", "Predeterminada",
     ["La réplica contada en 20 segundos, en 1 minuto y en 3 minutos.",
      "Las 20 preguntas más probables del jurado, cada una con su respuesta corta.",
      "Las palabras que conviene evitar, qué decir en su lugar y las cifras clave para recordar."],
     "Episodio 14 de 14, ensayo. Una voz hace de jurado y lanza las preguntas de la fuente; la otra responde en corto, como en un examen oral, y añade un consejo. Empieza con la réplica en 20 segundos y termina con las frases que conviene evitar y las cifras clave. Despide la serie con una frase de resumen."),
]

COMUN = "Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. "


def tramo(texto, inicio, fin):
    """Las líneas desde el encabezado que empieza por `inicio` hasta el siguiente que empieza por `fin`, sin incluirlo."""
    lineas = texto.splitlines()
    a = next(i for i, l in enumerate(lineas) if l.startswith(inicio))
    b = next(i for i in range(a + 1, len(lineas)) if lineas[i].startswith(fin))
    return "\n".join(lineas[a:b]).strip()


def para_notebooklm(texto):
    """Las figuras pasan a una nota y los enlaces, a su texto: en audio no sirven y en otro archivo estarían rotos."""
    texto = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"*(Figura: \1)*", texto)
    return re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", texto)


def para_pdf(texto):
    """En el PDF se quedan las figuras y los enlaces externos; los internos apuntarían a otro documento."""
    return re.sub(r"(?<!!)\[([^\]]+)\]\((?!https?:)[^)]*\)", r"\1", texto)


def cabecera(n, titulo, esencial):
    prev = next((f"episodio {e[0]}, «{e[2]}»" for e in EPISODIOS if e[0] == n - 1), "es el primero de la serie")
    sig = next((f"episodio {e[0]}, «{e[2]}»" for e in EPISODIOS if e[0] == n + 1), "es el último de la serie")
    puntos = "\n".join(f"- {p}" for p in esencial)
    return (f"# Episodio {n} de {len(EPISODIOS)}: {titulo}\n\n"
            f"Serie «{SERIE}»: la réplica del paper «A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting» "
            f"(Euro-Par 2024), explicada para principiantes.\n\n"
            f"- **Episodio anterior:** {prev}.\n- **Episodio siguiente:** {sig}.\n\n"
            f"**Lo esencial de este episodio:**\n\n{puntos}\n\n---\n\n")


def mapa():
    filas = "\n".join(f"| {n} | {titulo} | {esencial[0]} |" for n, _, titulo, _, _, _, esencial, _ in EPISODIOS)
    return f"""# Mapa de la serie «{SERIE}»

Esta es una serie de {len(EPISODIOS)} episodios sobre una réplica científica. Explica, para principiantes, el paper **«A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting»** (de Wolff, Anderson, Keller y Seletskiy, Euro-Par 2024), y lo que pasó cuando un equipo de estudiantes repitió sus experimentos.

Este documento es solo el mapa. Cada episodio tiene su propia fuente, y cada episodio trata solo de su tema.

## El equipo

David Tamo Turpo, Jheremy Manuel Alvarez Astete y Diego Quispe Candelario. Repitieron los experimentos en un PC con un Intel Core Ultra 9 285 de 24 núcleos, con los programas oficiales que publicaron los autores, y además con un programa de pruebas propio.

## Los personajes

| Nombre en la serie | Qué es | En una frase |
|---|---|---|
| Autores | El algoritmo del paper | Lee con un solo `fetch_add`, que nunca falla: por eso es *wait-free* |
| Libstdc++ | `std::atomic<std::shared_ptr>` de GCC | Usa un candado: es simple, pero forma colas |
| Williams | El *split reference count* de Anthony Williams | Guarda puntero y cuenta en 16 bytes, con bucles de CAS |
| Folly | La biblioteca de Meta | Lo mete todo en 8 bytes, con bucles de CAS que pueden reintentar |
| Anderson | *Hazard pointers* con liberación diferida | Es rápido, pero retiene algo de memoria un rato |
| Mutex | Referencia del equipo; no está en el paper | Un candado clásico |
| Versión ingenua | La que está rota | Sirve para ver la carrera en acción |

## Las analogías que se repiten en toda la serie

- **La biblioteca.** Un objeto en memoria es un libro; su dirección, el estante; un puntero, una ficha que dice «estante 42».
- **La libreta pegada al libro** es el contador de referencias: cuánta gente lo usa. Quien la deja en 0 tira el libro a la **trituradora**, es decir, lo libera.
- **El tablón del vestíbulo** es el *atomic shared pointer*: la variable compartida que dice cuál es «el libro del día».
- **Marta y Beto.** Marta lee el tablón; Beto lo cambia y tritura el libro viejo. Si Beto lo tritura mientras Marta va de camino, hay un *use-after-free*.
- **El taco de vales prepagados** es la solución del paper: arrancar un vale lee la dirección y reserva el libro en un solo gesto.
- **El cuaderno que viaja** es una línea de caché que varios núcleos se pasan. Compartirlo es caro.

## Los episodios

| # | Título | De qué trata |
|---|---|---|
{filas}

## Cifras que aparecen en toda la serie

- **La máquina de la réplica:** Intel Core Ultra 9 285, 24 núcleos (8 rápidos, P, y 16 eficientes, E), un solo módulo de RAM.
- **La máquina del paper:** 4 procesadores Intel Xeon E7-8867, con 72 núcleos y 144 hilos.
- **Mediciones:** más de 14 000, ninguna fallida.
- **Veredicto:** de las 15 afirmaciones del paper, 9 se reproducen, 2 en parte, 3 no y 1 no se confirma.
- **n** es el número de pilas: pocas pilas significa mucha gente en poco sitio. **u** es el porcentaje de escrituras.
- **Mop/s** son millones de operaciones por segundo.
"""


def instrucciones(md_nombres):
    tabla = "\n".join(f"| {n} | {titulo} | `00_mapa_de_la_serie` y `{md_nombres[n]}` | {formato} | {duracion} |"
                      for n, _, titulo, _, formato, duracion, _, _ in EPISODIOS)
    prompts = "\n\n".join(f"### Episodio {n}: {titulo}\n\nFormato: **{formato}**. Duración: **{duracion}**. Fuentes: `00_mapa_de_la_serie` y `{md_nombres[n]}`.\n\n```text\n{COMUN}{prompt}\n```"
                          for n, _, titulo, _, formato, duracion, _, prompt in EPISODIOS)
    return f"""# Cómo generar el podcast con NotebookLM

**Este archivo no se sube a NotebookLM.** Es para ti: los pasos, qué fuentes marcar en cada episodio y el texto que hay que pegar en cada uno.

La serie se llama **«{SERIE}»** y tiene **{len(EPISODIOS)} episodios**: uno por cada parte de la réplica, más dos de juicio y uno de ensayo para la exposición.

## Qué hay en esta carpeta

| Carpeta o archivo | Qué es | ¿Se sube? |
|---|---|---|
| `fuentes_md/` | Una fuente por episodio, el mapa de la serie y el glosario | **Sí, estos** |
| `fuentes_pdf/` | Lo mismo en PDF, con las figuras dentro | Solo si NotebookLM rechaza los `.md`, o para leerlos tú |
| `00_COMO_GENERAR_EL_PODCAST.md` | Este archivo | No |
| `generar_fuentes.py` | Vuelve a crear todo a partir de `EXPLICACION.md` y `DEFENSA.md` | No |

**No subas al mismo cuaderno las guías antiguas del escritorio** (`VERSION_DUMMIE_TOTAL.md`, `guias_adversarios/` y las demás). Se escribieron antes de la réplica y a veces la contradicen: por ejemplo, dicen que Folly queda «derrotada ampliamente», cuando en la réplica empata o gana en 3 de 6 escenarios. Si mezclas fuentes que se contradicen, los presentadores repetirán las dos versiones.

## Paso a paso

1. **Crea un cuaderno** en [notebooklm.google.com](https://notebooklm.google.com) con el nombre «{SERIE}».
2. **Sube las fuentes:** arrastra los {len(EPISODIOS) + 2} archivos de `fuentes_md/` a «Añadir fuente». Son el mapa (`00`), los {len(EPISODIOS)} episodios y el glosario (`99`).
3. **Para cada episodio:**
   1. En la columna de fuentes, **desmarca todas** y marca solo las dos que indica la tabla: el mapa y la del episodio. Si quieres, marca también `99_glosario`.
   2. En el panel de Audio Overview, pulsa el **lápiz** (Personalizar).
   3. Elige el **formato** y la **duración** de la tabla, y el idioma **español**.
   4. Pega el **prompt** del episodio, más abajo, en el cuadro de instrucciones.
   5. Pulsa **Generar** y espera unos minutos.
   6. Descárgalo desde el menú de los tres puntos y ponle de nombre `Ep01 - Qué hicimos y qué salió.mp3`, y así con cada uno.
4. **Escúchalo antes de compartirlo.** Los presentadores a veces redondean o confunden cifras. Si un episodio sale mal, vuelve a generarlo: cada vez sale distinto.

**Límite diario.** La versión gratuita de NotebookLM limita cuántos audios puedes generar, y Google no publica la cifra exacta. Cuenta con hacer unos pocos al día y planifica la serie en varios días. NotebookLM te avisa cuando llegas al límite.

## Los episodios

| # | Título | Fuentes que marcar | Formato | Duración |
|---|---|---|---|---|
{tabla}

Los nombres cambian según el idioma de la interfaz. **Análisis en profundidad** es *Deep Dive*, **Resumen** es *Brief*, **Crítica** es *Critique* y **Debate** se llama igual. En la duración, **Más corta**, **Predeterminada** y **Más larga** son *Shorter*, *Default* y *Longer*. El formato Debate solo admite las dos primeras.

## Prompts para pegar

Cada prompt cabe en el cuadro de NotebookLM: tiene menos de {LIMITE_PROMPT} caracteres.

{prompts}

## Extras opcionales

**Tráiler de la serie** (formato **Resumen**, que dura uno o dos minutos). Fuentes: `00_mapa_de_la_serie` y `01_presentacion`.

```text
Tráiler en español latino neutro de la serie «{SERIE}»: de qué trata el paper, qué hizo el equipo y por qué vale la pena escuchar los 14 episodios. Solo una cifra: de 15 afirmaciones del paper, 9 se reproducen. Termina invitando al episodio 1.
```

**La réplica vista por un revisor** (formato **Crítica**). Fuentes: `00_mapa_de_la_serie` y `11_veredicto`.

```text
Habla en español latino neutro. Haz de revisor experto de la réplica: qué hace bien, qué limitaciones pesan más y qué mejoraría primero. Usa solo las cifras de la fuente y reconoce lo que la propia réplica ya admite.
```

## Si cambian los documentos

Si se actualizan `EXPLICACION.md` o `DEFENSA.md` en el repositorio de la réplica, vuelve a generar las fuentes con:

```bash
cd ~/Escritorio/podcast_notebooklm
python3 generar_fuentes.py
```

Después, en NotebookLM, borra las fuentes viejas y sube las nuevas.
"""


ESTILO = """
@page { size: A4; margin: 1.6cm; }
body { max-width: none; margin: 0; padding: 0; font-family: "DejaVu Serif", serif; font-size: 10.5pt; line-height: 1.45; }
h1 { font-size: 1.6em; } h2 { font-size: 1.3em; margin-top: 1.4em; } h3 { font-size: 1.1em; }
table { border-collapse: collapse; width: 100%; font-size: 0.9em; margin: 0.8em 0; }
th, td { border: 1px solid #bbb; padding: 3px 6px; vertical-align: top; }
th { background: #eee; }
img { max-width: 100%; }
pre, code { font-family: "DejaVu Sans Mono", monospace; font-size: 0.88em; }
pre { white-space: pre-wrap; background: #f6f6f6; padding: 6px; }
blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 0.8em; color: #333; }
"""


def a_pdf(texto, nombre, dir_pdf, chrome):
    """Markdown → HTML con pandoc, con las figuras dentro, y HTML → PDF con Chrome sin ventana.
    LuaLaTeX no carga sus fuentes en este equipo; Chrome muestra bien los acentos, los símbolos y las tablas."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "estilo.css").write_text(ESTILO, encoding="utf-8")
        (tmp / "doc.md").write_text(texto, encoding="utf-8")
        r = subprocess.run(["pandoc", str(tmp / "doc.md"), "-s", "--embed-resources", "-c", str(tmp / "estilo.css"),
                            "--metadata", f"pagetitle={nombre}", "--metadata", "lang=es", "--resource-path", str(REPLICA),
                            "-o", str(tmp / "doc.html")], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"Falló el HTML de {nombre}:\n{r.stderr[-2000:]}")
        r = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={tmp / 'chrome'}",
                            f"--print-to-pdf={dir_pdf / (nombre + '.pdf')}", (tmp / "doc.html").as_uri()],
                           capture_output=True, text=True, timeout=180)
        if not (dir_pdf / f"{nombre}.pdf").exists():
            sys.exit(f"Falló el PDF de {nombre}:\n{r.stderr[-2000:]}")


def main():
    textos = {k: v.read_text(encoding="utf-8") for k, v in FUENTES.items()}
    dir_md, dir_pdf = AQUI / "fuentes_md", AQUI / "fuentes_pdf"
    for d in (dir_md, dir_pdf):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir()

    documentos = {"00_mapa_de_la_serie": mapa()}
    md_nombres = {}
    for n, archivo, titulo, tramos, _, _, esencial, prompt in EPISODIOS:
        largo = len(COMUN + prompt)
        if largo > LIMITE_PROMPT:
            sys.exit(f"El prompt del episodio {n} tiene {largo} caracteres; el límite es {LIMITE_PROMPT}")
        nombre = f"{n:02d}_{archivo}"
        md_nombres[n] = nombre
        cuerpo = "\n\n".join(tramo(textos[f], a, b) for f, a, b in tramos)
        documentos[nombre] = cabecera(n, titulo, esencial) + cuerpo + "\n"
    documentos["99_glosario"] = ("# Glosario de la serie\n\nLas palabras técnicas que aparecen en los episodios, explicadas en una o dos frases.\n\n"
                                 + tramo(textos["EXP"], "## Parte 10.", "## Referencias") + "\n")

    chrome = next(filter(None, map(shutil.which, ("google-chrome", "chromium", "chromium-browser"))), None)
    hay_pdf = shutil.which("pandoc") and chrome
    for nombre, texto in documentos.items():
        (dir_md / f"{nombre}.md").write_text(para_notebooklm(texto), encoding="utf-8")
        if hay_pdf:
            a_pdf(para_pdf(texto), nombre, dir_pdf, chrome)
        print(f"{nombre}: {len(texto.split())} palabras", flush=True)
    (AQUI / "00_COMO_GENERAR_EL_PODCAST.md").write_text(instrucciones(md_nombres), encoding="utf-8")
    print(f"Listo: {len(documentos)} fuentes" + (" en .md y .pdf" if hay_pdf else " en .md (sin PDF: falta pandoc o Chrome)"))


if __name__ == "__main__":
    main()

# Cómo generar el podcast con NotebookLM

**Este archivo no se sube a NotebookLM.** Es para ti: los pasos, qué fuentes marcar en cada episodio y el texto que hay que pegar en cada uno.

La serie se llama **«Leer sin que te quiten el libro»** y tiene **14 episodios**: uno por cada parte de la réplica, más dos de juicio y uno de ensayo para la exposición.

## Qué hay en esta carpeta

| Carpeta o archivo | Qué es | ¿Se sube? |
|---|---|---|
| `fuentes_md/` | Una fuente por episodio, el mapa de la serie y el glosario | **Sí, estos** |
| `fuentes_pdf/` | Lo mismo en PDF, con las figuras dentro | Solo si NotebookLM rechaza los `.md`, o para leerlos tú |
| `00_COMO_GENERAR_EL_PODCAST.md` | Este archivo | No |
| `generar_fuentes.py` | Vuelve a crear todo a partir de `EXPLICACION.md` y `DEFENSA.md` | No |

**No subas al mismo cuaderno las guías antiguas del escritorio** (`VERSION_DUMMIE_TOTAL.md`, `guias_adversarios/` y las demás). Se escribieron antes de la réplica y a veces la contradicen: por ejemplo, dicen que Folly queda «derrotada ampliamente», cuando en la réplica empata o gana en 3 de 6 escenarios. Si mezclas fuentes que se contradicen, los presentadores repetirán las dos versiones.

## Paso a paso

1. **Crea un cuaderno** en [notebooklm.google.com](https://notebooklm.google.com) con el nombre «Leer sin que te quiten el libro».
2. **Sube las fuentes:** arrastra los 16 archivos de `fuentes_md/` a «Añadir fuente». Son el mapa (`00`), los 14 episodios y el glosario (`99`).
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
| 1 | Qué hicimos y qué salió | `00_mapa_de_la_serie` y `01_presentacion` | Análisis en profundidad | Predeterminada |
| 2 | La carrera entre leer y liberar | `00_mapa_de_la_serie` y `02_el_problema` | Análisis en profundidad | Más larga |
| 3 | Los rivales: candados, cuentas dobles y basura retrasada | `00_mapa_de_la_serie` y `03_los_rivales` | Análisis en profundidad | Más larga |
| 4 | La solución del paper: el taco de vales | `00_mapa_de_la_serie` y `04_la_solucion` | Análisis en profundidad | Más larga |
| 5 | Cómo se hizo la réplica, y cuánto fiarse | `00_mapa_de_la_serie` y `05_el_metodo` | Análisis en profundidad | Predeterminada |
| 6 | Simular 4 procesadores con un solo PC | `00_mapa_de_la_serie` y `06_simular_4_xeon` | Análisis en profundidad | Más larga |
| 7 | Rendimiento: quién gana, y el misterio de Folly | `00_mapa_de_la_serie` y `07_rendimiento` | Análisis en profundidad | Más larga |
| 8 | Latencia y memoria retenida | `00_mapa_de_la_serie` y `08_latencia_y_memoria` | Análisis en profundidad | Predeterminada |
| 9 | ¿Es correcto? Detectores y la cota wait-free | `00_mapa_de_la_serie` y `09_correccion` | Análisis en profundidad | Predeterminada |
| 10 | Sin Docker: el error escondido y la caché que se llena | `00_mapa_de_la_serie` y `10_sin_docker` | Análisis en profundidad | Más larga |
| 11 | El veredicto y los límites | `00_mapa_de_la_serie` y `11_veredicto` | Análisis en profundidad | Predeterminada |
| 12 | Juicio a la réplica (1): escala, método y Folly | `00_mapa_de_la_serie` y `12_juicio_1` | Debate | Predeterminada |
| 13 | Juicio a la réplica (2): corrección, RAM, estadística y sentencia | `00_mapa_de_la_serie` y `13_juicio_2` | Debate | Predeterminada |
| 14 | Ensayo para la exposición: las preguntas del jurado | `00_mapa_de_la_serie` y `14_ensayo` | Análisis en profundidad | Predeterminada |

Los nombres cambian según el idioma de la interfaz. **Análisis en profundidad** es *Deep Dive*, **Resumen** es *Brief*, **Crítica** es *Critique* y **Debate** se llama igual. En la duración, **Más corta**, **Predeterminada** y **Más larga** son *Shorter*, *Default* y *Longer*. El formato Debate solo admite las dos primeras.

## Prompts para pegar

Cada prompt cabe en el cuadro de NotebookLM: tiene menos de 500 caracteres.

### Episodio 1: Qué hicimos y qué salió

Formato: **Análisis en profundidad**. Duración: **Predeterminada**. Fuentes: `00_mapa_de_la_serie` y `01_presentacion`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 1 de 14. Presenta el paper (Euro-Par 2024), al equipo y qué significa reproducir un experimento. Cuenta qué se hizo y el marcador: de 15 afirmaciones, 9 se reproducen, 2 en parte, 3 no y 1 no se confirma. Sin detalles técnicos: llegan después. Cierra anunciando el episodio 2, la carrera entre leer y liberar.
```

### Episodio 2: La carrera entre leer y liberar

Formato: **Análisis en profundidad**. Duración: **Más larga**. Fuentes: `00_mapa_de_la_serie` y `02_el_problema`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 2 de 14. Explica la carrera read-reclaim con la historia de Marta y Beto en la biblioteca, paso a paso. Luego el vocabulario: operaciones atómicas, CAS, fetch_add, wait-free frente a lock-free y por qué compartir una línea de caché es caro. Termina con las tres familias de solución. Cierra anunciando el episodio 3, los rivales.
```

### Episodio 3: Los rivales: candados, cuentas dobles y basura retrasada

Formato: **Análisis en profundidad**. Duración: **Más larga**. Fuentes: `00_mapa_de_la_serie` y `03_los_rivales`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 3 de 14. Presenta uno a uno a los rivales del paper: la versión ingenua, Mutex, Libstdc++, Williams, Folly y Anderson. De cada uno: la idea en una frase, su analogía, cómo lee y cómo escribe, y su punto débil. Termina con la tabla que los compara. Cierra anunciando el episodio 4, la solución del paper.
```

### Episodio 4: La solución del paper: el taco de vales

Formato: **Análisis en profundidad**. Duración: **Más larga**. Fuentes: `00_mapa_de_la_serie` y `04_la_solucion`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 4 de 14, el central. Explica el algoritmo del paper con la historia del taco de vales: la regla de oro, cómo caben dirección y vales en 64 bits, qué pasa al recargar el taco y por qué la cota es de P intentos. Repite la idea de varias formas. Cierra anunciando el episodio 5, cómo se hizo la réplica.
```

### Episodio 5: Cómo se hizo la réplica, y cuánto fiarse

Formato: **Análisis en profundidad**. Duración: **Predeterminada**. Fuentes: `00_mapa_de_la_serie` y `05_el_metodo`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 5 de 14. Explica qué midieron los autores, qué se usó aquí y cada adaptación con su porqué: hilos divididos entre 6, 2 s en vez de 10 y orden aleatorio. Después, cómo se comprobó que recortar no cambia las conclusiones y por qué una diferencia pequeña es un empate. Cierra anunciando el episodio 6, simular 4 procesadores.
```

### Episodio 6: Simular 4 procesadores con un solo PC

Formato: **Análisis en profundidad**. Duración: **Más larga**. Fuentes: `00_mapa_de_la_serie` y `06_simular_4_xeon`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 6 de 14. Explica por qué no se usó una máquina virtual, cómo se midieron las distancias entre núcleos y el experimento de dosis-respuesta con 4 hilos. Cuenta la rareza de Williams entre clústeres como una historia de detectives. Deja claro qué demuestra la simulación y qué no. Cierra anunciando el episodio 7, el rendimiento.
```

### Episodio 7: Rendimiento: quién gana, y el misterio de Folly

Formato: **Análisis en profundidad**. Duración: **Más larga**. Fuentes: `00_mapa_de_la_serie` y `07_rendimiento`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 7 de 14. Explica la figura 5: qué son n y u, por qué con más hilos casi todo se desploma y escenario por escenario quién gana. Dedica tiempo al misterio de Folly y al argumento del hilo único. Luego el empate con un millón de pilas y cómo se midió la RAM. Cierra anunciando el episodio 8, latencia y memoria.
```

### Episodio 8: Latencia y memoria retenida

Formato: **Análisis en profundidad**. Duración: **Predeterminada**. Fuentes: `00_mapa_de_la_serie` y `08_latencia_y_memoria`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 8 de 14. Explica la figura 6: qué miden load, store y store que libera, y qué cambia con contención. Cuenta cómo se descubrió el candado escondido de Williams y por qué cambió el veredicto. Insiste en que la latencia con contención es muy variable. Después, quién deja basura y cuánta. Cierra anunciando el episodio 9, la corrección.
```

### Episodio 9: ¿Es correcto? Detectores y la cota wait-free

Formato: **Análisis en profundidad**. Duración: **Predeterminada**. Fuentes: `00_mapa_de_la_serie` y `09_correccion`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 9 de 14. Explica qué vigilan ASan, UBSan y TSan con ejemplos sencillos, por qué la versión ingenua sirve de prueba del detector y qué pasa al romper las reglas del paper. Luego cómo se contaron los intentos de recarga. Recalca la diferencia entre no encontrar errores y demostrar que no los hay. Cierra anunciando el episodio 10.
```

### Episodio 10: Sin Docker: el error escondido y la caché que se llena

Formato: **Análisis en profundidad**. Duración: **Más larga**. Fuentes: `00_mapa_de_la_serie` y `10_sin_docker`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 10 de 14. Cuenta cómo se midió sin Docker y la conclusión: Docker no cambia los resultados. Luego, como un caso de detectives, el hallazgo de la compartición falsa en el programa del equipo, y la sorpresa de que alinear frena con un millón de pilas, con la analogía del cajón y el almacén. Cierra anunciando el episodio 11, el veredicto.
```

### Episodio 11: El veredicto y los límites

Formato: **Análisis en profundidad**. Duración: **Predeterminada**. Fuentes: `00_mapa_de_la_serie` y `11_veredicto`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 11 de 14. Recorre las 15 afirmaciones del paper una por una con su veredicto, agrupando las que se reproducen, las de en parte y las que no. Luego las limitaciones, sin rodeos: máquina, método y conclusiones. El tono es de rendir cuentas con honestidad. Cierra anunciando los episodios 12 y 13, el juicio a la réplica.
```

### Episodio 12: Juicio a la réplica (1): escala, método y Folly

Formato: **Debate**. Duración: **Predeterminada**. Fuentes: `00_mapa_de_la_serie` y `12_juicio_1`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 12 de 14, formato juicio. Una voz es el juez escéptico y la otra defiende la réplica con los datos. Empieza aclarando réplica frente a reproducción. Recorre los cargos 1 a 7 en orden: acusación, defensa y fallo del tribunal. Concede lo que la fuente concede. Cierra anunciando el episodio 13, la segunda parte del juicio.
```

### Episodio 13: Juicio a la réplica (2): corrección, RAM, estadística y sentencia

Formato: **Debate**. Duración: **Predeterminada**. Fuentes: `00_mapa_de_la_serie` y `13_juicio_2`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 13 de 14, formato juicio. Una voz es el juez escéptico y la otra defiende la réplica. Recorre los cargos 8 a 14: acusación, defensa y fallo. Después lee la sentencia y el plan de mejoras por orden de prioridad. Concede lo que la fuente concede. Cierra anunciando el episodio 14, el ensayo para la exposición.
```

### Episodio 14: Ensayo para la exposición: las preguntas del jurado

Formato: **Análisis en profundidad**. Duración: **Predeterminada**. Fuentes: `00_mapa_de_la_serie` y `14_ensayo`.

```text
Español latino neutro (ustedes, no vosotros), para principiantes, con la analogía de la biblioteca. Cifras exactas de la fuente, sin inventar otras. Episodio 14 de 14, ensayo. Una voz hace de jurado y lanza las preguntas de la fuente; la otra responde en corto, como en un examen oral, y añade un consejo. Empieza con la réplica en 20 segundos y termina con las frases que conviene evitar y las cifras clave. Despide la serie con una frase de resumen.
```

## Extras opcionales

**Tráiler de la serie** (formato **Resumen**, que dura uno o dos minutos). Fuentes: `00_mapa_de_la_serie` y `01_presentacion`.

```text
Tráiler en español latino neutro de la serie «Leer sin que te quiten el libro»: de qué trata el paper, qué hizo el equipo y por qué vale la pena escuchar los 14 episodios. Solo una cifra: de 15 afirmaciones del paper, 9 se reproducen. Termina invitando al episodio 1.
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

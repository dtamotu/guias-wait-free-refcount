# Mapa de la serie «Leer sin que te quiten el libro»

Esta es una serie de 14 episodios sobre una réplica científica. Explica, para principiantes, el paper **«A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting»** (de Wolff, Anderson, Keller y Seletskiy, Euro-Par 2024), y lo que pasó cuando un equipo de estudiantes repitió sus experimentos.

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
| 1 | Qué hicimos y qué salió | El equipo repitió el paper con los programas oficiales de los autores en un PC con un Intel Core Ultra 9 285, con y sin Docker: más de 14 000 mediciones, ninguna fallida. |
| 2 | La carrera entre leer y liberar | Leer un puntero compartido y apuntarse como usuario son dos pasos. Entre los dos, otro hilo puede liberar el objeto: es la carrera read-reclaim, que acaba en un use-after-free. |
| 3 | Los rivales: candados, cuentas dobles y basura retrasada | Mutex y Libstdc++ usan un candado: es simple, pero forma colas. |
| 4 | La solución del paper: el taco de vales | El tablón guarda un taco de vales prepagados. Arrancar un vale lee la dirección y reserva el libro en un solo gesto: un fetch_add que nunca falla. |
| 5 | Cómo se hizo la réplica, y cuánto fiarse | Se usaron los programas oficiales del artefacto de Zenodo, con su MD5 comprobado: es el código de los autores, no una copia. |
| 6 | Simular 4 procesadores con un solo PC | Una máquina virtual con 4 nodos NUMA sería un decorado. Se usaron distancias reales: 35 ns dentro de un clúster, 47 entre clústeres y 86 entre núcleos P. |
| 7 | Rendimiento: quién gana, y el misterio de Folly | Autores gana a Libstdc++ y a Williams. Anderson gana cuando hay muchas escrituras sobre una sola pila (de 1,87× a 1,99×). El mejor caso de Autores se reproduce casi exacto. |
| 8 | Latencia y memoria retenida | El load de Autores es el de menor latencia en los tres casos, aunque con contención gana por poco. |
| 9 | ¿Es correcto? Detectores y la cota wait-free | ASan y TSan no encontraron errores en Autores. La versión ingenua los dispara enseguida, lo que demuestra que los detectores funcionaban. |
| 10 | Sin Docker: el error escondido y la caché que se llena | Con los mismos programas oficiales, Docker no cambia nada: de 270 puntos, 259 cambian menos de un 10 %. |
| 11 | El veredicto y los límites | Veredicto: de 15 afirmaciones, 9 se reproducen, 2 en parte, 3 no y 1 no se confirma. |
| 12 | Juicio a la réplica (1): escala, método y Folly | En el lenguaje de la ACM, esto es una reproducción: otro equipo, con los artefactos de los autores. |
| 13 | Juicio a la réplica (2): corrección, RAM, estadística y sentencia | Cargos 8 a 14: la corrección, la RAM, la selección de resultados, la estadística, la máquina sin controlar, el uso de IA y las erratas del informe. |
| 14 | Ensayo para la exposición: las preguntas del jurado | La réplica contada en 20 segundos, en 1 minuto y en 3 minutos. |

## Cifras que aparecen en toda la serie

- **La máquina de la réplica:** Intel Core Ultra 9 285, 24 núcleos (8 rápidos, P, y 16 eficientes, E), un solo módulo de RAM.
- **La máquina del paper:** 4 procesadores Intel Xeon E7-8867, con 72 núcleos y 144 hilos.
- **Mediciones:** más de 14 000, ninguna fallida.
- **Veredicto:** de las 15 afirmaciones del paper, 9 se reproducen, 2 en parte, 3 no y 1 no se confirma.
- **n** es el número de pilas: pocas pilas significa mucha gente en poco sitio. **u** es el porcentaje de escrituras.
- **Mop/s** son millones de operaciones por segundo.

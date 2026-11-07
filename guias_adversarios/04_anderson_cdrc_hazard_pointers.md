# Guía de Adversario: Anderson et al. (CDRC / Hazard Pointers)

> **Paper de Referencia:** *A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting* (de Wolff et al., Euro-Par 2024).  
> **Trabajos Previos del Rival:** Anderson, Blelloch y Wei (PLDI 2021, PLDI 2022; CppCon 2023).  
> **Clasificación del Rival:** Reclamación Segura de Memoria (SMR) con Reclamación Diferida (*Deferred Reclamation*) y Punteros de Riesgo (*Hazard Pointers*).

---

## 1. Explicación Detallada (Nivel Técnico Avanzado)

### 1.1. Arquitectura de CDRC (Concurrent Deferred Reference Counting)
Daniel Anderson et al. propusieron abordar las carreras *read-reclaim* cambiando el paradigma: en lugar de obligar al lector a incrementar el contador de referencias inmediatamente en el bloque de control compartido, utilizan técnicas de **Reclamación Segura de Memoria (SMR)** mediante **Punteros de Riesgo (*Hazard Pointers*)**:
1. **Ranuras por Hilo:** Cada hilo posee un arreglo local de punteros de riesgo publicados globalmente.
2. **Lectura por Instantánea (*Snapshot*):** Cuando un hilo lector quiere acceder al objeto, lee el puntero y lo anota en su ranura privada de Hazard Pointer. Esto actúa como un escudo protector: ningún escritor puede destruir el objeto mientras la dirección del objeto figure en el hazard pointer de algún hilo activo.
3. **Lecturas Puras:** El lector no modifica el bloque de control del objeto. Esto elimina el tráfico de invalidación de caché en el bloque de control para las lecturas puras.

### 1.2. El Coste Ineludible: Sobrecoste de Memoria y Retención Indefinida
A pesar de su velocidad en lecturas, CDRC y los Hazard Pointers sufren de graves limitaciones arquitectónicas que el paper de de Wolff et al. resuelve por completo:
* **Reclamación Diferida (*Deferred Reclamation*):** Cuando un escritor retira la última referencia oficial a un objeto ($rc=0$), el objeto **NO se destruye en ese instante**. En su lugar, se añade a una *lista de retiro* (*retire list*) local o global.
* **Sobrecoste Espacial (*Space Overhead*):** La memoria de los objetos muertos permanece ocupada indefinidamente hasta que se ejecute una fase periódica de escaneo de los hazard pointers (inspección de todas las ranuras de todos los hilos).
* **Violación de Semánticas RAII y Modificación en el Sitio:**
  * En C++ idiomático, cuando `rc == 1`, el poseedor sabe con certeza matemática que es el único dueño y puede modificar el objeto *in-place* sin copiarlo (*copy-on-write optimization*).
  * Con reclamación diferida, un objeto puede tener $rc=1$ pero estar siendo observado por un hazard pointer de un hilo rezagado, rompiendo esta optimización o requiriendo sincronizaciones lentas adicionales.
  * Los destructores de los objetos se ejecutan fuera de tiempo, lo que puede provocar retención indebida de recursos críticos (descriptores de archivos, sockets, cerrojos).

### 1.3. Comparación en los Benchmarks del Paper (Figura 5 y 6)
* **Baja Contención ($n$ grande o $u$ bajo):** El algoritmo de de Wolff et al. (**Ours**) es **más rápido que Anderson** gracias a que su `load` es una sola instrucción `fetch_sub` sin sobrecarga de gestión de ranuras de hazard pointers.
* **Alta Contención con Escrituras ($n=1$, $u=50\%$):** Anderson supera a de Wolff et al. porque en Anderson las lecturas no escriben en la celda del puntero, permitiendo que los escritores completen sus swaps sin que los lectores les ensucien la palabra de memoria.
* **Latencia ($p = 56$ hilos):**
  * Mediana de `load`: **Ours = 1.14 µs** frente a **Anderson = 2.58 µs** (el Autor es más de 2× más rápido).
* **Consumo de Memoria:** El Autor garantiza **cero sobrecoste de espacio** (*Zero Space Overhead*). Anderson acumula objetos y bloques de memoria basura en espera de retiro.

---

## 2. Versión Dummie (Explicación para Principiantes)

### 2.1. La Analogía del Mundo Real: "El Basurero Perezoso y la Casa Llena de Cajas"
Imagina el dilema de botar la basura en tu casa:
* **Cómo trabaja el Autor (de Wolff et al.):** En cuanto terminas una caja de pizza y nadie más la quiere, vas directamente al incinerador y la quemas en ese mismo segundo. Tu casa está 100% limpia todo el tiempo. Cero cajas estorbando.
* **Cómo trabaja Anderson (CDRC):** En vez de pararte a botar la caja de pizza, la tiras al piso en un rincón del pasillo. Dices: *"Bueno, luego vendrá el camión a revisar si alguien la quiere y se la llevará"*. 
* **El problema:** Al cabo de unas horas, el pasillo está atiborrado de 300 cajas de pizza vacías. Tu casa se queda sin espacio y huele mal (tu memoria RAM se satura de objetos muertos que no se pueden borrar todavía).

### 2.2. Resumen "En Cristiano" (3 Balas Clave)
1. **¿Qué hace?** Para no frenar las lecturas, los hilos se ponen un papelito en la frente que dice: *"¡Oigan, estoy mirando este objeto, no lo borren todavía!"*.
2. **¿Por qué es malo?** Retrasa la destrucción de los objetos. La memoria RAM se llena de basura acumulada en listas de espera y no se destruyen las cosas en el momento exacto en que deben destruirse.
3. **¿Qué inventó el autor para vencerlo?** Una técnica con **cero basura acumulada**: el objeto se destruye en el nanosegundo exacto en que el contador llega a cero, sin listas de espera, sin gastar un solo megabyte de memoria adicional y con lecturas súper rápidas.

### 2.3. Preguntas Tontas que Todos nos Hacemos
* *¿Si Anderson es tan rápido cuando hay muchas escrituras, por qué el autor no lo copió?*  
  Porque en sistemas embebidos, videojuegos y computación de alto rendimiento, la memoria RAM es sagrada. No puedes darte el lujo de acumular gigabytes de objetos muertos en listas de espera perezosas.
* *¿Qué significa "Cero Sobrecoste de Memoria"?*  
  Significa que el algoritmo del autor no gasta ni un solo byte de memoria extra más allá de lo que ocupa el objeto y su contador. No hay arreglos auxiliares por hilo ni colas de retiro.

### 2.4. Veredicto Dummie
> **Calificación:** 8 / 10 en velocidad bruta de lectura, pero 4 / 10 en disciplina de memoria.  
> **Veredicto:** Un adversario muy digno y extremadamente rápido, pero a costa de desperdiciar memoria RAM y romper la regla de oro de C++ de "destruir inmediatamente lo que ya no se usa".

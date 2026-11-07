# Guía de Adversario: Libstdc++ (GCC `std::atomic<std::shared_ptr<T>>`)

> **Paper de Referencia:** *A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting* (de Wolff, Anderson, Keller y Seletskiy, Euro-Par 2024).  
> **Clasificación del Rival:** Estándar de la industria C++20 / Implementación basada en cerrojos internos.

---

## 1. Explicación Detallada (Nivel Técnico Avanzado)

### 1.1. Arquitectura y Fundamentos Teóricos
El estándar C++20 introdujo la especialización `std::atomic<std::shared_ptr<T>>` para permitir el acceso concurrente seguro sobre punteros con conteo de referencias. Sin embargo, la especificación del estándar **no exige** que la implementación sea libre de bloqueos (*lock-free*), permitiendo que `atomic<shared_ptr<T>>::is_lock_free()` devuelva `false`.

En la biblioteca estándar de GCC (**libstdc++**), la implementación no utiliza instrucciones atómicas libres de espera para manipular simultáneamente el puntero y el bloque de control. En su lugar, emplea un conjunto de **candados internos** (*spinlocks* o cerrojos livianos mapeados por hash sobre la dirección de la celda compartida, o integrados directamente en el encapsulado del puntero atómico).

### 1.2. Primitivas de Hardware y Mecanismos de Sincronización
* **Estructura Interna:** Cada operación `load()`, `store()` o `compare_exchange()` adquiere un cerrojo de exclusión mutua antes de tocar el puntero o alterar los contadores del bloque de control (`_Sp_counted_base`).
* **Instrucciones:** En arquitecturas x86-64, la adquisición del cerrojo suele involucrar un bucle `lock bts` o `lock cmpxchg` con pausas `_mm_pause()`, y en caso de alta contención, una llamada al sistema `futex` (en Linux) para suspender el hilo.
* **Garantía de Progreso:** **Bloqueante (*Blocking*)**. No es *lock-free* ni mucho menos *wait-free*.

### 1.3. Consecuencias Formales y Comportamiento ante Contención
1. **Inversión de Prioridades e Inanición:** Si un hilo que posee el cerrojo interno es desalojado por el planificador del sistema operativo (por ejemplo, debido al agotamiento de su quantum de tiempo, una interrupción o un fallo de página), **todos los demás hilos que intenten leer o escribir sobre ese puntero quedan congelados** esperando.
2. **Degradación del Throughput:** A medida que aumenta el número de hilos, los núcleos compiten agresivamente por la misma línea de caché que contiene la palabra del cerrojo, provocando una tormenta de invalidaciones de caché (*cache-line bouncing*).

### 1.4. Desmontaje en los Benchmarks (Paper y Réplica Local)
* **Rendimiento (1 pila, 1% actualizaciones, 12 hilos - Intel i5-10400):**
  * Autores (*de Wolff et al.*): **39.13 Mop/s** (hasta 44.8 Mop/s con 1 hilo).
  * Libstdc++: **1.58 Mop/s**.  
  * *Resultado:* El algoritmo del autor es **~25 veces más rápido** que Libstdc++ en el entorno local. Con 144 hilos en el paper, la diferencia se ensancha todavía más.
* **Latencia de `load` (56 hilos en el paper vs 12 hilos en réplica):**
  * Paper (56 hilos, Xeon w7-3465X): Mediana de Libstdc++ = **99.7 µs** frente a **1.14 µs** del Autor.
  * Réplica local (12 hilos): Mediana de Libstdc++ = **3.06 µs** (3060 ns) frente a **0.27 µs** (269 ns) del Autor. El percentil 99 ($p99$) de Libstdc++ alcanza **16.0 µs**.

---

## 2. Versión Dummie (Explicación para Principiantes)

### 2.1. La Analogía del Mundo Real: "La Cabina Telefónica con Candado"
Imagina una plaza pública donde hay una cabina telefónica que tiene una pizarra con un número anotado (el puntero) y una libreta de firmas (el contador de cuánta gente lo está usando):
* **Cómo trabaja Libstdc++:** El creador de la cabina le puso un candado pesado con una sola llave. Para leer el número, tienes que hacer fila, pedir la llave, entrar a la cabina, cerrar la puerta con cerrojo, leer el número, firmar la libreta, abrir la puerta y devolver la llave.
* **El desastre:** Si el chico que tiene la llave se distrae amarrándose los zapatos adentro de la cabina o le da un calambre, las 50 personas que están en la fila afuera bajo la lluvia se quedan completamente congeladas sin poder hacer nada.

### 2.2. Resumen "En Cristiano" (3 Balas Clave)
1. **¿Qué hace?** Protege el puntero compartido usando candados tradicionales dentro de la biblioteca oficial de C++ de GCC.
2. **¿Por qué es malo?** Porque los candados detienen a los hilos. Si un hilo se frena, todos los demás se estrellan detrás de él, haciendo que la computadora ande a tirones.
3. **¿Qué inventó el autor para vencerlo?** Un sistema donde **no hay cabina ni candado**: el número está a la vista de todos con un talonario de tickets pre-pagados. Cualquier hilo arranca un ticket en un nanosegundo sin frenar a nadie.

### 2.3. Preguntas Tontas que Todos nos Hacemos
* *¿Si es de la biblioteca estándar de C++, no debería ser lo mejor del mundo?*  
  No siempre. La biblioteca estándar prioriza que funcione en cualquier procesador del planeta sin romperse, aunque sea lento. Por eso pusieron un candado seguro en vez de un algoritmo de alta tecnología sin bloqueos.
* *¿Qué pasa si mi programa usa `std::atomic<std::shared_ptr>` en un videojuego o servidor?*  
  Si tienes muchos hilos leyendo a la vez, tu servidor o videojuego tendrá caídas de fotogramas (*frame drops*) y picos de lag repentinos cuando varios hilos choquen por el mismo candado.

### 2.4. Veredicto Dummie
> **Calificación:** 3 / 10 en velocidad concurrente.  
> **Veredicto:** Es seguro y fácil de usar, pero es el rival más lento de todos cuando hay muchos núcleos trabajando juntos.

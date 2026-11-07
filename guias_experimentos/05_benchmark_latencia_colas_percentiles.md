# Guía de Experimento 5: Benchmark de Latencia y Estudio de Percentiles

> **Archivo de Código:** `codigo/bench.cpp` (Modo `latencia`)  
> **Objetivo Científico:** Medir con precisión de ciclo de reloj (nanosegundos) el tiempo individual que toma ejecutar cada operación (`load`, `store`, `store & reclaim`) y contrastar las distribuciones de latencia para desmentir el mito de la mediana mediante el análisis del percentil 99 ($p99$).

---

## 1. Explicación Detallada (Nivel Técnico Avanzado)

### 1.1. Metodología de Medición en Nanosegundos con Hardware RDTSC
Medir operaciones que toman menos de 300 nanosegundos requiere técnicas de bajo nivel para no perturbar la medición:
* **Instrucción `__rdtsc`:** Lee el contador de sellos de tiempo del procesador (*Time Stamp Counter*).
* **Serialización con `_mm_lfence()`:** Evita que el procesador reordene instrucciones especulativamente fuera del bloque de medición:
  ```cpp
  static inline uint64_t tsc() { 
      _mm_lfence(); 
      uint64_t t = __rdtsc(); 
      _mm_lfence(); 
      return t; 
  }
  ```
* **Calibración de Frecuencia:** `ns_por_tick()` mide cuántos ciclos transcurren en una ventana de 300 ms de `std::chrono::steady_clock` para calcular los nanosegundos reales por ciclo de reloj.
* **Técnica de Lotes ($B=16$ con $p=1$):** Cuando corre un solo hilo, la operación dura apenas ~15–20 ns, lo cual es inferior al propio costo de leer el reloj (~46 ns). Para evitar medir el costo del reloj, se ejecutan 16 operaciones seguidas y se divide entre 16.
* **Operaciones Evaluadas:**
  1. `load`: Adquisición de un puntero compartido.
  2. `store`: Reemplazo del puntero por otro objeto pre-asignado (sin invocar al destructor).
  3. `store & reclaim`: Reemplazo y destrucción inmediata del objeto anterior en memoria.

### 1.2. Tabla de Resultados Empíricos (12 hilos, 200,000 muestras)
Datos oficiales de la réplica en Intel i5-10400 (`capturas/07_latencia.txt` y `latencia.csv`):

```text
====================================================================================================
Implementación   Operación           Percentil 1   Mediana (p50)   Percentil 75   Percentil 99 (p99)
====================================================================================================
Autores          load                   194.2 ns        269.2 ns       374.3 ns             830.4 ns
Libstdc++ (GCC)  load                  1893.3 ns       3061.1 ns      4210.8 ns           16012.3 ns
Williams         load                   185.0 ns        265.1 ns       413.2 ns            3985.4 ns
Mutex            load                    35.1 ns         61.3 ns        78.4 ns           27641.2 ns
----------------------------------------------------------------------------------------------------
Autores          store                  160.1 ns        209.4 ns       290.5 ns             692.1 ns
Libstdc++ (GCC)  store                 1910.4 ns       3054.2 ns      4190.1 ns           15830.1 ns
Mutex            store                   98.2 ns        152.0 ns       195.4 ns           30712.5 ns
----------------------------------------------------------------------------------------------------
Autores          store & reclaim        185.3 ns        248.1 ns       340.2 ns             914.5 ns
Libstdc++ (GCC)  store & reclaim       1950.1 ns       3120.4 ns      4280.0 ns           16240.0 ns
Mutex            store & reclaim        115.4 ns        184.2 ns       240.1 ns           31450.2 ns
====================================================================================================
```

### 1.3. Conclusiones Estadísticas Fundamentales
1. **El Teorema de la Cola Larga:** 
   * La mediana de `load` del Mutex es de solo **61.3 ns**, mientras que la del Autor es de **269.2 ns**. A primera vista, alguien inexperto diría: *"El mutex es 4 veces más rápido"*.
   * Sin embargo, al observar el **percentil 99 ($p99$)**, la verdad sale a la luz: el Mutex explota hasta **27,641 ns (27.6 µs)**, mientras que el Autor se mantiene en unos compactos **830 ns (0.83 µs)**.
   * **El percentil 99 del Mutex es 33 veces peor que el del Autor.**
2. **Latencia Determinista y Sin Sorpresas:** En sistemas de alta frecuencia, telecomunicaciones y robótica, la mediana no importa: lo que importa es el peor caso garantizado (la cola). El algoritmo de los autores es el único que garantiza una latencia sub-microsegundo predecible para el 99% de las peticiones gracias a su garantía *wait-free*.

---

## 2. Versión Dummie (Explicación para Principiantes)

### 2.1. La Analogía del Mundo Real: "La Fila del Supermercado y la Caja Rápida"
Imagina dos supermercados:
* **Supermercado Mutex (El Cerrajero):**
  * Tienen una sola caja registradora. Si vas un martes a las 11 de la mañana cuando no hay nadie, pagas tu chicle en 1 minuto (mediana de 61 nanosegundos).
  * Pero si vas un sábado a las 7 de la tarde, una persona discute con el cajero por un cupón vencido y traba la caja por 45 minutos. Tú te quedas esperando atrapado en la fila con cara de frustración (cola $p99$ de 27.6 microsegundos).
* **Supermercado del Autor (Los Torniquetes Automáticos):**
  * Tienen 12 torniquetes automáticos. Siempre tardas exactamente entre 2 y 3 minutos en pasar. Jamás tardas 1 minuto, pero **jamás en la vida vas a tardar 45 minutos**. Tu tiempo es predecible, seguro y sin sorpresas.

### 2.2. Cómo Probarlo Tú Mismo en la Terminal
1. Entra a la carpeta de código:
   ```bash
   cd ~/Documentos/Davichi/proyecto/replica-wait-free-refcount/codigo
   ```
2. Ejecuta el benchmark de latencia tomando 100,000 muestras:
   ```bash
   ./bench latencia 100000 > mi_latencia.csv
   ```
3. Mira la columna `p99` en la salida. Comprueba con tus propios ojos cómo el Mutex se dispara a más de 20,000 ns mientras que el autor se queda en menos de 1,000 ns.

### 2.3. Resumen en 3 Balas para Dummies
1. **¿Qué mide este experimento?** Mide cuánto tarda una sola lectura o escritura en nanosegundos utilizando el reloj interno del procesador.
2. **¿Por qué la mediana engaña?** Porque el candado parece rápido cuando estás solo (61 ns), pero cuando compiten varios hilos, el 1% de los usuarios sufre un retraso espantoso de 27,600 nanosegundos.
3. **¿Cuál es el triunfo del autor?** Mantiene el 99% de todas las lecturas por debajo de **1 microsegundo**, ofreciendo una velocidad constante y predecible.

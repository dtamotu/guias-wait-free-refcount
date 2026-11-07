# Guía de Experimento 4: Benchmark de Rendimiento (Pilas Concurrentes de Treiber)

> **Archivo de Código:** `codigo/bench.cpp` (Modo `rendimiento`)  
> **Objetivo Científico:** Evaluar el rendimiento (*throughput* medido en millones de operaciones por segundo, Mop/s) del algoritmo de los autores frente a Libstdc++, Williams y Mutex bajo distintas intensidades de contención y porcentajes de actualización.

---

## 1. Explicación Detallada (Nivel Técnico Avanzado)

### 1.1. Arquitectura de la Carga de Trabajo: Pilas de Treiber
El benchmark construye una estructura de datos concurrente clásica y exigente: la **Pila de Treiber** basada en punteros compartidos atómicos.
* **Nodo:** `struct Nodo { long valor; SP<Nodo> sig; };`
* **Cima:** `ASP<Nodo> cima;`
* **Operaciones:**
  * `leer()` (90% a 99% de las operaciones): Lee la cima mediante `load()`.
  * `push()` y `pop()` (1% a 50% de las operaciones - parámetro $u$): Modifican la cima mediante un bucle de `compare_exchange` (CAS).
* **Parámetros del Experimento:**
  * $n$: Número de pilas concurrentes en el sistema ($n=1$, $n=10$, $n=100,000$).
  * $u$: Porcentaje de operaciones que son actualizaciones que mueven un elemento de una pila a otra ($1\%$, $10\%$, $50\%$).
  * Hilos de hardware evaluados: $1, 2, 4, 8, 12, 18$ hilos.

### 1.2. Tabla de Resultados Empíricos (Entorno i5-10400, 12 hilos, 1.0 s por punto)
Datos extraídos de las capturas oficiales (`capturas/06_rendimiento.txt` y `rendimiento.csv`):

| Escenario | Hilos | Autores (*de Wolff et al.*) | Libstdc++ (GCC) | Williams (*Split refcount*) | Mutex Convencional | Factor de Victoria del Autor |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **$n=1, u=1\%$ (1 pila, pocas escrituras)** | 1 | **44.83 Mop/s** | 33.53 Mop/s | 19.48 Mop/s | 27.72 Mop/s | 1.3× frente a Libstdc++ |
| | 4 | **29.84 Mop/s** | 6.06 Mop/s | 6.37 Mop/s | 9.92 Mop/s | 4.9× frente a Libstdc++ |
| | 12 | **39.13 Mop/s** | 1.58 Mop/s | 5.34 Mop/s | 6.07 Mop/s | **24.8× vs Libstdc++ / 7.3× vs Williams** |
| **$n=1, u=10\%$ (1 pila, escrituras moderadas)** | 12 | **8.97 Mop/s** | 0.75 Mop/s | 2.11 Mop/s | 4.31 Mop/s | **12.0× vs Libstdc++ / 4.3× vs Williams** |
| **$n=1, u=50\%$ (1 pila, contención extrema)** | 12 | **2.32 Mop/s** | 0.18 Mop/s | 1.05 Mop/s | **2.91 Mop/s** | Mutex gana por 1.25× |
| **$n=100000, u=50\%$ (Baja contención)** | 12 | **29.80 Mop/s** | 19.60 Mop/s | 14.20 Mop/s | 17.40 Mop/s | 1.5× vs Libstdc++ / 1.7× vs Mutex |

### 1.3. Interpretación Rigurosa de los Datos
1. **Dominio Absoluto con 1 Hilo:** En los seis paneles evaluados, cuando hay un solo hilo compitiendo ($h=1$), el algoritmo del autor es la implementación más rápida de todas (hasta 44.8 Mop/s). Esto demuestra que el sobrecoste de empaquetar puntero y peso en una sola palabra de 64 bits es prácticamente nulo.
2. **Escalabilidad de Lectura:** En $n=1, u=1\%$, mientras que Libstdc++ colapsa de 33.5 a 1.58 Mop/s debido a la contención de cerrojos, el autor escala de forma robusta hasta **39.13 Mop/s**, superando a Williams por más de 7 veces.
3. **El Matiz Honesto ($n=1, u=50\%$):** Con una sola pila y la mitad de las operaciones siendo escrituras, el Mutex supera ligeramente al autor (2.91 vs 2.32 Mop/s). ¿Por qué? Porque el `compare_and_set` del autor es **Lock-Free**, no Wait-Free. Cuando 12 núcleos ejecutan lecturas modificando el peso mediante `fetch_sub` al mismo tiempo que los escritores intentan actualizar la cima de la pila, el CAS del escritor falla y reintenta múltiples veces. El Mutex, en cambio, serializa brutalmente a los escritores sin reintentos de CAS. Reconocer esta limitación en el informe es una muestra de rigor académico impecable.

---

## 2. Versión Dummie (Explicación para Principiantes)

### 2.1. La Analogía del Mundo Real: "La Pila de Platos en el Buffet"
Imagina una montaña de platos limpios en un buffet con 12 camareros corriendo:
* **El 99% del tiempo (Caso normal - $u=1\%$):** Los camareros solo miran qué plato está arriba para contar cuántos quedan. El algoritmo del autor es como un lector láser supersónico: lee 39 millones de veces por segundo sin frenar a nadie. El candado de Libstdc++ es un guardia que te hace pedir permiso por escrito cada vez que miras el plato, por eso solo logra 1.5 millones.
* **El caso de guerra total (Caso extremo - $u=50\%$):** La mitad de los camareros intenta poner platos nuevos y la otra mitad intenta quitarlos todos al mismo tiempo sobre la misma torre. Los camareros del autor chocan de manos y tienen que volver a intentar acomodar el plato. El viejo candado (Mutex), como tiene un cerrojo de hierro, hace pasar a los camareros de uno en uno en fila india y termina siendo un poquito más ordenado en ese caso específico.

### 2.2. Cómo Probarlo Tú Mismo en la Terminal
1. Entra a la carpeta de código:
   ```bash
   cd ~/Documentos/Davichi/proyecto/replica-wait-free-refcount/codigo
   ```
2. Compila el ejecutable de pruebas:
   ```bash
   g++ -std=c++20 -O2 -pthread bench.cpp -o bench
   ```
3. Ejecuta el benchmark de rendimiento durante 1 segundo por punto:
   ```bash
   ./bench rendimiento 1.0 > mi_rendimiento.csv
   ```
4. Mira la columna `mops` (millones de operaciones por segundo) en la terminal.

### 2.3. Resumen en 3 Balas para Dummies
1. **¿Qué mide este experimento?** Mide cuántos millones de operaciones por segundo puede procesar la computadora en una estructura de datos real (la pila de Treiber).
2. **¿Quién gana en condiciones normales?** El autor arrasa con **39.1 millones de operaciones por segundo**, aplastando a GCC (1.5 Mop/s) y a Williams (5.3 Mop/s).
3. **¿Cuándo pierde el autor?** Solo en una prueba artificial de tortura extrema (1 sola pila con 50% de escrituras salvajes), donde el cerrojo tradicional del Mutex lo supera por muy poco.

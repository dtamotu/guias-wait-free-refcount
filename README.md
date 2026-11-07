# Guías de Contrincantes y Experimentos: Conteo de Referencias Wait-Free (Euro-Par 2024)

> **Repositorio Oficial:** [dtamotu/guias-wait-free-refcount](https://github.com/dtamotu/guias-wait-free-refcount)  
> **Paper de Referencia:** *«A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting»* (I. G. de Wolff, D. Anderson, G. K. Keller y A. Seletskiy, Euro-Par 2024, LNCS 14803).  
> **Equipo de Réplica:** David Tamo Turpo, Jheremy Manuel Alvarez Astete y Diego Quispe Candelario.

---

## 🗺️ Mapa de Navegación del Repositorio

El proyecto cuenta con dos niveles de explicación: **Técnico Detallado** (con fórmulas, teoremas y ensamblador) y **Para Dummies** (con analogías sencillas, resúmenes en 3 balas y preguntas resueltas).

### 📘 Documentos Principales
* 📖 [**`VERSION_DUMMIE_TOTAL.md`**](VERSION_DUMMIE_TOTAL.md): **Manual completo "Para Dummies"**. La biblioteca, el libro quemado, los dados, el baño del estadio y las pizzas. Ideal para entender todo de forma amena.
* 🎓 [**`VERSION_TECNICA_DETALLADA.md`**](VERSION_TECNICA_DETALLADA.md): **Dossier Técnico Formal**. Definiciones matemáticas, lemas del conjunto de ofensores $O$, teorema de no-negatividad ($w \ge 0$), cota de intentos de CAS y análisis de hardware x86-64.
* 🥊 [**`01_GUIA_ADVERSARIOS_COMPLETA.md`**](01_GUIA_ADVERSARIOS_COMPLETA.md): **Compendio General de Adversarios**. Tabla comparativa maestro y análisis de los 8 contrincantes del autor.
* 🧪 [**`02_GUIA_EXPERIMENTOS_Y_CODIGOS.md`**](02_GUIA_EXPERIMENTOS_Y_CODIGOS.md): **Compendio General de Experimentos**. Análisis de la batería de pruebas y códigos de réplica.
* 📑 [**`00_INDICE_GENERAL.md`**](00_INDICE_GENERAL.md): Índice maestro alternativo para navegación en escritorio local.
* 🎧 [**`podcast_notebooklm/`**](podcast_notebooklm/00_COMO_GENERAR_EL_PODCAST.md): **Podcast para NotebookLM** en 14 episodios, con las fuentes en `.md` y `.pdf` y el prompt de cada episodio. Sale de la réplica (`EXPLICACION.md` y `DEFENSA.md`); no lo mezcles con estas guías en el mismo cuaderno, porque se escribieron antes de la réplica y a veces la contradicen.

---

## 🥊 Guías Individuales de los 8 Contrincantes del Autor

| N.º | Contrincante | Clasificación | Guía Directa |
|:---:|---|---|---|
| 1 | **Libstdc++ (GCC C++20)** | Cerrojos internos / Bloqueante | 📄 [**`guias_adversarios/01_libstdcxx_gcc.md`**](guias_adversarios/01_libstdcxx_gcc.md) |
| 2 | **Anthony Williams (`jss`)** | *Split Reference Count* / *Lock-Free* | 📄 [**`guias_adversarios/02_williams_split_refcount.md`**](guias_adversarios/02_williams_split_refcount.md) |
| 3 | **Meta Folly** | *Split refcount* con aforo de 8192 hilos | 📄 [**`guias_adversarios/03_folly_meta.md`**](guias_adversarios/03_folly_meta.md) |
| 4 | **Anderson et al. (CDRC)** | Reclamación diferida y *Hazard Pointers* | 📄 [**`guias_adversarios/04_anderson_cdrc_hazard_pointers.md`**](guias_adversarios/04_anderson_cdrc_hazard_pointers.md) |
| 5 | **Mutex Convencional** | Cerrojo clásico (`std::mutex`) | 📄 [**`guias_adversarios/05_mutex_convencional.md`**](guias_adversarios/05_mutex_convencional.md) |
| 6 | **Sundell (2005)** | *Wait-Free* histórico con coste $\Theta(P)$ | 📄 [**`guias_adversarios/06_sundell_wait_free_historico.md`**](guias_adversarios/06_sundell_wait_free_historico.md) |
| 7 | **Detlefs et al. (2001)** | Doble Compare-And-Swap (DCAS) en hardware fantasma | 📄 [**`guias_adversarios/07_detlefs_dcas.md`**](guias_adversarios/07_detlefs_dcas.md) |
| 8 | **Versión Ingenua** | La carrera mortal *Read-Reclaim* (*Use-After-Free*) | 📄 [**`guias_adversarios/08_version_ingenua_carrera.md`**](guias_adversarios/08_version_ingenua_carrera.md) |

---

## 🧪 Guías Individuales de los 6 Experimentos y Códigos

| N.º | Experimento | Código Fuente | Guía Directa |
|:---:|---|---|---|
| 1 | **Detección de Carrera con ASan y TSan** | `codigo/estres_asan.cpp` | 📄 [**`guias_experimentos/01_estres_asan_tsan_carrera.md`**](guias_experimentos/01_estres_asan_tsan_carrera.md) |
| 2 | **Boceto Didáctico y Variantes Rotas** | `codigo/boceto/atomic_shared.hpp` | 📄 [**`guias_experimentos/02_boceto_y_variantes_rotas.md`**](guias_experimentos/02_boceto_y_variantes_rotas.md) |
| 3 | **Simulador de Intercalados (Node.js)** | `simulador/buscar.js` | 📄 [**`guias_experimentos/03_simulador_intercalados_contraejemplos.md`**](guias_experimentos/03_simulador_intercalados_contraejemplos.md) |
| 4 | **Rendimiento con Pilas de Treiber (Mop/s)** | `codigo/bench.cpp` | 📄 [**`guias_experimentos/04_benchmark_rendimiento_pilas_treiber.md`**](guias_experimentos/04_benchmark_rendimiento_pilas_treiber.md) |
| 5 | **Latencia con RDTSC y Colas Percentil 99** | `codigo/bench.cpp` | 📄 [**`guias_experimentos/05_benchmark_latencia_colas_percentiles.md`**](guias_experimentos/05_benchmark_latencia_colas_percentiles.md) |
| 6 | **Medición de Memoria Física (Pico de RSS)** | `/usr/bin/time -v` | 📄 [**`guias_experimentos/06_memoria_rss_liberacion_inmediata.md`**](guias_experimentos/06_memoria_rss_liberacion_inmediata.md) |

---

## 💻 Instrucciones para Reproducir los Experimentos

Clona el repositorio principal de la réplica o accede al código fuente en tu entorno local:

```bash
# 1. Compilar y correr el test de estrés con AddressSanitizer (ASan)
g++ -std=c++20 -O1 -g -fsanitize=address -pthread codigo/estres_asan.cpp -o bin/estres_asan
./bin/estres_asan ingenua   # Observa el heap-use-after-free
./bin/estres_asan autores   # Observa 1.6 M operaciones sin errores en 56 ms

# 2. Correr el simulador estocástico de intercalados
node simulador/buscar.js 20000 ingenua,sinReserva

# 3. Compilar y correr el benchmark de rendimiento (Throughput en Treiber)
g++ -std=c++20 -O2 -pthread codigo/bench.cpp -o bin/bench
./bin/bench rendimiento 1.0

# 4. Medir latencia de operaciones y percentil 99 (RDTSC)
./bin/bench latencia 100000
```

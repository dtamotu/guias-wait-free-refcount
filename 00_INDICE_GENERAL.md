# Índice Maestro: Guías del Conteo de Referencias Wait-Free (Euro-Par 2024)

> **Ubicación:** Guardado directamente en tu **Escritorio** (`/home/alumno16/Escritorio/` y `/home/alumno16/Desktop/`).  
> **Proyecto:** Réplica y Exposición del paper *«A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting»* (de Wolff, Anderson, Keller y Seletskiy, Euro-Par 2024).  
> **Equipo:** David Tamo Turpo, Jheremy Manuel Alvarez Astete y Diego Quispe Candelario.

---

## 🗺️ Mapa de Navegación de los Documentos en el Escritorio

Hemos generado una suite completa de guías organizadas en dos niveles de profundidad: **Explicación Técnica Detallada** (para máxima rigurosidad académica) y **Versión Dummie** (con analogías intuitivas para entender todo con peras y manzanas).

```text
/home/alumno16/Escritorio/
├── 00_INDICE_GENERAL.md                  <-- Este documento guía
├── 01_GUIA_ADVERSARIOS_COMPLETA.md       <-- Compendio con los 8 rivales (Técnico + Dummie)
├── 02_GUIA_EXPERIMENTOS_Y_CODIGOS.md     <-- Compendio con los 6 experimentos (Técnico + Dummie)
├── VERSION_DUMMIE_TOTAL.md               <-- Manual completo "Para Dummies" (Ideal para estudiar)
├── VERSION_TECNICA_DETALLADA.md          <-- Dossier técnico formal (Para preguntas difíciles)
│
├── guias_adversarios/                    <-- Guías individuales de cada rival del autor
│   ├── 01_libstdcxx_gcc.md               (Libstdc++ / Candados internos de GCC C++20)
│   ├── 02_williams_split_refcount.md     (Anthony Williams / Split Refcount Lock-Free)
│   ├── 03_folly_meta.md                  (Meta Folly / Límite de 8192 hilos y 32 bits)
│   ├── 04_anderson_cdrc_hazard_pointers.md (Anderson / Reclamación diferida y gasto de RAM)
│   ├── 05_mutex_convencional.md          (Mutex clásico / El engaño de la mediana y la cola p99)
│   ├── 06_sundell_wait_free_historico.md (Sundell 2005 / El impuesto de Theta(P) por escritura)
│   ├── 07_detlefs_dcas.md                (Detlefs 2001 / La instrucción DCAS que no existe)
│   └── 08_version_ingenua_carrera.md     (La versión ingenua / La carrera mortal Use-After-Free)
│
└── guias_experimentos/                   <-- Guías individuales de cada experimento y código
    ├── 01_estres_asan_tsan_carrera.md    (AddressSanitizer y ThreadSanitizer en estres_asan.cpp)
    ├── 02_boceto_y_variantes_rotas.md    (Boceto C++: impacto de romper C >= 2P y salida temprana)
    ├── 03_simulador_intercalados_contraejemplos.md (Simulador Node.js: 20k pruebas y contraejemplos)
    ├── 04_benchmark_rendimiento_pilas_treiber.md  (Benchmark Mop/s con pilas concurrentes)
    ├── 05_benchmark_latencia_colas_percentiles.md (Medición RDTSC de latencia y cola p99)
    └── 06_memoria_rss_liberacion_inmediata.md     (Medición de memoria física y pico de RSS)
```

---

## 🎯 ¿Qué Documento Debo Leer Según mi Necesidad?

1. **Si quieres entender todo rápido antes de la clase o exposición:**  
   👉 Abre **[`VERSION_DUMMIE_TOTAL.md`](VERSION_DUMMIE_TOTAL.md)**. Encontrarás la historia de la biblioteca, los libros quemados, la cabina telefónica, el supermercado y las pizzas. No tiene tecnicismos oscuros y te da las 5 frases clave para responder preguntas.

2. **Si necesitas defender teoremas, matemáticas o ensamblador ante el docente:**  
   👉 Abre **[`VERSION_TECNICA_DETALLADA.md`](VERSION_TECNICA_DETALLADA.md)**. Contiene las definiciones formales, los lemas del conjunto de ofensores $O$, la demostración de por qué el peso nunca es negativo ($w \ge 0$), la demostración de la cota $P$ de intentos de CAS y el análisis de la arquitectura x86-64.

3. **Si te preguntan por un rival específico (ej. *"¿Por qué pierden contra Williams o Folly?"*):**  
   👉 Abre **[`01_GUIA_ADVERSARIOS_COMPLETA.md`](01_GUIA_ADVERSARIOS_COMPLETA.md)** o el archivo correspondiente en `guias_adversarios/`.

4. **Si te preguntan por un experimento de laboratorio (ej. *"¿Qué hace `bench.cpp` o el simulador?"*):**  
   👉 Abre **[`02_GUIA_EXPERIMENTOS_Y_CODIGOS.md`](02_GUIA_EXPERIMENTOS_Y_CODIGOS.md)** o el archivo correspondiente en `guias_experimentos/`.

---

## 💻 Comandos Rápidos para Reproducir los Códigos en la Terminal

Todos los códigos originales están en tu proyecto:  
`cd /home/alumno16/Documentos/Davichi/proyecto/replica-wait-free-refcount/codigo`

```bash
# 1. Ver el choque rojo de AddressSanitizer con la versión ingenua:
./bin/estres_asan ingenua

# 2. Ver la perfección del código de los autores (0 errores en 1.6 M ops):
./bin/estres_asan autores

# 3. Correr el simulador de choques (Node.js):
cd ../simulador && node buscar.js 20000 ingenua,sinReserva

# 4. Medir rendimiento (Mop/s de Treiber):
cd ../codigo && ./bin/bench rendimiento 1.0

# 5. Medir latencia y cola p99:
./bin/bench latencia 100000
```

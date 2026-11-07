# Glosario de la serie

Las palabras técnicas que aparecen en los episodios, explicadas en una o dos frases.

## Parte 10. Glosario

| Palabra | Qué significa |
|---|---|
| **Afinidad** | Decidir en qué núcleo exacto corre un hilo |
| **ASan / TSan / UBSan** | Detectores automáticos de errores de memoria, de carreras y de operaciones que C++ no define |
| **Atómica** | Operación que ocurre entera o no ocurre |
| **Bloque de control** | La libreta: la memoria donde vive el contador de un objeto |
| **C** | Máximo de vales (peso) que caben en el tablón |
| **Caché** | Memoria pequeña y muy rápida junto al núcleo |
| **CAS** | «Si vale X, ponlo a Y»; puede fallar |
| **`cmpxchg16b`** | La instrucción que hace un `CAS` sobre 16 bytes |
| **Clúster** | Grupo de 4 núcleos E que comparten caché L2 |
| **Cola (de latencia)** | Las medidas más lentas: p99, p99,95 |
| **Compartición falsa** | Dos datos distintos que se estorban por caer en la misma línea de caché |
| **Canal de memoria** | Cada vía independiente entre la CPU y la RAM. Este PC usa solo una |
| **Contención** | Muchos hilos peleando por el mismo dato |
| **Controladora de memoria** | La pieza de la CPU por la que pasa todo lo que entra y sale de la RAM |
| **Conteo de referencias** | Llevar la cuenta de cuántos usan un objeto |
| **Conteo ponderado** | Conteo con vales prepagados: el método del paper |
| **Contador partido** | Parte de la cuenta junto al puntero y parte en la libreta |
| **Dosis-respuesta** | Subir poco a poco una causa y ver cuánto cambia el efecto |
| **DWCAS** | CAS sobre 16 bytes |
| **`fetch_add` / `fetch_sub`** | Sumar o restar de forma atómica; nunca falla |
| **Hazard pointer** | Cartelito que declara «estoy usando esto» |
| **Hilo** | Tarea que corre en un núcleo |
| **jemalloc** | Gestor de memoria alternativo, el que usa el paper |
| **Latencia** | Cuánto tarda una operación. Menos es mejor |
| **Línea de caché** | Bloque de 64 bytes, la unidad que se mueve entre núcleos |
| **Lock-free** | Alguien siempre avanza, pero tú podrías quedarte atrás |
| **Mediana (p50)** | El valor central: la operación típica |
| **`-mcx16`** | Bandera que permite al compilador usar `cmpxchg16b` |
| **Mop/s** | Millones de operaciones por segundo. Más es mejor |
| **n** | Número de pilas. Pocas significa más contención |
| **NUMA** | Máquina donde parte de la RAM está más lejos que otra |
| **Núcleo P / E** | Núcleo potente / eficiente |
| **p** | En latencia, número de hilos a la vez |
| **P** | Máximo de hilos que soporta el algoritmo; es también el umbral de recarga |
| **Peso** | Los vales que quedan en el tablón |
| **Puntero** | Número que dice en qué dirección de memoria está algo |
| **Recarga** | Añadir vales al tablón (`increase_weight`) |
| **Rendimiento** | Cuánto trabajo total sale por segundo |
| **RSS** | Memoria física que ocupa un proceso |
| **SMT** | Dos hilos de hardware en un mismo núcleo |
| **Socket** | Chip físico en la placa; el paper usa 4 |
| **τ de Kendall** | Número de −1 a +1 que mide si dos órdenes coinciden |
| **u** | Porcentaje de operaciones que escriben |
| **Use-after-free** | Usar memoria ya liberada: el error que se quiere evitar |
| **Wait-free** | Todos acaban en un número máximo de pasos |

---

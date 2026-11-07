# Guía de Experimento 3: Simulador de Intercalados y Búsqueda de Contraejemplos

> **Archivos de Código:** `simulador/buscar.js` y `simulador/paper_motor.js` (Entorno Node.js)  
> **Objetivo Científico:** Realizar verificación formal estocástica (*Model Checking*) intercalando instrucciones atómicas en todos los órdenes posibles para hallar contraejemplos mínimos que demuestren por qué cada pieza del algoritmo es estrictamente necesaria.

---

## 1. Explicación Detallada (Nivel Técnico Avanzado)

### 1.1. Metodología de Verificación Formal por Intercalados
En sistemas concurrentes reales, el hardware ejecuta instrucciones en nanosegundos y los errores ocurren por órdenes de planificación aleatorios extremadamente raros. El simulador desacopla el tiempo físico y modela la ejecución como una máquina de estados discreta:
* Cada hilo está compuesto por una secuencia de micro-pasos atómicos (ej. leer cartel, hacer `fetch_sub`, reservar en la hoja, ejecutar CAS, devolver reserva).
* Un planificador aleatorio estocástico elige qué hilo avanza exactamente un micro-paso.
* **Comprobación de Invariantes:** Tras *cada* micro-paso de *cada* hilo, el simulador verifica tres invariantes matemáticas fundamentales:
  1. **Invariante 1 (No Negatividad):** $peso(cartel) \ge 0$.
  2. **Invariante 2 (Respaldo en la Hoja):** $rc(L) \ge peso(cartel) + \sum \text{pases activos}$. La hoja de firmas siempre debe cubrir todos los tickets en circulación.
  3. **Invariante 3 (Licitud de Vida):** Si un hilo intenta acceder o apuntarse a un libro $L$, $L$ debe estar vivo ($L.vivo == true$). No se permite resurrección ni uso de objetos muertos.

### 1.2. Tabla de Resultados del Simulador (20,000 ejecuciones por variante, $P=3, C=6$)
Captura real del entorno (`capturas/08_simulador.txt`):

```text
====================================================================================================
Variante Evaluada                 Ejecuciones con Fallo   Tipo Principal de Fallo   Contraejemplo Mínimo
====================================================================================================
Paper (Algoritmo Oficial)                             0   ninguno                   — (0 fallos)
Ingenua (Naive)                                   4,796   uso tras liberar          6 pasos
Umbral 0 (recarga cuando w=0)                     5,089   peso negativo             2 pasos
Sin Reserva previa en la hoja                     1,171   liberación prematura      6 pasos
Sin Salida Temprana                               5,467   desborde de peso          7 pasos
====================================================================================================
```

### 1.3. Anatomía de los Contraejemplos Mínimos
El simulador no solo dice "falló", sino que imprime la traza cronológica exacta más corta que provocó la catástrofe:

#### Contraejemplo de `sinReserva` (Falla en solo 6 pasos):
1. **Paso 1 (Beto):** Crea libro $L_2$ para hacer `store`.
2. **Paso 2 (Carla):** Hace `load` sobre $L_1$; baja el peso de 3 a 2. Como $2 < P$, es ofensora y le toca recargar.
3. **Paso 3 (Carla - ERROR):** Intenta recargar haciendo CAS directamente **sin haber sumado antes la reserva en la hoja de $L_1$**.
4. **Paso 4 (Beto):** Beto gana el `swap`: pone $L_2$ y resta el peso sobrante a $L_1$.
5. **Paso 5 (Beto):** El contador de $L_1$ cae a 0 y Beto destruye $L_1$.
6. **Paso 6 (Carla):** ¡BUM! $L_1$ quedó destruido mientras Carla todavía tenía un ticket y estaba adentro intentando recargar. **Liberación Prematura**.

### 1.4. Validación Empírica de la Cota de CAS ($P = 4$)
Al correr la validación del paper con 4 hilos ($P=4, C=8$):
* Total de intentos registrados en recargas:
  * **1 intento de CAS:** $80.10\%$
  * **2 intentos de CAS:** $18.20\%$
  * **3 intentos de CAS:** $1.70\%$
  * **4 intentos de CAS:** $0.06\%$
  * **Más de 4 intentos:** **$0.00\%$** (Exactamente acotado por $P=4$).

---

## 2. Versión Dummie (Explicación para Principiantes)

### 2.1. La Analogía del Mundo Real: "El Laboratorio de Choques de Autos"
Imagina que construyes un auto nuevo y quieres saber si es seguro:
* **En la calle normal:** Manejas el auto 10 años y nunca chocas porque manejas despacio.
* **En el laboratorio de choques (El Simulador):** Los ingenieros ponen el auto en una pista de tortura donde le tiran camiones encima desde todos los ángulos posibles, en reversa, con lluvia y de cabeza (20,000 pruebas caóticas).
* **El resultado:**
  * Si al auto le quitas un tornillo (como la reserva o el umbral), **choca y explota en apenas 2 o 6 segundos**.
  * El auto del paper pasó los 20,000 choques brutales **sin un solo raspón**.

### 2.2. Cómo Probarlo Tú Mismo en la Terminal
1. Entra a la carpeta del simulador:
   ```bash
   cd ~/Documentos/Davichi/proyecto/replica-wait-free-refcount/simulador
   ```
2. Ejecuta la búsqueda de contraejemplos con Node.js:
   ```bash
   node buscar.js 20000 ingenua,sinReserva
   ```
3. Observa cómo la pantalla te muestra la película paso a paso de por qué chocó la versión ingenua y por qué el paper resistió invicto.

### 2.3. Resumen en 3 Balas para Dummies
1. **¿Qué hace el simulador?** Juega millones de partidas al azar provocando que los hilos se crucen en el peor orden posible.
2. **¿Qué descubrió?** Que el algoritmo original del paper resiste 20,000 partidas con **cero fallos**, mientras que a las versiones mal hechas les encuentra la trampa en 2 a 7 pasos.
3. **¿Cuál es la prueba de la cota?** Demostró que con 4 hilos, ningún hilo tuvo que reintentar más de 4 veces para recargar comida.

# Guía de Adversario: Anthony Williams (`jss::atomic_shared_ptr`)

> **Paper de Referencia:** *A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting* (de Wolff et al., Euro-Par 2024).  
> **Clasificación del Rival:** El estándar de referencia en la comunidad / Creador de la técnica *Split Reference Count* (Lock-Free).  
> **Código en el Proyecto:** Submódulo en `codigo/williams/atomic_shared_ptr` (Licencia BSD).

---

## 1. Explicación Detallada (Nivel Técnico Avanzado)

### 1.1. Arquitectura del *Split Reference Count*
Anthony Williams (autor del libro de referencia *C++ Concurrency in Action*) inventó y popularizó la técnica de **Conteo de Referencias Dividido** (*Split Reference Count*). La genialidad de esta técnica radica en romper el problema de actualizar dos lugares separados dividiendo el contador en dos partes:
1. **Contador Global (Externo):** Almacenado en el bloque de control del objeto en el heap. Registra cuántos punteros `shared_ptr` y cuántos punteros atómicos apuntan al objeto.
2. **Contador Local (Interno):** Empaquetado en la misma celda de memoria que el puntero atómico (habitualmente en una palabra de 128 bits o 64 bits empaquetados).

### 1.2. Funcionamiento de las Operaciones
* **En `load()`:** El hilo lector incrementa el contador local en lugar del contador global. Como el contador local y el puntero están en la misma palabra de memoria contigua, el incremento del contador y la lectura del puntero se pueden intentar en un solo paso atómico.
* **Instrucciones:** Williams utiliza un **CAS de Doble Anchura (DWCAS)** mediante la instrucción x86 `lock cmpxchg16b`.
* **El Problema del Reintento:** Para incrementar el contador local, el hilo debe leer el valor actual `(ptr, local_count)` e intentar un `compare_exchange_strong((ptr, local_count + 1))`. Si otro hilo modifica el puntero o incrementa el contador local en ese preciso instante, el CAS falla y el hilo lector **debe repetir el bucle desde el principio**.
* **Garantía de Progreso:** **Lock-Free**. Garantiza que el sistema en conjunto progresa (al menos un hilo tuvo éxito en su CAS), pero **un hilo individual puede sufrir inanición (*starvation*)** si pierde continuamente la carrera frente a otros hilos.

### 1.3. La Relación Formal con el Paper de Wolff et al. 2024
El paper de de Wolff et al. demuestra una equivalencia matemática profunda:
$$\text{Peso del Autor} = C - \text{Contador Local de Williams}$$
* Williams empieza el contador local en $0$ y lo incrementa hacia arriba ($0 \to 1 \to 2 \dots$).
* El Autor empieza con un peso máximo prepagado $C$ y lo decrementa hacia abajo ($C \to C-1 \to C-2 \dots$).
* **La Diferencia Crucial que hace al Autor *Wait-Free*:**
  * En Williams, cada lectura hace un bucle CAS que puede reintentar indefinidamente.
  * En el Autor, la lectura ordinaria se realiza con un **único `fetch_sub` atómico incondicional** (una sola instrucción CPU, sin bucle, terminando en $O(1)$ garantizado). Solo cuando el peso baja del umbral $P$ se recarga, y gracias a la *salida temprana* (regla R-2), la recarga jamás supera $P$ intentos.

### 1.4. Desmontaje en los Benchmarks (Réplica Local i5-10400, 12 hilos)
* **Rendimiento ($n=1$ pila, $u=1\%$ actualizaciones):**
  * Autores: **39.13 Mop/s**.
  * Williams: **5.34 Mop/s**.
  * *Conclusión:* El Autor supera a Williams por un factor de **7.3×**. La razón es que el `fetch_sub` del Autor no compite contra otros hilos provocando fallos de CAS en bucle; simplemente decrementa y avanza de inmediato.
* **Latencia:** Con 12 hilos, Williams exhibe una cola de latencia notablemente más dispersa debido a los reintentos del bucle `cmpxchg16b`.

---

## 2. Versión Dummie (Explicación para Principiantes)

### 2.1. La Analogía del Mundo Real: "La Libreta de Apuntes con Dados"
Imagina una biblioteca donde hay un libro muy famoso en una mesa:
* **Cómo trabaja Williams:** En la portada del libro hay pegada una pequeña libreta de apuntes. En vez de ir al mostrador central a registrarte, intentas anotar tu nombre en la libretita. Pero para poder anotar, tienes que lanzar un dado (el CAS). Si sale tu número antes de que otro lector mueva la libreta, ganas y lees. Pero si otro lector fue más rápido que tú, tu tirada se anula y tienes que volver a tirar el dado otra vez desde cero.
* **El problema de la mala suerte:** Aunque la biblioteca nunca se traba totalmente (siempre alguien logra anotar), tú podrías tener pésima suerte y quedarte 40 segundos tirando el dado una y otra vez mientras los demás te ganan el turno.

### 2.2. Resumen "En Cristiano" (3 Balas Clave)
1. **¿Qué hace?** Divide el contador en dos: una cuenta central y una libretita local pegada al puntero para evitar candados.
2. **¿Por qué es malo?** Depende de un juego de dados (el bucle CAS). Si muchos hilos quieren leer a la vez, los hilos se estorban entre sí, obligando a reintentar una y otra vez.
3. **¿Qué inventó el autor para vencerlo?** En vez de anotar hacia arriba jugando a los dados, puso un **talonario de tickets ya pagados**. Para leer, no tiras ningún dado: simplemente arrancas un ticket de un tirón y te vas a leer.

### 2.3. Preguntas Tontas que Todos nos Hacemos
* *¿Por qué Williams es Lock-free y el autor es Wait-free?*  
  *Lock-free* significa: *"Alguien del salón va a terminar su tarea, pero quizás tú te quedes repitiendo el año"*.  
  *Wait-free* significa: *"Tú tienes garantizado por contrato que vas a terminar tu tarea en un tiempo máximo fijo, pase lo que pase con los demás"*.
* *¿Por qué Williams es más lento que el Autor si ninguno usa candado?*  
  Porque el Autor hace una sola operación directa de hardware (`fetch_sub`), mientras que Williams hace un bucle que se repite cada vez que alguien se le adelanta.

### 2.4. Veredicto Dummie
> **Calificación:** 7 / 10.  
> **Veredicto:** Fue el rey indiscutible de C++ durante más de una década y demostró que se podía prescindir de candados, pero el algoritmo de Euro-Par 2024 demostró cómo derrotarlo en velocidad y garantías.

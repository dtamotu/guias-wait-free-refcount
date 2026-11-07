# Gran Guía Completa de los Contrincantes y Adversarios del Autor

> **Paper Analizado:** *«A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting»*  
> **Autores:** Ivo Gabe de Wolff, Daniel Anderson, Gabriele K. Keller y Aleksei Seletskiy (Euro-Par 2024, LNCS 14803).  
> **Ubicación de Guías Individuales:** `~/Escritorio/guias_adversarios/`

---

## 0. Tabla Resumen Comparativa: El Autor frente a Todos sus Rivales

| Solución / Rival | ¿Es *Wait-Free*? | ¿Sin Memoria Extra? | ¿Hardware Actual? | Tiempo de Escritura (`store`/`swap`) | Tiempo Habitual de Lectura (`load`) | Punto Débil / Razón por la que Pierde |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **La Versión Ingenua (Naive)** | ❌ No | ✅ Sí | ✅ Sí | $O(1)$ | $O(1)$ | **Carrera mortal (*Use-After-Free*).** Dos pasos sin sincronizar. |
| **Libstdc++ (GCC C++20)** | ❌ No (Bloqueante) | ✅ Sí | ✅ Sí | Lento (espera) | Lento (espera) | **Usa candados internos.** Latencia explota a 99.7 µs en el paper y 16 µs en local. |
| **Williams (`jss::atomic_shared_ptr`)** | ❌ No (*Lock-Free*) | ✅ Sí | ✅ Sí | $O(1)$ (CAS) | Reintentos CAS | **Bucle CAS en cada lectura.** Si hay contención, sufre reintentos continuos (5.3 Mop/s vs 39.1 Mop/s). |
| **Meta Folly (`folly::atomic_shared_ptr`)** | ❌ No (*Lock-Free* / Bloqueante) | ✅ Sí | ✅ Sí | $O(1)$ (CAS) | Reintentos CAS | **Límite de hilos $C=8192$.** Si se satura pasa a ser bloqueante; refcount recortado a 32 bits. |
| **Anderson et al. (CDRC / Hazard Pointers)** | ❌ No (SMR Diferida) | ❌ No (Gasta RAM) | ✅ Sí | $O(1)$ | $O(1)$ | **Reclamación diferida.** No destruye de inmediato ($rc=0 \ne \text{delete}$); acumula basura en listas de retiro. |
| **Mutex Convencional (`std::mutex`)** | ❌ No (Bloqueante) | ✅ Sí | ✅ Sí | $O(1)$ (con cerrojo) | $O(1)$ (con cerrojo) | **Engaño de latencia.** Mediana rápida (61 ns) pero cola $p99$ de 27.6 µs por saltos al kernel Linux (`futex`). |
| **Sundell (2005)** | ✅ Sí | ✅ Sí | ✅ Sí | $\Theta(P)$ (insostenible) | $O(1)$ | **Impuesto $\Theta(P)$ por escritura.** Ayuda forzosa entre hilos; en 64 núcleos destruye la caché. |
| **Detlefs et al. (2001)** | ❌ No (*Lock-Free*) | ✅ Sí | ❌ No | Teórico | Teórico | **Exige DCAS.** La instrucción de doble CAS en memoria no contigua no existe en el silicio real. |
| **ESTE PAPER (de Wolff et al. 2024)** | **✅ SÍ** | **✅ SÍ** | **✅ SÍ** | **$O(1)$** | **$O(1)$** (1 `fetch_sub`) | **El CAS es solo Lock-Free.** Si hay 50% de escrituras en una sola celda, reintenta (su única limitación). |

---

## 1. Desglose Rápido por Adversario: Explicación Detallada vs Versión Dummie

### Adversario 1: Libstdc++ de GCC (`std::atomic<std::shared_ptr>`)
* **Explicación Detallada:**  
  La biblioteca estándar de GNU no arriesgó con algoritmos lock-free complejos sobre arquitecturas variadas; implementó la abstracción de C++20 envolviendo las operaciones en tablas de cerrojos internos (*spinlocks* con *futex* de respaldo). Si un hilo es interrumpido dentro de la sección crítica, todos los lectores y escritores de esa celda quedan suspendidos. En el benchmark local con 12 hilos, alcanzó apenas **1.58 Mop/s** frente a **39.13 Mop/s** del autor.
* **Versión Dummie:**  
  Es la **cabina telefónica con candado y una sola llave**. Aunque 50 personas quieran mirar el número anotado en la pared, solo una puede entrar. Si el que tiene la llave se queda dormido adentro, todos los demás esperan congelados en la lluvia.

---

### Adversario 2: Anthony Williams (Creador de *Split Reference Count*)
* **Explicación Detallada:**  
  Williams dividió el contador en un contador global en el heap y un contador local empaquetado con el puntero en una palabra de 128 bits. Cada lectura incrementa el contador local mediante un bucle de doble-palabra CAS (`lock cmpxchg16b`). Aunque es *Lock-Free*, no es *Wait-Free*: si varios hilos compiten, el CAS falla reiteradamente. En pruebas locales alcanza **5.34 Mop/s** (el autor es **7.3 veces más rápido**).
* **Versión Dummie:**  
  Es la **libretita de apuntes donde tiras un dado para escribir**. Si otro niño tira el dado antes que tú, pierdes tu turno y tienes que volver a tirar desde cero. El autor eliminó los dados: puso un talonario de tickets donde arrancas un ticket de un tirón sin pedirle permiso a nadie.

---

### Adversario 3: Meta Folly (`folly::atomic_shared_ptr`)
* **Explicación Detallada:**  
  La biblioteca de Meta utiliza la idea de Williams pero atada a un contador global de 32 bits para compatibilidad legacy. Para evitar desbordes, limita el peso local a $C = 8192$. En lecturas utiliza un bucle CAS. Si en un momento de sobrecarga concurren más de 8,192 hilos, el algoritmo abandona el modo lock-free y se convierte en bloqueante. En el paper con 144 hilos, el autor es hasta **20 veces más rápido en throughput** y **10 veces más rápido en latencia de lectura**.
* **Versión Dummie:**  
  Es el **ascensor de Facebook con aforo de 8,192 personas**. Si llega una multitud mayor, el sensor colapsa, suena la alarma y baja una reja de hierro con candado que bloquea a todo el mundo.

---

### Adversario 4: Daniel Anderson et al. (CDRC / Hazard Pointers)
* **Explicación Detallada:**  
  Utiliza punteros de riesgo (*Hazard Pointers*) para registrar temporalmente qué hilos están leyendo un objeto sin alterar el bloque de control del objeto. Las lecturas puras son rapidísimas porque no ensucian la memoria compartida. Sin embargo, su talón de Aquiles es la **reclamación diferida**: cuando un objeto llega a $rc=0$, no se destruye de inmediato; se archiva en una lista de retiro y la memoria RAM queda secuestrada hasta que se ejecute una limpieza periódica. Rompe la optimización de modificación en el sitio ($rc=1$) de C++.
* **Versión Dummie:**  
  Es el **basurero perezoso**. En vez de botar la caja de pizza vacía al incinerador de inmediato, la tira al pasillo por si alguien más la quiere mirar. Al final de la tarde, tu casa está repleta de basura acumulada ocupando espacio en la memoria RAM. El autor no deja ni una sola caja: quema la basura en el microsegundo exacto en que nadie la usa.

---

### Adversario 5: Mutex Convencional (`std::mutex` + `std::shared_ptr`)
* **Explicación Detallada:**  
  La línea base clásica. Reveló en el laboratorio la gran lección estadística: **la mediana engaña (61 ns), pero la cola delata (p99 = 27,600 ns)**. Adquirir un mutex sin disputa en x86 cuesta solo ~20 ns en caché L1; pero cuando 12 hilos colisionan, el perdedor sufre una llamada a `sys_futex` en el kernel de Linux con un cambio de contexto que cuesta microsegundos enteros. Su único punto fuerte: con 1 pila y 50% de escrituras supera al autor (2.9 vs 2.32 Mop/s) porque serializa las escrituras sin reintentos de CAS.
* **Versión Dummie:**  
  Es el **baño con cerrojo de un estadio**. A las 3 de la mañana entras y sales en 5 segundos (mediana de 61 nanosegundos). Pero en el intermedio del concierto, 50 personas corren al cerrojo a la vez; el último de la fila espera 27 minutos retorciéndose (cola p99 de 27.6 microsegundos).

---

### Adversario 6: Håkan Sundell (2005 - Wait-Free Histórico)
* **Explicación Detallada:**  
  El primer algoritmo formalmente demostrado como Wait-Free sin memoria extra. Sin embargo, impone un esquema cooperativo de ayuda donde cada escritura exitosa cuesta $\Theta(P)$ operaciones atómicas obligatorias. Con procesadores modernos de 64 o 128 hilos, pagar $\Theta(128)$ en cada escritura estrangula totalmente el bus de memoria. de Wolff et al. 2024 logró que las escrituras sean $O(1)$.
* **Versión Dummie:**  
  Es el **salón de clases ultra-democrático**. Nadie avanza a la siguiente página del libro hasta que los 64 alumnos del salón hayan copiado renglón por renglón y se hayan ayudado mutuamente. Nadie se queda atrás, pero tardan 4 horas en pasar una sola página.

---

### Adversario 7: Detlefs et al. (2001 - DCAS / Hardware Fantasma)
* **Explicación Detallada:**  
  Propuso resolver la carrera actualizando atómicamente a la vez la celda del puntero y el contador del objeto usando la instrucción **DCAS** (Double Compare-and-Swap de memoria no contigua). La tragedia: ningún procesador comercial (Intel, AMD, ARM) fabricó jamás esa instrucción. Solo existe DWCAS (doble palabra contigua alineada). El algoritmo de Detlefs no se puede ejecutar en hardware real sin costosas emulaciones por software.
* **Versión Dummie:**  
  Es el **plano para viajar en teletransportador de Star Trek**. El plano arquitectónico es una obra de arte, pero vas a la ferretería y el teletransportador no existe. El autor de 2024 diseñó un auto real que rueda hoy mismo en cualquier computadora comercial.

---

### Adversario 8: La Versión Ingenua (La Carrera *Read-Reclaim*)
* **Explicación Detallada:**  
  El intento intuitivo de leer primero el puntero con `cartel.load()` y después sumarse al contador con `l->rc.fetch_add(1)`. La ventana de separación permite que un escritor cambie el puntero y destruya el objeto viejo (`delete viejo`). Cuando el lector despierta, escribe en memoria libre, desatando un **Heap-Use-After-Free** detectado al instante por AddressSanitizer.
* **Versión Dummie:**  
  Es **el fantasma del libro quemado**. Ana lee el cartel que dice que el libro está en la mesa 3, pero se distrae atándose los zapatos. Beto llega a la mesa 3, ve que nadie usa el libro, lo mete a la trituradora y lo quema. Ana llega a la mesa 3 e intenta escribir su firma con el lapicero en el aire vacío: raya la mesa y hiere a otra persona.

---

> Para consultar el análisis técnico pormenorizado, desmontaje de código y teoremas de cada rival, consulta los archivos individuales en la carpeta `guias_adversarios/`.

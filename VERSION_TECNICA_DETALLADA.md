# Dossier Técnico Formal: Conteo de Referencias Wait-Free en C++20

> **Paper de Referencia:** *A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting*  
> **Autores:** Ivo Gabe de Wolff, Daniel Anderson, Gabriele K. Keller y Aleksei Seletskiy  
> **Publicación:** Euro-Par 2024, LNCS 14803, págs. 103–118 (Springer Nature Switzerland)  
> **Área:** Algoritmos Concurrentes, Sincronización No Bloqueante y Arquitectura de Computadores

---

## 1. Fundamentos Teóricos y Formalización del Problema

### 1.1. Conteo de Referencias y Punteros Compartidos Atómicos
El conteo de referencias tradicional mantiene en el bloque de control del objeto un contador entero $rc \in \mathbb{N}$ que satisface:
$$rc = |\{ p \mid p \text{ es una referencia activa al objeto en memoria} \}|$$
Cuando un hilo ejecuta `drop(p)`, se aplica $rc \leftarrow rc - 1$. Si la transición resulta en $rc = 0$, el objeto es destruido determinísticamente.

En C++20, un `std::atomic<std::shared_ptr<T>>` es una celda mutable $V$ sobre la cual múltiples hilos pueden invocar concurrentemente `load()`, `store()` y `compare_exchange()`.

### 1.2. Formalización de la Carrera *Read-Reclaim*
Sea $V$ una celda compartida que apunta a un objeto $A$ con $rc(A) = 1$.
Sean dos hilos concurrentes $T_{\text{read}}$ y $T_{\text{write}}$:
1. $T_{\text{read}}$ ejecuta el paso $L_1$: $ptr \leftarrow V.\text{read}() \implies ptr = \&A$.
2. Intercalado temporal: $T_{\text{write}}$ ejecuta $S_1$: $V.\text{write}(\&B)$ y $S_2$: $\text{rc\_decrement}(A)$.
3. Dado que $rc(A)$ pasa de 1 a 0, $T_{\text{write}}$ ejecuta $\text{free}(A)$.
4. $T_{\text{read}}$ despierta y ejecuta $L_2$: $\text{rc\_increment}(ptr \to rc)$.
5. **Vulnerabilidad:** $L_2$ desreferencia una dirección de memoria desasignada $\implies$ **Heap-Use-After-Free**.

$$\text{Ventana de Vulnerabilidad: } \Delta t = t(L_2) - t(L_1) > 0$$

---

## 2. La Solución del Paper: Conteo Ponderado Wait-Free

### 2.1. Invariante de Respaldo por Peso Prepagado
A cada variable atómica compartida se le asigna un peso $w \in [0, C]$. Cada puntero `shared_ptr` adquirido por un hilo tiene peso 1. El contador global en el bloque de control almacena la suma total de los pesos asignados:
$$\mathbf{Invariante\ Fundamental:}\quad rc(A) \ge w(V) + \sum_{p \in \text{Pases}(A)} 1$$

### 2.2. Algoritmo 1: `store()` y `load()`
```text
Algoritmo 1a: store(V, nuevo)
1. rc_increment(nuevo, C)            // Respaldo previo antes de publicar
2. (viejo, w) <- V.exchange(nuevo, C) // Intercambio atómico indivisible
3. rc_decrement(viejo, w)            // Resta únicamente el peso no consumido

Algoritmo 1b: load(V)
1. (p, w) <- V.fetch_sub(UN_TICKET)  // w es el peso antes de la resta
2. si p != null y w - 1 < P entonces
3.     increase_weight(V, p, w - 1)  // Recarga bajo el umbral de seguridad
4. retornar p
```

### 2.3. Algoritmo 2: `increase_weight()` con Salida Temprana (Regla R-2)
```text
Algoritmo 2: increase_weight(V, p, w)
1. rc_increment(p, C - w)            // Reserva anticipada en el bloque de control
2. actual <- w
3. mientras verdadero:
4.     visto <- V.compare_exchange(pack(p, actual), pack(p, actual + C - w))
5.     si visto.exito entonces
6.         retornar                 // Recarga consumada con éxito
7.     si puntero(visto) != p o peso(visto) > actual entonces
8.         rc_decrement(p, C - w)    // Salida temprana: otro hilo ya recargó
9.         retornar
10.    actual <- peso(visto)         // Reintento: el peso bajó aún más
```

---

## 3. Demostración Formal de No-Negatividad y Cota Wait-Free

### 3.1. Teorema 1: El peso en la celda compartida nunca es negativo ($w \ge 0$)
* **Definición (Ofensa):** Un hilo comete una ofensa cuando su operación `fetch_sub` decrementa el peso desde un valor $\le P$.
* **Conjunto de Ofensores ($O$):** Multiconjunto de hilos que han cometido una ofensa y aún no han completado `increase_weight()`.
* **Lema 1:** Cada hilo activo puede estar en $O$ como máximo una vez simultáneamente, puesto que tras ofender, el hilo no vuelve a invocar `load()` sobre $V$ hasta salir de `increase_weight()`. Por ende:
  $$|O| \le P$$
* **Lema 2:** Por inducción sobre la secuencia de micro-pasos atómicos, el peso en la celda compartida satisface en todo instante:
  $$w \ge P - |O|$$
* **Conclusión:** Dado que $|O| \le P$ y la constante $C \ge 2P$ (Regla R-1):
  $$w \ge P - P = 0 \quad \blacksquare$$

### 3.2. Teorema 2: El peor caso de `increase_weight` está estrictamente acotado por $P$
1. En cada iteración fallida del bucle CAS (línea 4 de Algoritmo 2), la celda no cambió de puntero y su peso no es mayor que `actual` (de lo contrario se activa la salida temprana en la línea 7).
2. En consecuencia, el nuevo peso observado `actual'` satisface estrictamente:
   $$\text{actual}' < \text{actual} \le P - 1$$
3. La secuencia de pesos esperados forma una cadena estrictamente decreciente de números enteros no negativos:
   $$P - 1 \ge w_0 > w_1 > w_2 > \dots \ge 0$$
4. Por el principio del palomar, la longitud máxima de esta cadena es a lo sumo $P$.
5. **Conclusión:** `increase_weight()` ejecuta a lo sumo $P$ intentos de CAS, garantizando complejidad temporal en el peor caso de **$O(P)$ pasos propios $\implies$ WAIT-FREE $\blacksquare$**.

---

## 4. Matriz Comparativa Exhaustiva frente a los 8 Adversarios

| Adversario | Garantía de Progreso | Complejidad Temporal (`load`) | Complejidad Temporal (`store`) | Sobrecoste Memoria | Instrucciones Clave | Limitación Fatal |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **Ingenua** | Bloqueante / Rota | $O(1)$ | $O(1)$ | 0 | `load` + `fetch_add` | Corrupción *Use-After-Free*. |
| **Libstdc++** | Bloqueante | Depende del cerrojo | Depende del cerrojo | 0 | `lock bts`, `futex` | Congela hilos; latencia $p99$ de 16 µs. |
| **Williams** | *Lock-Free* | Bucle CAS | Bucle CAS | 0 | `lock cmpxchg16b` | Inanición individual por reintentos de CAS. |
| **Meta Folly** | *Lock-Free* $\to$ Bloq. | Bucle CAS | Bucle CAS | 0 | `lock cmpxchg` | Límite $C=8192$; refcount 32 bits. |
| **Anderson** | *Wait-Free* (Snapshot) | $O(1)$ | $O(1)$ | $\mathbf{> 0}$ (Listas SMR) | Ranuras Hazard Pointers | Reclamación diferida; no libera al instante. |
| **Mutex** | Bloqueante | $O(1)$ (si libre) | $O(1)$ (si libre) | 0 | `lock cmpxchg`, `futex` | Cola $p99$ masiva (27.6 µs por context switch). |
| **Sundell** | *Wait-Free* | $O(1)$ | $\mathbf{\Theta(P)}$ | 0 | Protocolo de Ayuda | Escrituras $\Theta(P)$ saturan el bus de memoria. |
| **Detlefs** | *Lock-Free* | Teórico | Teórico | 0 | Inexistente (DCAS) | Hardware no existe en Intel, AMD ni ARM. |
| **Autor (2024)** | **Wait-Free** | **$O(1)$ habitual / $O(P)$ peor caso** | **$O(1)$** | **0** | `fetch_sub`, `exchange` | `compare_and_set` es solo Lock-Free. |

---

## 5. Resumen de Hallazgos Experimentales en la Réplica (Intel i5-10400, 12 Hilos)

1. **Corrección de Memoria:** AddressSanitizer y ThreadSanitizer confirman 0 violaciones de punteros en 1.6 millones de operaciones del autor y detección fulminante de *heap-use-after-free* en la versión ingenua.
2. **Robustez de Invariantes:** El simulador estocástico en Node.js completó 20,000 intercalados caóticos con 0 violaciones para el algoritmo oficial, mientras que las variantes sin reserva, sin salida temprana y con $C=P$ fallaron en 2 a 7 pasos atómicos.
3. **Escalabilidad de Rendimiento:** En una pila de Treiber con contención de lectura ($n=1, u=1\%$), el autor alcanzó **39.13 Mop/s**, superando a Libstdc++ (**1.58 Mop/s**, ratio 24.8×) y a Williams (**5.34 Mop/s**, ratio 7.3×).
4. **Comportamiento en Alta Contención de Escritura:** En $n=1, u=50\%$, el Mutex superó al autor (2.91 vs 2.32 Mop/s) debido a que las actualizaciones de la pila requieren el bucle CAS de `compare_and_set` que sufre interferencia por los lectores.
5. **Comportamiento de Latencia en la Cola ($p99$):**
   * Autores: Mediana = 269 ns, $p99 = \mathbf{830\text{ ns}}$ (sub-microsegundo garantizado).
   * Mutex: Mediana = 61 ns, $p99 = \mathbf{27,641\text{ ns}}$ (explosión por expulsión de CPU y llamadas a `sys_futex`).

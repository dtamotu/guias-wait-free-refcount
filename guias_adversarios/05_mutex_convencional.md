# Guía de Adversario: Mutex Convencional (`std::mutex` + `std::shared_ptr`)

> **Paper de Referencia:** *A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting* (de Wolff et al., Euro-Par 2024).  
> **Clasificación del Rival:** La solución clásica de exclusión mutua directa / Línea base bloqueante.  
> **Código en la Réplica:** Implementación `struct Mutex` en `codigo/bench.cpp`.

---

## 1. Explicación Detallada (Nivel Técnico Avanzado)

### 1.1. Arquitectura y Código
Antes de que existieran primitivas libres de bloqueos para punteros compartidos, el enfoque canónico de la industria era encapsular un `std::shared_ptr<T>` ordinario junto con un cerrojo de exclusión mutua `std::mutex`:

```cpp
template <class T>
struct CeldaMutex {
    std::mutex m;
    std::shared_ptr<T> p;
};

// Lectura protegida:
std::shared_ptr<T> load(CeldaMutex<T>& c) {
    std::lock_guard<std::mutex> g(c.m);
    return c.p; // Incrementa el rc del bloque de control dentro del candado
}

// Escritura protegida:
void store(CeldaMutex<T>& c, std::shared_ptr<T> nuevo) {
    std::shared_ptr<T> viejo;
    {
        std::lock_guard<std::mutex> g(c.m);
        c.p.swap(nuevo); // Intercambio rápido dentro del candado
    } // El puntero viejo se destruye aquí, FUERA del candado, para no alargar la sección crítica
}
```

### 1.2. Análisis Formal de Latencia: "La Mediana Engaña, la Cola Delata"
La réplica experimental del proyecto (ejecutada en Intel i5-10400 con 12 hilos de hardware) reveló un fenómeno estadístico fundamental que se debe comprender a fondo:

| Implementación | Mediana ($p50$) de `load` | Percentil 75 ($p75$) | Percentil 99 ($p99$) | Ratio Cola ($p99 / p50$) |
|---|---|---|---|---|
| **Autores (*de Wolff et al.*)** | **269 ns** | **374 ns** | **830 ns (0.83 µs)** | **3.08×** (muy compacto) |
| **Mutex Convencional** | **61 ns** | **78 ns** | **27,600 ns (27.6 µs)** | **452.4×** (explosión masiva) |
| **Libstdc++ (GCC)** | 3,060 ns | 4,210 ns | 16,000 ns (16.0 µs) | 5.22× |

#### ¿Por qué la mediana del Mutex es tan engañosamente baja (61 ns)?
En procesadores x86-64 modernos, si un hilo llega y encuentra el mutex completamente libre (*uncontended lock*), la adquisición del cerrojo se resuelve en espacio de usuario mediante una sola instrucción `lock cmpxchg` que golpea la caché L1 en apenas ~15–20 ns. Si el hilo tiene la suerte de no colisionar, entra y sale casi instantáneamente.

#### ¿Por qué el percentil 99 ($p99$) explota a 27.6 µs (33 veces peor que el Autor)?
Cuando 12 hilos intentan adquirir el cerrojo a la vez:
1. Uno solo gana la carrera del CAS.
2. Los 11 hilos restantes fallan el cerrojo en espacio de usuario tras unos pocos ciclos de *spin*.
3. La biblioteca de hilos de Linux (`libpthread`) ejecuta una llamada al sistema **`sys_futex`** para suspender a los hilos perdedores en el kernel del sistema operativo.
4. Un salto al kernel con cambio de contexto (*context switch*), desalojo de hilo y posterior reactivación por interrupción cuesta entre **3 y 10 microsegundos por hilo**.
5. Los hilos al final de la cola acumulan un retraso de más de **27 microsegundos**.

### 1.3. La Anomalía Honesta: ¿Por qué el Mutex gana en Rendimiento con $n=1, u=50\%$?
En la prueba de 1 pila con 50% de operaciones de actualización concurrente:
* **Mutex:** **2.9 Mop/s**.
* **Autores:** **2.32 Mop/s**.
* **Explicación Teórica:** El algoritmo de de Wolff et al. es *wait-free* para `load`, `store` y `swap`, pero su función `compare_and_set` (utilizada por la Pila de Treiber en cada push/pop) es **Lock-Free**. En una sola pila con 12 hilos leyendo y escribiendo continuamente, las lecturas modifican constantemente el peso de la celda mediante `fetch_sub`. Esto hace que el escritor sufra fallos de CAS repetidos en su bucle de `compare_and_set`. En cambio, el Mutex serializa a los escritores de manera brutal pero ordenada en $O(1)$ directo una vez adquirido el cerrojo.

---

## 2. Versión Dummie (Explicación para Principiantes)

### 2.1. La Analogía del Mundo Real: "El Baño con Cerrojo en el Concierto de Rock"
Imagina el baño público de un estadio:
* **A las 3 de la mañana (Mediana - 61 nanosegundos):** No hay nadie en el estadio. Llegas corriendo, empujas la puerta, cierras el cerrojo, te lavas las manos y sales en 5 segundos. Parece la cosa más rápida del universo.
* **En el intermedio del concierto (Percentil 99 - 27.6 microsegundos):** 50 personas corren al baño al mismo tiempo. El cerrojo se traba. El guardia de seguridad tiene que empezar a intervenir para ordenar la fila a gritos (llamada al kernel `futex`). La persona que quedó al final de la fila espera 27 minutos retorciéndose con ganas de orinar.

### 2.2. Resumen "En Cristiano" (3 Balas Clave)
1. **¿Qué hace?** Pone un cerrojo simple (`std::mutex`) en la puerta del puntero.
2. **¿Por qué es engañoso?** Si miras el promedio o la mediana, parece ultra-rápido; pero si miras al 1% de los usuarios con peor suerte ($p99$), sufren retrasos monstruosos de hasta 27 microsegundos por culpa de los cambios de contexto del sistema operativo.
3. **¿Qué inventó el autor para vencerlo?** Eliminó la puerta y el cerrojo por completo. En el algoritmo del autor no hay fila ni cerrojo: los hilos entran y salen fluidamente, garantizando que nadie jamás sufra una espera impredecible.

### 2.3. Preguntas Tontas que Todos nos Hacemos
* *¿Qué significa "la mediana engaña, la cola delata"?*  
  Imagina cruzar un río que en promedio mide 40 centímetros de profundidad... pero en la mitad hay un hoyo negro de 15 metros donde te ahogas. La mediana es el promedio engañoso; la cola ($p99$) es el hoyo negro que destruye los servidores en producción.
* *¿Por qué en un caso raro de muchas escrituras el Mutex le gana al Autor?*  
  Porque cuando todos quieren escribir desesperadamente en un solo punto, un candado actúa como un policía de tránsito que hace pasar a uno por uno en fila india estricta. El autor, al no tener policía, hace que los escritores choquen entre sí reintentando.

### 2.4. Veredicto Dummie
> **Calificación:** 5 / 10.  
> **Veredicto:** Muy simple de programar, pero peligroso en sistemas de tiempo real debido a sus colas de latencia extremas cuando hay contención.

# Guía de Adversario: La Implementación Ingenua (La Carrera Mortal *Read-Reclaim*)

> **Paper de Referencia:** *A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting* (de Wolff et al., Euro-Par 2024).  
> **Clasificación del Rival:** El intento "inocente" y fallido / Demostración empírica de la vulnerabilidad *Use-After-Free*.  
> **Código en la Réplica:** Implementación `struct Ingenua` en `codigo/estres_asan.cpp`.

---

## 1. Explicación Detallada (Nivel Técnico Avanzado)

### 1.1. La Falacia del Puntero Atómico Ordinario
Muchos programadores novatos o intermedios en C++ creen erróneamente que declarar un puntero atómico ordinario `std::atomic<T*>` es suficiente para compartir punteros con conteo de referencias sin necesidad de candados. Esta falsa creencia da lugar a la implementación **Ingenua (*Naive*)**:

```cpp
struct Libro { 
    std::atomic<long> rc{1}; 
    long dato = 42; 
};

struct Ingenua {
    std::atomic<Libro*> cartel{nullptr};

    void store(Libro* nuevo) {
        nuevo->rc.fetch_add(1);
        soltar(cartel.exchange(nuevo)); 
    }

    Libro* load() {
        // PASO 1: Leer el puntero compartido
        Libro* l = cartel.load(); 
        
        // --- VENTANA VULNERABLE (Nanosegundos mortales) ---
        // Si el sistema operativo pausa este hilo justo aquí...
        
        // PASO 2: Apuntarse en el contador del objeto
        if (l) l->rc.fetch_add(1); 
        return l;
    }

    static void soltar(Libro* l) {
        if (l && l->rc.fetch_sub(1) == 1) {
            delete l; // ¡Destrucción y liberación de memoria física!
        }
    }
};
```

### 1.2. Anatomía de la Carrera *Read-Reclaim* (Paso a Paso)
Consideremos dos hilos concurrentes, **Ana (Lectora)** y **Beto (Escritor)**:
1. **Estado Inicial:** `cartel` apunta al objeto $A$ en la dirección de memoria `0x5000`. El objeto $A$ tiene $rc = 1$ (solo referenciado por el cartel).
2. **Paso 1 (Ana):** Ana ejecuta `cartel.load()`. Su variable local `l` recibe la dirección `0x5000`.
3. **Interrupción:** El planificador del kernel o una interrupción de hardware pausa a Ana antes de que pueda ejecutar el Paso 2.
4. **Paso 2 (Beto):** Beto llega y hace `store(B)`.
   * Pone el nuevo objeto $B$ en `cartel`.
   * El intercambio devuelve el viejo objeto $A$.
   * Beto llama a `soltar(A)`.
   * Como $A$ solo tenía $rc = 1$, la resta lo deja en $0$.
   * Beto ejecuta `delete A`. El asignador de memoria (glibc / `malloc`) marca el bloque `0x5000` como libre y lo devuelve al sistema operativo o a su lista de bloques disponibles.
5. **El Despertar Mortal de Ana:** Ana despierta y continúa su ejecución ciega:
   $$\text{Ana ejecuta: } l\text{->}rc\text{.fetch\_add}(1) \implies \text{escribe en la dirección libre } \mathtt{0x5000}$$
6. **Consecuencia:** **`Heap-Use-After-Free`**. Ana acaba de escribir en memoria que ya no le pertenece. Esto corrompe las estructuras del asignador de memoria, provoca fallos de segmentación (`SIGSEGV`) aleatorios o abre la puerta a vulnerabilidades de ejecución remota de código (RCE).

### 1.3. Por qué la Ventana es Casi Invisible pero Catastrófica
En condiciones normales de laboratorio sin herramientas especiales, la ventana temporal entre el Paso 1 y el Paso 2 dura apenas **unos pocos nanosegundos**. El código puede pasar miles de pruebas unitarias sin fallar jamás, engañando a los ingenieros. Sin embargo, en un servidor de producción bajo alta carga con millones de peticiones por segundo, la carrera ocurrirá inevitablemente y tumbará el servicio.

---

## 2. Versión Dummie (Explicación para Principiantes)

### 2.1. La Analogía del Mundo Real: "El Fantasma del Libro Quemado"
Imagina una biblioteca pública:
* **Ana (la lectora):** Ana entra a la biblioteca y mira el cartel de anuncios que dice: *"El libro de Harry Potter está en la mesa 4"*. Ana lee el cartel y empieza a caminar hacia la mesa 4. Pero en el camino se detiene 3 segundos a amarrarse los cordones de las zapatillas.
* **Beto (el bibliotecario):** En esos 3 segundos, Beto llega a la mesa 4. Ve que no hay nadie leyendo el libro, revisa la hoja de firmas y ve que nadie lo tiene prestado. Como el libro está viejo, Beto lo agarra, lo mete en una trituradora de papel y quema los restos en el incinerador. El libro ya no existe en el universo.
* **El choque de Ana:** Ana termina de amarrarse las zapatillas, llega a la mesa 4 con su lapicero en la mano y, sin mirar si el libro está ahí, estampa su firma con fuerza en el aire donde antes estaba la portada. ¡Raya la mesa de madera y le clava la punta del lapicero en la mano a otra persona que se acababa de sentar!

### 2.2. Resumen "En Cristiano" (3 Balas Clave)
1. **¿Qué hace?** Es lo primero que a cualquiera se le ocurriría programar: lee primero la dirección del puntero y luego va a sumarse al contador.
2. **¿Por qué es mortal?** Porque son dos pasos separados. En el microsegundo entre el paso 1 y el paso 2, otro hilo puede destruir y borrar el objeto, haciendo que tu programa intente escribir en un muerto (*Use-After-Free*).
3. **¿Qué inventó el autor para vencerlo?** Unió los dos pasos en uno solo: el cartel viene con un **talonario de pases prepagados**. Al mismo tiempo que lees el puntero, arrancas tu pase de un solo tirón atómico. Beto jamás podrá quemar el libro mientras tú tengas tu pase en la mano.

### 2.3. Preguntas Tontas que Todos nos Hacemos
* *¿Por qué no podemos simplemente verificar si el puntero sigue vivo antes de sumarle?*  
  Porque esa verificación también tomaría otro microsegundo. Si verificas y dices: *"Sigue vivo"*, justo después de verificar el otro hilo puede destruirlo antes de que sumes. Cualquier solución de dos pasos está condenada a morir.
* *¿Cómo se detecta este error?*  
  Con una herramienta llamada **AddressSanitizer (ASan)**, que pinta la pantalla de rojo escandaloso y te dice exactamente qué hilo quemó el objeto y qué hilo intentó escribir en su tumba.

### 2.4. Veredicto Dummie
> **Calificación:** 0 / 10 (Prohibido terminantemente en producción).  
> **Veredicto:** Una bomba de tiempo de memoria que parece funcionar en tu casa pero explota en el servidor de la empresa.

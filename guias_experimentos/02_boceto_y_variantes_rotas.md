# Guía de Experimento 2: El Boceto Didáctico y las Variantes Rotas

> **Archivos de Código:** `codigo/boceto/atomic_shared.hpp` y `codigo/boceto/prueba.cpp`  
> **Objetivo Científico:** Aislar los principios matemáticos del paper en un código compacto y verificar experimentalmente qué ocurre cuando se violan las dos reglas de oro: **R-1 ($C \ge 2P$)** y **R-2 (Salida Temprana)**.

---

## 1. Explicación Detallada (Nivel Técnico Avanzado)

### 1.1. Empaquetado de Puntero y Peso en 64 bits (*Pointer Tagging*)
En procesadores x86-64 modernos, las direcciones de memoria virtual utilizan 48 bits (permitiendo direccionar hasta 256 Terabytes de RAM). Los 16 bits superiores (del bit 48 al 63) están disponibles como bits de etiqueta (*tagged pointer*).
* **Definición de Constantes:**
  ```cpp
  constexpr int      BITS_DIR    = 48;
  constexpr uint64_t UN_TICKET   = uint64_t(1) << BITS_DIR; // Bit 48 en 1
  constexpr uint64_t MASCARA_DIR = UN_TICKET - 1;          // Bits 0 al 47 en 1
  ```
* **Extracción y Empaquetado:**
  * `pack(p, w) = (w << 48) | uintptr_t(p)`
  * `puntero(v) = (Objeto*)(v & MASCARA_DIR)`
  * `peso(v)    = v >> 48`
* **Magia del `fetch_sub`:** Restar un ticket de peso es simplemente ejecutar `value.fetch_sub(UN_TICKET)`. La dirección del puntero en los bits bajos no se altera en absoluto.

### 1.2. Las Dos Reglas de Oro Teóricas del Paper
1. **Regla R-1 ($C \ge 2P$):** La capacidad total de tickets $C$ debe ser al menos el doble del número máximo de hilos $P$. Esto garantiza que incluso si los $P$ hilos deciden ofender al mismo tiempo (bajar de peso simultáneamente), el peso jamás bajará a números negativos.
2. **Regla R-2 (Salida Temprana en `increase_weight`):** Al recargar, si el CAS falla porque otro hilo ya recargó y dejó el peso en un valor superior al que vimos (`peso(visto) > actual`), **el hilo debe abortar inmediatamente su intento, devolver su reserva y salir**.

### 1.3. Las Variantes Rotas y los Resultados de Laboratorio (Capturas 04 y 05)

El banco de pruebas ejecuta 8 hilos ($P=8$), cada uno realizando 50,000 operaciones sobre la celda compartida.

```text
========================================================================================
Variante Compilada            Errores Memoria    Objetos Sin Liberar    Máx Intentos CAS
========================================================================================
1. Boceto Normal (Paper)                    0                      0              7 (≤ 8)
2. SIN_SALIDA temprana                      0                      0             38 (> 8)
3. Con C = P (VAR_C=8, R-1 rota)       50,060                  3,055                    7
========================================================================================
```

#### Análisis de los Resultados:
* **Boceto Normal:** Cero errores de memoria y el número máximo de intentos de CAS fue de **7**, cumpliendo estrictamente con la cota teórica del paper ($\text{intentos} \le P = 8$). Es rigurosamente **Wait-Free**.
* **Variante `SIN_SALIDA`:** Aunque no hay corrupción de memoria inmediata, el número máximo de intentos de CAS **se dispara a 38 intentos (muy superior a $P=8$)**. Al eliminar la salida temprana, los hilos entran en bucles redundantes de reintento, perdiendo la cota finita y degradándose a **Lock-Free**.
* **Variante $C = P$ (violación de R-1):** Se desata el desastre: **50,060 errores de memoria** y **3,055 objetos corruptos sin liberar**. Como el colchón de seguridad era insuficiente, el peso sufrió un subdesborde (*underflow*), interpretándose como $2^{16}-1$ tickets fantasmas que desencadenaron dobles liberaciones y *use-after-free*.

---

## 2. Versión Dummie (Explicación para Principiantes)

### 2.1. La Analogía del Mundo Real: "La Billetera Mágica y la Fiesta de Pizzas"
Imagina que vas a organizar una fiesta para 8 amigos hambrientos ($P = 8$):
* **El truco de la billetera de 64 bits:** En un solo bolsillo tienes un billete largo. A la izquierda está escrita la cantidad de pizzas que quedan (el peso), y a la derecha la dirección de la casa donde es la fiesta (el puntero). Cuando alguien agarra una porción de pizza, le resta 1 al número de la izquierda con un marcador en medio segundo sin tocar la dirección.
* **La Regla 1 ($C \ge 2P$ - La reserva de comida):** Tienes que tener al menos 16 porciones ($2 \times 8$). Si compraste solo 8 porciones ($C=8$), y los 8 amigos hambrientos se lanzan sobre la mesa al mismo segundo, la mesa queda vacía de golpe y la gente empieza a morderse los dedos (¡50,000 errores de memoria!).
* **La Regla 2 (Salida Temprana - La compra de emergencia):** Cuando quedan pocas pizzas, tú sales corriendo a la pizzería a comprar más. Pero cuando vas entrando por la puerta, ves que tu amigo Beto ya llegó con 3 cajas familiares gigantes. ¿Qué haces? ¿Sigues comprando pizza como un terco o te regresas a la fiesta a comer? ¡Te regresas a la fiesta! Si eres terco y sigues comprando (`SIN_SALIDA`), te quedas atrapado 38 viajes inútiles a la pizzería.

### 2.2. Cómo Probarlo Tú Mismo en la Terminal
1. Entra a la carpeta del boceto:
   ```bash
   cd ~/Documentos/Davichi/proyecto/replica-wait-free-refcount/codigo/boceto
   ```
2. Compila y corre el boceto normal:
   ```bash
   g++ -O2 prueba.cpp -o prueba_normal && ./prueba_normal
   ```
   *(Verás: `0 errores, 0 sin liberar, max intentos = 7 ≤ 8`).*
3. Compila la versión rota sin salida temprana:
   ```bash
   g++ -O2 -DSIN_SALIDA prueba.cpp -o prueba_sin_salida && ./prueba_sin_salida
   ```
   *(Verás: `max intentos = 38 > 8`. ¡Dejó de ser wait-free!).*
4. Compila la versión con $C=8$:
   ```bash
   g++ -O2 -DVAR_C=8 prueba.cpp -o prueba_c8 && ./prueba_c8
   ```
   *(Verás miles de errores de memoria en pantalla).*

### 2.3. Resumen en 3 Balas para Dummies
1. **¿Qué prueba este experimento?** Demuestra con números reales que las dos reglas matemáticas del paper no son un capricho: son las columnas que sostienen todo el edificio.
2. **¿Qué pasa sin salida temprana?** El programa se vuelve torpe y repite intentos en bucle (hasta 38 veces), dejando de ser *wait-free*.
3. **¿Qué pasa si achicas el peso $C$?** Ocurre un desastre atómico con más de 50,000 corrupciones de memoria.

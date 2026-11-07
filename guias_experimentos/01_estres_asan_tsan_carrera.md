# Guía de Experimento 1: Detección de la Carrera con AddressSanitizer y ThreadSanitizer

> **Archivos de Código:** `codigo/estres_asan.cpp` y `codigo/correr_tsan.sh`  
> **Objetivo Científico:** Demostrar empíricamente la existencia de la carrera *read-reclaim* (*heap-use-after-free*) en la versión ingenua y verificar la inmunidad total del código de los autores.

---

## 1. Explicación Detallada (Nivel Técnico Avanzado)

### 1.1. Principio de Funcionamiento de AddressSanitizer (ASan)
AddressSanitizer instrumenta el código en tiempo de compilación mediante dos mecanismos fundamentales:
1. **Zonas Rojas (*Redzones*):** Rodea cada bloque de memoria asignado en el heap (`malloc` o `new`) con zonas prohibidas no direccionables.
2. **Memoria Sombra (*Shadow Memory*):** Mapea cada 8 bytes de la memoria virtual ordinaria a 1 byte en un área especial de memoria sombra que codifica el estado de validez (libre, asignado, zona roja).
3. **Interceptación de Liberación:** Cuando se ejecuta `delete p`, ASan envenena inmediatamente la memoria sombra correspondiente al bloque (`poisoned memory`), marcándola como inaccesible antes de devolverla a la lista de bloques libres.

### 1.2. El Código en `codigo/estres_asan.cpp`
El código compara dos implementaciones bajo una carga idéntica de 8 hilos ejecutando 200,000 operaciones por hilo (un total de 1,600,000 operaciones, con 10% de escrituras `store` y 90% de lecturas `load`):

```cpp
// Versión Ingenua: dos pasos separados
Libro* load() {
    Libro* l = cartel.load();      // Paso 1: Lee puntero compartido
    std::this_thread::yield();     // Ensancha deliberadamente la ventana de nanosegundos
    if (l) l->rc.fetch_add(1);     // Paso 2: Incrementa rc... ¡PELIGRO!
    return l;
}
```

La llamada a `std::this_thread::yield()` cede voluntariamente la CPU al planificador del sistema operativo, garantizando que otro hilo escritor intermedie y destruya el objeto antes de que el lector ejecute el paso 2.

### 1.3. La Salida Real de AddressSanitizer (Captura 02)
Al ejecutar `./bin/estres_asan ingenua`, ASan aborta la ejecución con un reporte de error detallado:
```text
=================================================================
==13253==ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000070
WRITE of size 8 at 0x502000000070 thread T1
    #0 0x5608df4f54e1 in Ingenua::load() codigo/estres_asan.cpp:31
    #1 0x5608df4f494f in ejecutar_ingenua()::{lambda(int)#1}::operator()
0x502000000070 is located 0 bytes inside of 16-byte region [0x502000000070,0x502000000080)
freed by thread T2 here:
    #0 0x7fa2ea0b5cb5 in operator delete(void*, unsigned long)
    #1 0x5608df4f451d in Ingenua::soltar(Libro*) codigo/estres_asan.cpp:26
    #2 0x5608df4f46e5 in Ingenua::store(Libro*) codigo/estres_asan.cpp:27
```
* **Análisis de la Traza:** La traza prueba inequívocamente la teoría del paper: el hilo `T2` destruyó el objeto en la línea 26 (`delete l`), y milisegundos después el hilo `T1` intentó escribir en la dirección `0x502000000070` en la línea 31 (`l->rc.fetch_add(1)`).

### 1.4. Comportamiento del Código de los Autores (Captura 03)
Al compilar y ejecutar `./bin/estres_asan autores 8 200000`:
* **Resultado:** `terminado en 56 ms sin errores de memoria (suma de comprobacion 64000000)`.
* **Cero violaciones de memoria:** El `load()` de los autores ejecuta un único `fetch_sub(UN_TICKET)` sobre la celda compartida. La lectura del puntero y la adquisición del peso ocurren en una sola instrucción atómica de hardware indivisible.

### 1.5. El Rol de ThreadSanitizer (TSan - `correr_tsan.sh`)
Mientras que ASan vigila la memoria física, **ThreadSanitizer (TSan)** vigila las relaciones temporales de concurrencia (*Happens-Before*) mediante relojes vectoriales. TSan demuestra que en el código de los autores no existen carreras de datos (*data races*) sobre la palabra empaquetada ni sobre el bloque de control gracias a las barreras `std::memory_order_acquire` y `std::memory_order_release`.

---

## 2. Versión Dummie (Explicación para Principiantes)

### 2.1. La Analogía del Mundo Real: "El Inspector de Sanidad y el Restaurante"
Imagina un restaurante con dos cocineros:
* **El Cocinero Ingenuo:** Ana saca un pollo crudo del congelador y lo deja en el mostrador para ir a buscar un cuchillo. Mientras busca el cuchillo, Beto ve el pollo, dice *"este pollo se venció"* y lo tira a la basura con lejía. Ana regresa distraída con los ojos cerrados e intenta freír la bolsa de basura vacía con lejía.
* **El Inspector ASan:** Es un policía con un megáfono gigante que vigila la cocina con rayos X. En cuanto Ana intenta tocar la bolsa de basura envenenada, el policía hace sonar una alarma que despierta a todo el barrio, saca una tarjeta roja y clausura el restaurante en el acto.
* **El Cocinero del Paper:** Ana y Beto usan un dispensador sellado donde el pollo y el cuchillo salen en una sola cápsula sellada automática. El inspector de sanidad revisa 1,600,000 platos servidos en 56 milisegundos y no encuentra ni una sola mota de polvo.

### 2.2. Cómo Probarlo Tú Mismo en la Terminal (Paso a Paso)
1. Abre tu terminal de Linux.
2. Entra a la carpeta del proyecto:
   ```bash
   cd ~/Documentos/Davichi/proyecto/replica-wait-free-refcount/codigo
   ```
3. Compila con AddressSanitizer:
   ```bash
   g++ -std=c++20 -O1 -g -fsanitize=address -pthread estres_asan.cpp -o estres_asan
   ```
4. Corre la versión ingenua para ver el choque:
   ```bash
   ./estres_asan ingenua
   ```
   *(Verás el pantallazo rojo con el mensaje `ERROR: AddressSanitizer: heap-use-after-free`).*
5. Corre la versión de los autores para ver la perfección:
   ```bash
   ./estres_asan autores
   ```
   *(Verás: `terminado en 56 ms sin errores de memoria`).*

### 2.3. Resumen en 3 Balas para Dummies
1. **¿Qué prueba este experimento?** Prueba que el problema no era teórico ni un invento de los autores: la versión ingenua explota y destruye la memoria en la vida real.
2. **¿Qué hace AddressSanitizer?** Pinta de rojo la pantalla y te muestra con nombre y apellido qué hilo destruyó el objeto y qué hilo intentó usar al muerto.
3. **¿Cuál fue el resultado del autor?** 1,600,000 operaciones en 56 milisegundos con cero choques y cero errores de memoria.

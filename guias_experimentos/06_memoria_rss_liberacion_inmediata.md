# Guía de Experimento 6: Medición de Memoria (Pico de RSS) y Liberación Inmediata

> **Comando de Medición:** `/usr/bin/time -v ./bench rendimiento 1.0` (o `codigo/medir_memoria.sh`)  
> **Objetivo Científico:** Evaluar la huella de memoria física en el sistema operativo (*Maximum Resident Set Size*, RSS) para contrastar la propiedad de **Cero Sobrecoste de Memoria y Liberación Inmediata** frente a los esquemas de reclamación diferida (*Deferred Reclamation* como Anderson / CDRC).

---

## 1. Explicación Detallada (Nivel Técnico Avanzado)

### 1.1. Resident Set Size (RSS) y Gestión de Memoria en Linux
El **Resident Set Size (RSS)** representa la cantidad exacta de memoria RAM física que el sistema operativo Linux tiene asignada en las tablas de páginas de un proceso (sin contar la memoria virtual que ha sido enviada al área de intercambio *swap* o que aún no ha sufrido un fallo de página).
* **El Comando de Medición:**
  ```bash
  /usr/bin/time -v ./bench rendimiento 1.0
  ```
  La línea clave que se debe inspeccionar en la salida de `time` es:
  `Maximum resident set size (kbytes): XXXX`

### 1.2. Liberación Inmediata (*Immediate Reclamation*) vs Reclamación Diferida (*Deferred*)
En C++ idiomático y en el diseño original del conteo de referencias (desde Collins en 1960), existe un contrato sagrado:
$$\text{Si } rc == 0 \implies \text{se invoca el destructor y se libera la memoria en ese mismo instante}$$

#### La Ruptura de Esquemas como Anderson (CDRC) y Hazard Pointers:
1. Cuando un hilo retira la última referencia a un nodo de una pila concurrente, el nodo no se puede borrar porque un lector rezagado podría estar leyendo sus campos a través de un puntero de riesgo.
2. El nodo muerto se encola en una **lista de retiro (*retire list*)**.
3. Mientras los hilos sigan operando a alta velocidad, la lista de retiro acumula miles de nodos muertos.
4. **Consecuencia en RSS:** El pico de RSS se infla dramáticamente, aumentando la huella de caché y provocando fragmentación en el montón (*heap*).

#### El Triunfo de de Wolff et al. 2024 (*Zero Space Overhead*):
* **Cero Listas de Retiro:** No existen búferes por hilo, ni listas de nodos pendientes, ni épocas globales.
* **Destrucción Inmediata:** Gracias al sistema de tickets prepagados, en cuanto el peso sobrante se resta al puntero viejo en el `store()`, si la hoja llega a 0, se llama a `delete` de inmediato.
* **Huella de Memoria Mínima:** El algoritmo de los autores consume exactamente el mismo RSS mínimo que un programa secuencial ordinario con punteros clásicos.

---

## 2. Versión Dummie (Explicación para Principiantes)

### 2.1. La Analogía del Mundo Real: "La Prueba de la Balanza"
Imagina poner a los 4 competidores sobre una balanza de peso corporal:
* **El competidor Anderson (con bolsas de basura):** Corre rápido, pero va cargando 20 bolsas de basura en los hombros porque no las puede soltar en la calle (retiene memoria en listas de espera). Al pesarse en la balanza, pesa 150 kilos (pico de RSS alto).
* **El competidor del Autor (atleta limpio):** Corre igual de rápido o más, pero en cuanto termina de tomarse una botella de agua, la deposita en el tacho de basura en ese mismo segundo. No carga basura ni engorda. Al pesarse en la balanza, pesa solo 60 kilos (pico de RSS mínimo y perfecto).

### 2.2. Cómo Medirlo Tú Mismo en la Terminal
1. Entra a la carpeta de código:
   ```bash
   cd ~/Documentos/Davichi/proyecto/replica-wait-free-refcount/codigo
   ```
2. Mide la memoria con el comando de tiempo de Linux:
   ```bash
   /usr/bin/time -v ./bench rendimiento 1.0
   ```
3. Busca la línea que dice:
   `Maximum resident set size (kbytes)`
4. Comprueba que el algoritmo de los autores no tiene fugas de memoria y mantiene una huella compacta de apenas unos pocos megabytes.

### 2.3. Resumen en 3 Balas para Dummies
1. **¿Qué mide este experimento?** Mide cuánta memoria RAM real gasta el programa mientras trabaja a toda velocidad.
2. **¿Por qué el autor no gasta memoria extra?** Porque no guarda listas de espera de objetos viejos: cuando algo ya no sirve, lo destruye en ese mismo microsegundo.
3. **¿Cuál es la ventaja?** Que tu programa jamás se quedará sin memoria RAM ni provocará caídas de rendimiento por acumulación de basura.

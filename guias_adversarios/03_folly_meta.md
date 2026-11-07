# Guía de Adversario: Meta Folly (`folly::atomic_shared_ptr`)

> **Paper de Referencia:** *A Fast Wait-Free Solution to Read-Reclaim Races in Reference Counting* (de Wolff et al., Euro-Par 2024).  
> **Clasificación del Rival:** Biblioteca industrial de alto rendimiento de Facebook / Meta.  
> **Código Original:** [facebook/folly en GitHub](https://github.com/facebook/folly).

---

## 1. Explicación Detallada (Nivel Técnico Avanzado)

### 1.1. Arquitectura y Compromisos de Diseño Industrial
`folly::atomic_shared_ptr` es la implementación en producción utilizada en la infraestructura a hiperescala de Meta (servidores de Facebook, Instagram, WhatsApp). Al igual que la de Anthony Williams, se basa en la técnica de **Split Reference Count**, pero con un compromiso de diseño crítico:
* **Contador de 32 bits:** Para ser compatible con el ecosistema existente de Folly y minimizar el tamaño de las estructuras en la memoria caché L1/L2, Meta forzó que el contador de referencias total sea de solo 32 bits (incluso en arquitecturas de 64 bits).
* **Techo Reducido ($C = 8192$):** Como el contador global de 32 bits corre peligro de desbordamiento si se le suman valores gigantes, Folly tuvo que fijar el valor máximo de peso o conteo local en un valor muy bajo: $C = 8192$ ($2^{13}$).

### 1.2. El Bucle de Lectura y la Degradación a Bloqueante
* **Bucle CAS en `load()`:** A diferencia del algoritmo de de Wolff et al. (que ejecuta un `fetch_sub` ciego en $O(1)$), Folly ejecuta un bucle de `compare_exchange` en cada lectura para evitar que el contador local desborde o se corrompa.
* **El Peligro Oculto (Degradación a Bloqueante):** Si en un momento de altísima contención concurren **más de $C$ hilos** operando sobre el mismo puntero (más de 8,192 lecturas simultáneas no consolidadas), la implementación de Folly **abandona la propiedad Lock-Free y se degrada a un mecanismo bloqueante**. Esto significa que los hilos excedentes son puestos a dormir o atrapados en un cerrojo para no corromper la memoria.
* **Sobrecarga de Sincronización:** Cada lectura genera invalidación de la línea de caché en todos los demás núcleos debido a la continua contención de CAS.

### 1.3. Resultados Experimentales en el Paper (Sección 6)
* **Rendimiento con 144 hilos (4 procesadores Intel Xeon E7-8867):**
  * Con 1 pila y contención moderada de actualizaciones, el algoritmo de de Wolff et al. alcanza un rendimiento hasta **≈ 20× superior al de Folly**.
  * La sobrecarga del bucle CAS de Folly con 144 hilos activos satura el bus de interconexión entre sockets (QPI/UPI), ahogando el throughput.
* **Latencia de `load` con 56 hilos (Intel Xeon w7-3465X):**
  * Autor (*de Wolff et al.*): Mediana = **1.14 µs**.
  * Folly: Mediana = **11.6 µs**.  
  * *Resultado:* El Autor es **10 veces más rápido en latencia** que Folly a nivel de percentil 50, y la cola de Folly se dispara dramáticamente debido a los reintentos de CAS.

---

## 2. Versión Dummie (Explicación para Principiantes)

### 2.1. La Analogía del Mundo Real: "El Ascensor de Meta con Aforo Limitado"
Imagina el ascensor de las oficinas de Facebook:
* **Cómo trabaja Folly:** Los ingenieros de Meta querían un ascensor rápido y pequeño, así que le pusieron un cartel de aforo: *"Capacidad máxima: 8,192 personas"*. Cada vez que entra alguien, el ascensor revisa con un sensor si cabe. Si cabes, entras rápido.
* **El colapso de la fiesta:** Si un día hay una convención masiva y 8,193 personas quieren entrar al mismo tiempo, el sensor entra en pánico, suena una alarma estridente, el ascensor se apaga por seguridad y baja una reja de hierro con candado. Todo el mundo tiene que hacer una fila manual bloqueada.

### 2.2. Resumen "En Cristiano" (3 Balas Clave)
1. **¿Qué hace?** Es la versión oficial de Meta para servidores gigantes, basada en la libreta dividida pero con números pequeños de 32 bits.
2. **¿Por qué es malo?** Tiene un límite estricto de capacidad ($C=8192$). Si se llena, se apaga la velocidad y se vuelve bloqueante (usa candados de emergencia); además, leer requiere repetir intentos si hay congestión.
3. **¿Qué inventó el autor para vencerlo?** Aprovechó que las computadoras modernas tienen direcciones de 64 bits para empaquetar pesos gigantescos ($C=2^{19} = 524,288$ tickets) y hacer que leer sea arrancar un ticket de inmediato sin sensores quisquillosos ni bloqueos.

### 2.3. Preguntas Tontas que Todos nos Hacemos
* *¿Por qué Meta aceptó que se vuelva bloqueante con muchos hilos?*  
  Porque pensaron que en la vida real era muy raro tener más de 8,000 hilos leyendo la misma variable exacta al mismo microsegundo. Pero bajo ataques de denegación de servicio (DDoS) o picos de tráfico viral, ese límite sí se puede alcanzar.
* *¿Es mejor Folly que Libstdc++ (GCC)?*  
  Sí, Folly es mucho mejor que Libstdc++ porque en el 99% de las ocasiones no usa candados. Pero contra el algoritmo del paper de Euro-Par 2024, Folly pierde feo en velocidad y latencia.

### 2.4. Veredicto Dummie
> **Calificación:** 6.5 / 10.  
> **Veredicto:** Excelente ingeniería pragmática para la década pasada, pero limitada por sus compromisos de 32 bits y derrotada ampliamente por la nueva solución wait-free.

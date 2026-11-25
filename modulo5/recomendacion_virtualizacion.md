# Recomendación técnica de virtualización para DeliFIIS

> **BORRADOR PROVISIONAL — pendiente de validación completa**
>
> Semana 12 — Sistemas Operativos SW407, UNI  
> Responsable: Frank — Rol 4, integración y recomendación

Este documento responde de manera provisional a la pregunta 5 de la práctica. La recomendación se basa en el modelo educativo y en las verificaciones actualmente reproducibles del repositorio. No describe un despliegue real en Docker, VirtualBox ni otra plataforma de virtualización.

## Índice

1. [Decisión técnica](#1-decisión-técnica)
2. [Comparación de capacidad](#2-comparación-de-capacidad)
3. [Aislamiento y kernel compartido](#3-aislamiento-y-kernel-compartido)
4. [Cuotas de memoria y LRU](#4-cuotas-de-memoria-y-lru)
5. [Seguridad](#5-seguridad)
6. [Limitaciones y trabajo pendiente](#6-limitaciones-y-trabajo-pendiente)
7. [Estado de validación](#7-estado-de-validación)

## 1. Decisión técnica

Se recomienda una arquitectura combinada, seleccionando el mecanismo de virtualización según el nivel de aislamiento y la velocidad de escalamiento requerida.

### Contenedores para P1–P4

Los servicios asociados con los pedidos P1, P2, P3 y P4 se modelan como contenedores. La función `recomendar({"escalado_rapido": True})` de [`virt_hipervisores.py`](virt_hipervisores.py) devuelve `contenedor`, porque estos servicios representan cargas ligeras que podrían crearse o retirarse rápidamente según la demanda.

Esta elección ofrece las siguientes ventajas dentro del modelo:

- menor sobrecarga de memoria que una máquina virtual completa;
- mayor cantidad de instancias en el servidor disponible;
- arranque conceptualmente más ligero al compartir el kernel anfitrión;
- cuotas independientes para limitar el consumo de cada servicio.

Sus principales limitaciones son el kernel compartido y una frontera de aislamiento menor que la proporcionada por una máquina virtual. Además, el proyecto genera comandos Docker únicamente como texto: no se ha desplegado ni medido ningún contenedor real.

### Máquinas virtuales para aislamiento reforzado

Se recomiendan máquinas virtuales cuando la carga necesita una frontera más fuerte. Los escenarios propios definidos en [`virt_hipervisores.py`](virt_hipervisores.py) seleccionan VM para:

- el servidor de caja que maneja `caja.log`, considerado información sensible;
- el análisis de una ficha o programa sospechoso;
- componentes que requieran otro sistema operativo o kernel.

La VM incorpora un sistema operativo invitado y consume más memoria, pero reduce la dependencia del kernel anfitrión y proporciona una frontera adecuada para código no confiable. Esta es una recomendación derivada del modelo; no se ejecutó VirtualBox ni otro hipervisor.

## 2. Comparación de capacidad

Los resultados siguientes fueron recalculados con [`virt_capacidad.py`](virt_capacidad.py). Son resultados de un modelo aritmético verificado, no mediciones de consumo real.

| Perfil | Naturaleza | Memoria disponible | Memoria por juego VM | Juegos VM | Memoria por juego de contenedores | Juegos de contenedores |
|---|---|---:|---:|---:|---:|---:|
| PPT | CONTROL del docente | 14 336 MB | 2 560 MB | 5 | 562 MB | 25 |
| DeliFIIS | PROPIO del equipo | 20 480 MB | 8 704 MB | 2 | 2 720 MB | 7 |

En el perfil propio, el servidor parte de 24 576 MB y reserva 4 096 MB, por lo que quedan 20 480 MB disponibles. Con los supuestos del equipo caben dos juegos completos mediante VM y siete mediante contenedores. El cociente calculado es 3,5 veces más juegos con contenedores.

En el perfil de CONTROL de la PPT caben cinco juegos mediante VM y veinticinco mediante contenedores. Estos valores sirven para contrastar el modelo del docente con el escenario propio; no deben mezclarse como si pertenecieran a la misma configuración.

La mayor capacidad de contenedores no significa que sean siempre la opción más segura. La recomendación debe equilibrar eficiencia, compatibilidad y aislamiento.

## 3. Aislamiento y kernel compartido

### Namespaces

[`virt_aislamiento.py`](virt_aislamiento.py) modela aislamiento mediante namespaces de PID y UTS. Conceptualmente, un proceso conserva un PID visible desde el anfitrión y puede observar un PID diferente dentro de su namespace. El primer proceso del nuevo namespace de PID se presenta normalmente como PID 1 dentro de ese espacio.

El código contiene validaciones para comprobar identificadores, hostnames y PID no repetidos. En el entorno Windows actual se ejecutaron esas validaciones deterministas, pero la prueba real con `clone()` fue omitida porque no es Linux. Por tanto, **no se afirma que el equipo actual haya observado realmente PID 1 dentro de un namespace**.

### Kernel compartido

Los contenedores aíslan procesos y recursos, pero utilizan el kernel del anfitrión. Esto reduce la sobrecarga respecto de una VM, aunque un problema del kernel o una configuración débil puede afectar a varios contenedores. Una VM dispone de su propio kernel invitado y ofrece una separación más fuerte a cambio de mayor consumo.

### Jaula chroot

[`virt_jaula.py`](virt_jaula.py) comprueba la normalización de rutas y los metadatos esperados de las fichas de P1–P4. `chroot` cambia la raíz visible del sistema de archivos para el proceso confinado, pero no reemplaza namespaces, control de capacidades ni una VM.

En Windows se verificaron las reglas deterministas de rutas, tamaños, modos y huellas. La apertura real dentro de una jaula `chroot` fue omitida por falta de Linux y privilegios apropiados. No existe evidencia local que permita afirmar que el acceso real dentro de la jaula ya fue ejecutado.

## 4. Cuotas de memoria y LRU

La integración aplica un margen educativo del 25 % a la memoria de aplicación y relaciona el tamaño de cada pedido con una cantidad de marcos.

| Pedido | Cuota | Marcos | Fallos LRU |
|---|---:|---:|---:|
| P1 | 640 MB | 2 | 2 |
| P2 | 640 MB | 2 | 2 |
| P3 | 960 MB | 3 | 3 |
| P4 | 960 MB | 3 | 3 |
| **Total** | **3 200 MB** | **10** | **10** |

Los valores fueron reproducidos por [`virt_integracion.py`](virt_integracion.py). La memoria base de cada servicio proviene de `tamaño × 256 MB por estante`; el factor de 256 MB es un supuesto educativo del equipo definido en [`virt_comun.py`](virt_comun.py).

En el escenario normal, la secuencia de referencias produce un fallo inicial por cada página y no informa OOM:

- un **fallo de página** indica que la página solicitada no se encuentra cargada;
- un **reemplazo LRU** ocurre cuando los marcos están llenos y se retira la página usada menos recientemente;
- un **OOM** representa agotamiento de memoria sin una alternativa disponible y no se deduce simplemente de acceder a más páginas que marcos.

La integración diferencia estos conceptos. Su prueba negativa de OOM utiliza un gancho que lanza deliberadamente `MemoryError`; es una simulación controlada y no evidencia un proceso terminado realmente por el sistema operativo.

## 5. Seguridad

La política evaluada por [`sec_firewall.py`](sec_firewall.py) y reutilizada por la integración produjo:

| Tráfico | Decisión |
|---|---|
| TCP/443 | `ACCEPT` |
| TCP/3306 | `DROP` |

Permitir HTTPS mantiene disponible el servicio público previsto, mientras que bloquear el acceso directo al puerto de base de datos reduce la superficie expuesta. El firewall complementa el aislamiento: controla el tráfico de red, pero no sustituye cuotas, namespaces, permisos, chroot ni la separación ofrecida por una VM.

## 6. Limitaciones y trabajo pendiente

- No se ejecutaron Docker, VirtualBox ni otros hipervisores.
- No se midieron tiempos reales de arranque, uso de CPU ni consumo físico de memoria.
- El valor de 256 MB por estante es un supuesto educativo del equipo.
- Los tamaños, cuotas, fallos y capacidades pertenecen a una simulación.
- Faltan `virt_limites.py`, `virt_cuotas_memoria.py` y `virt_comandos.py`, asignados a Alejandro.
- Falta validar namespaces y el kernel compartido mediante una ejecución real en Linux.
- Falta validar la apertura real de las fichas dentro de `chroot` en Linux con los privilegios requeridos.
- Falta compilar `aislar.c` con GCC en Linux. En Windows la comprobación fue marcada correctamente como `OMITIDO` por incompatibilidad del entorno.
- Los comandos Docker generados por la integración son texto descriptivo y no evidencia de despliegue.

## 7. Estado de validación

### Evidencia reproducida en el entorno actual

| Elemento | Resultado | Alcance de la evidencia |
|---|---|---|
| Integración de virtualización | 19/19 verificaciones | Pruebas deterministas y ganchos simulados |
| Comparador de virtualización | 12/12 verificaciones internas | Clasificación de módulos y estados controlados |
| Módulos actualmente disponibles | 93/93 verificaciones; 6/9 módulos correctos | Ejecución Python local |
| Capacidad propia | 2 juegos VM y 7 de contenedores; 20 480 MB disponibles | Cálculo del modelo educativo |
| Capacidad CONTROL PPT | 5 juegos VM y 25 de contenedores | Cálculo de referencia del docente |
| Firewall | TCP/443 `ACCEPT`; TCP/3306 `DROP` | Evaluación de reglas simuladas |
| Namespaces y chroot reales | `OMITIDO` | El entorno actual es Windows |
| Compilación de `aislar.c` | `OMITIDO` | Requiere compilador y cabeceras Linux |

### Pendiente para convertirlo en versión definitiva

1. Incorporar y verificar los tres módulos aún ausentes.
2. Repetir el comparador hasta obtener los nueve módulos disponibles y correctos.
3. Ejecutar en Linux las pruebas reales de namespaces y chroot, conservando sus salidas como evidencia.
4. Compilar `aislar.c` en Linux con `gcc -Wall -Wextra -O2` sin ejecutar el binario durante la comprobación del comparador.
5. Revisar esta recomendación contra los resultados finales y retirar la etiqueta de borrador solo si no quedan comprobaciones pendientes.

Hasta completar esos pasos, la recomendación híbrida es técnicamente consistente con el modelo y las pruebas disponibles, pero continúa siendo **provisional**.

# SO-Sim · Simulador educativo de un sistema operativo (caso DeliFIIS)

Proyecto integrador del curso **SW407 · Arquitectura de computador y Sistemas Operativos** (UNI, Escuela de Ingeniería de Sistemas, 2026-II). Docente: Mg. Ing. José Carlos García La Riva. Equipo **Grupo M**: Franco García, Leonel Cruzado, Frank Chuctaya y Alejandro Meza.

El caso es **DeliFIIS**, un restaurante donde cada pedido se modela como un proceso del sistema operativo. Es una **simulación educativa**: las unidades de tiempo y los tamaños son abstractos y no representan una cocina ni un servidor reales.

## Módulos

| Carpeta | Tema | Lenguaje | Estado |
|---|---|---|---|
| `modulo1/` | Procesos y planificación (FCFS, SJF, Round Robin, Prioridad) | C y Python | Terminado |
| `modulo2/` | Sincronización (productor-consumidor, filósofos comensales) | Python | Terminado |
| `modulo3/` | Memoria (contigua, paginación, segmentación, reemplazo FIFO, LRU y Óptimo) | Python | Terminado |
| `modulo4/` | Entrada/Salida (`es_*`) y sistemas de archivos (`fs_*`) | Python | Terminado |
| `modulo5/` | Seguridad (`sec_*`, `acceso_real.c`) y virtualización (`virt_*`) | Python y C | Seguridad terminada; virtualización en desarrollo |
| Módulo 6 | Sistemas distribuidos | - | Pendiente |

Los módulos se reutilizan entre sí: los pedidos P1-P4 del Módulo 1 alimentan a los módulos 3, 4 y 5, y la seguridad del Módulo 5 abre las fichas del sistema de archivos del Módulo 4.

## Requisitos

- Python 3.10 o superior (solo biblioteca estándar).
- Linux, WSL o una máquina virtual con `gcc` para los programas en C (`fork()` y llamadas POSIX no existen en Windows nativo).
- `gpg` para las pruebas de cifrado del Módulo 5 (opcional: si falta, esa parte se omite).

## Cómo ejecutar (desde la raíz del repositorio)

Módulo 1: pedidos reales en C y planificador en Python.

    gcc -Wall -Wextra -O2 modulo1/codigo_c/preparar_pedido.c -o modulo1/codigo_c/preparar_pedido
    gcc -Wall -Wextra -O2 modulo1/codigo_c/mostrador.c -o modulo1/codigo_c/mostrador
    (cd modulo1/codigo_c && ./mostrador)
    python3 modulo1/codigo_py/simulador_planificacion.py --archivo modulo1/pedidos.json
    python3 modulo1/codigo_py/simulador_planificacion.py --verificar

Módulo 2: las dos soluciones sincronizadas.

    python3 modulo2/productor_consumidor.py
    python3 modulo2/modulo_filosofos_comensales.py

Los programas `sin_sincronizacion.py`, `sin_sincronizacion_con_fin.py` y `filosofos_deadlock.py` son demostraciones de contraste y pueden quedarse trabados a propósito (se detienen con Ctrl+C).

Verificación de los módulos 3, 4 y 5:

    python3 modulo3/comparacion_reemplazo.py
    python3 modulo4/comparacion_modulo4.py
    gcc -Wall -Wextra -O2 modulo5/acceso_real.c -o modulo5/acceso_real
    python3 modulo5/comparacion_modulo5.py

El `gcc` de `acceso_real.c` es opcional: sin él se omiten las pruebas con el kernel real.

## Convenciones del equipo

- Siempre se usa el nombre **DeliFIIS**.
- Prefijo de archivos por tema: `es_` (E/S), `fs_` (sistemas de archivos), `sec_` (seguridad) y `virt_` (virtualización).
- Cada archivo tiene `verificar()` y `main()`, e imprime `[OK]` o `[FALLO]`.
- Se distinguen los **valores de control** (de las presentaciones y prácticas del docente) de los **valores propios** del equipo.
- La salida por consola va sin tildes para evitar símbolos rotos en Windows.
- Lo que depende de herramientas externas (`gcc`, `gpg`, `sudo`) se prueba solo si están disponibles.

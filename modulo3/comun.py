"""Modulo comun para la gestion de memoria de CocinaPeru Express (Modulo 3).

Responsable: Persona 4 (Leonel)
Provee constantes globales, calculo de intervalos de ocupacion (basado en FCFS)
y ordenamiento de la linea de tiempo de eventos para los modulos de
memoria contigua, paginacion y segmentacion.
"""

from __future__ import annotations

import os
import sys

# Ajuste al path de modulo1 para importar el simulador de planificacion
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "modulo1", "codigo_py")
    ),
)

from simulador_planificacion import CONJUNTO_EQUIPO, CONJUNTO_OFICIAL, Proceso, fcfs

# Constantes del sistema acordadas para el Modulo 3
MEMORIA_TOTAL = 10  # 10 estantes / marcos de memoria
TAM_PAGINA = 4096   # 4 096 bytes por pagina/marco/estante


def intervalos(procesos: tuple[Proceso, ...] | list[Proceso]) -> list[tuple[str, int, int, int]]:
    """Calcula [(id, llegada, fin, tamano)] usando el tiempo de fin determinado por FCFS."""
    _, metricas = fcfs(procesos)
    return sorted(
        [
            (p.id, p.llegada, metricas[p.id].fin, p.tamano)
            for p in procesos
        ],
        key=lambda x: (x[1], x[0]),
    )


def eventos(intervs: list[tuple[str, int, int, int]]) -> list[tuple[int, int, str, int]]:
    """Genera la lista cronologica de eventos.

    Si en el mismo instante coinciden una salida y una llegada,
    la salida (tipo 0) se procesa antes que la llegada (tipo 1).
    Retorna lista de tuplas: (instante, tipo, id_pedido, tamano).
    """
    ev = []
    for (i, a, f, s) in intervs:
        ev.append((a, 1, i, s))  # llegada: tipo = 1
        ev.append((f, 0, i, s))  # salida:  tipo = 0
    return sorted(ev)


if __name__ == "__main__":
    print("=== MODULO 3 - COMUN.PY (VERIFICACION) ===")
    print(f"MEMORIA_TOTAL : {MEMORIA_TOTAL} estantes")
    print(f"TAM_PAGINA    : {TAM_PAGINA} bytes\n")

    print("--- Intervalos Q1-Q5 (tomando fin de FCFS) ---")
    intervs_q = intervalos(CONJUNTO_EQUIPO)
    for p_id, lleg, fin, tam in intervs_q:
        print(f"Pedido {p_id}: llega={lleg}, fin={fin}, tamano={tam} estantes")

    print("\n--- Eventos ordenados Q1-Q5 (salidas antes que llegadas en empate) ---")
    evs_q = eventos(intervs_q)
    for inst, tipo, p_id, tam in evs_q:
        tipo_str = "LLEGADA" if tipo == 1 else "SALIDA "
        print(f"Instante {inst:2d} | Evento: {tipo_str} de {p_id} (tam={tam})")

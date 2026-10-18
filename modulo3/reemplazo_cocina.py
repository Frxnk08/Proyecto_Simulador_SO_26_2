"""Modulo 3 - Cadena de referencias de CocinaPeru Express."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "modulo1", "codigo_py")))

from simulador_planificacion import CONJUNTO_EQUIPO, CONJUNTO_OFICIAL, round_robin


def cadena_cocina(conjunto="equipo", quantum=4):
    """Construye referencias PID:pagina desde cada unidad del Gantt Round Robin."""
    if conjunto == "equipo":
        procesos = CONJUNTO_EQUIPO
    elif conjunto == "oficial":
        procesos = CONJUNTO_OFICIAL
    else:
        raise ValueError("El conjunto debe ser 'equipo' u 'oficial'")

    tamano = {proceso.id: proceso.tamano for proceso in procesos}
    unidades = {proceso.id: 0 for proceso in procesos}
    gantt, _ = round_robin(procesos, quantum)
    referencias = []
    for pedido, inicio, fin in gantt:
        if pedido == "IDLE":
            continue
        for _ in range(inicio, fin):
            n = unidades[pedido]
            pagina = 0 if n % 2 == 0 or tamano[pedido] == 1 else 1 + ((n // 2) % (tamano[pedido] - 1))
            referencias.append(f"{pedido}:{pagina}")
            unidades[pedido] += 1
    return referencias


def main():
    esperados = {
        "oficial": (22, 10, ["P1:0", "P1:1", "P1:0", "P1:1", "P2:0", "P2:1", "P2:0", "P3:0"]),
        "equipo": (21, 11, ["Q1:0", "Q1:1", "Q1:0", "Q1:1", "Q2:0", "Q2:1", "Q2:0", "Q2:1"]),
    }
    correctas = []
    for conjunto, (total, distintas, primeras) in esperados.items():
        refs = cadena_cocina(conjunto)
        print(f"{conjunto}: {len(refs)} referencias, {len(set(refs))} paginas distintas")
        print("Primeras 8: " + ", ".join(refs[:8]))
        for nombre, cumple in (("total", len(refs) == total),
                               ("paginas distintas", len(set(refs)) == distintas),
                               ("primeras 8", refs[:8] == primeras)):
            print(f"[{'OK' if cumple else 'FALLO'}] {conjunto}: {nombre}")
            correctas.append(cumple)
    return 0 if all(correctas) else 1


if __name__ == "__main__":
    raise SystemExit(main())

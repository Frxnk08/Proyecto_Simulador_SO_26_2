from __future__ import annotations

from virt_comun import (
    MB_POR_ESTANTE,
    imprimir_verificaciones,
    servicios_delifiis,
)
from virt_limites import cuotas_delifiis

from reemplazo_cocina import cadena_cocina
import reemplazo_fifo
import reemplazo_lru
import reemplazo_optimo

ALGORITMOS_M3 = {
    "FIFO": reemplazo_fifo.simular,
    "LRU": reemplazo_lru.simular,
    "Optimo": reemplazo_optimo.simular,
}


def cuota_marcos(cuota_mb: int) -> int:
    """Convierte una cuota en MB a numero de marcos (256 MB por estante/marco)."""
    if cuota_mb <= 0:
        raise ValueError("La cuota en MB debe ser mayor que cero")
    return cuota_mb // MB_POR_ESTANTE


def simular_cuota(
    pedido: str,
    marcos: int,
    politica: str = "LRU",
    conjunto: str = "oficial",
) -> dict:
    """Simula los fallos de pagina de un pedido acotado a un numero de marcos."""
    if politica not in ALGORITMOS_M3:
        raise ValueError(f"Politica desconocida: {politica}. Validas: {list(ALGORITMOS_M3)}")
    if marcos <= 0:
        raise ValueError("La cantidad de marcos debe ser mayor que cero")

    refs_totales = cadena_cocina(conjunto)
    refs_pedido = [r for r in refs_totales if r.startswith(f"{pedido}:")]
    if not refs_pedido:
        raise ValueError(f"Pedido desconocido o sin referencias: {pedido}")

    fallos, _ = ALGORITMOS_M3[politica](refs_pedido, marcos)
    paginas_distintas = len(set(refs_pedido))

    return {
        "pedido": pedido,
        "marcos": marcos,
        "politica": politica,
        "accesos": len(refs_pedido),
        "paginas_distintas": paginas_distintas,
        "fallos": fallos,
        "oom_sin_swap": marcos < paginas_distintas,
    }


def tabla_cuotas(marcos: tuple[int, ...] = (1, 2, 3, 4)) -> dict[str, dict[int, dict[str, int]]]:
    """Genera {pedido: {marcos: {politica: fallos}}} para P1-P4."""
    pedidos = list(servicios_delifiis().keys())
    tabla: dict[str, dict[int, dict[str, int]]] = {}
    for pid in pedidos:
        tabla[pid] = {}
        for m in marcos:
            tabla[pid][m] = {}
            for pol in ALGORITMOS_M3:
                res = simular_cuota(pid, m, politica=pol, conjunto="oficial")
                tabla[pid][m][pol] = res["fallos"]
    return tabla


def verificar() -> list[tuple[str, bool]]:
    """Verifica cuotas en marcos, tabla esperada e invariantes contra M3."""
    pruebas: list[tuple[str, bool]] = []

    pruebas.append((
        "propio: cuota_marcos(640) == 2 y cuota_marcos(960) == 3",
        cuota_marcos(640) == 2 and cuota_marcos(960) == 3,
    ))

    esperado = {
        "P1": {1: (5, 5, 5), 2: (2, 2, 2), 3: (2, 2, 2), 4: (2, 2, 2)},
        "P2": {1: (3, 3, 3), 2: (2, 2, 2), 3: (2, 2, 2), 4: (2, 2, 2)},
        "P3": {1: (8, 8, 8), 2: (6, 5, 5), 3: (3, 3, 3), 4: (3, 3, 3)},
        "P4": {1: (6, 6, 6), 2: (5, 4, 4), 3: (3, 3, 3), 4: (3, 3, 3)},
    }
    tabla = tabla_cuotas((1, 2, 3, 4))
    tabla_ok = True
    orden_ok = True

    for pid, por_marco in esperado.items():
        for m, (f_esp, l_esp, o_esp) in por_marco.items():
            celda = tabla[pid][m]
            if (celda["FIFO"], celda["LRU"], celda["Optimo"]) != (f_esp, l_esp, o_esp):
                tabla_ok = False
            if not (celda["Optimo"] <= celda["LRU"] <= celda["FIFO"]):
                orden_ok = False

    pruebas.append((
        "propio (M3): tabla de fallos P1-P4 en 1..4 marcos coincide",
        tabla_ok,
    ))
    pruebas.append((
        "invariante: Optimo <= LRU <= FIFO en todas las celdas",
        orden_ok,
    ))

    total_accesos = 0
    total_distintas = 0
    sin_oom_ok = True
    for pid in ("P1", "P2", "P3", "P4"):
        info_base = simular_cuota(pid, 4, "LRU")
        total_accesos += info_base["accesos"]
        total_distintas += info_base["paginas_distintas"]
        if info_base["fallos"] != info_base["paginas_distintas"] or info_base["oom_sin_swap"]:
            sin_oom_ok = False

    pruebas.append((
        "invariante M3: suma de accesos == 22 y paginas distintas == 10",
        total_accesos == 22 and total_distintas == 10,
    ))
    pruebas.append((
        "invariante: con marcos >= paginas_distintas, fallos == paginas_distintas y sin OOM",
        sin_oom_ok,
    ))

    cuotas = cuotas_delifiis()
    fallos_asignados = []
    ningun_oom = True
    for pid in ("P1", "P2", "P3", "P4"):
        m = cuota_marcos(cuotas[pid])
        res = simular_cuota(pid, m, "LRU")
        fallos_asignados.append(res["fallos"])
        if res["oom_sin_swap"]:
            ningun_oom = False

    pruebas.append((
        "propio: cuotas DeliFIIS (2,2,3,3 marcos) -> fallos [2, 2, 3, 3] (total 10) sin OOM",
        fallos_asignados == [2, 2, 3, 3] and sum(fallos_asignados) == 10 and ningun_oom,
    ))

    err_pol = False
    try:
        simular_cuota("P1", 2, politica="CLOCK")
    except ValueError:
        err_pol = True

    err_ped = False
    try:
        simular_cuota("P99", 2, politica="LRU")
    except ValueError:
        err_ped = True

    pruebas.append((
        "validacion: ValueError ante politica o pedido desconocido",
        err_pol and err_ped,
    ))

    return pruebas


def main() -> int:
    print("=== MODULO 5 (SEMANA 12) - CUOTAS DE MEMORIA Y FALLOS DE PAGINA ===")
    print("[nota] Analogia didactica: un cgroup real no pagina el proceso, lo mata con codigo 137 si no hay swap.")
    tabla = tabla_cuotas((1, 2, 3, 4))
    for pid, filas in tabla.items():
        resumen = " | ".join(
            f"{m}m: {vals['FIFO']}/{vals['LRU']}/{vals['Optimo']}"
            for m, vals in filas.items()
        )
        print(f"  {pid}: {resumen}")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from es_comun import costo_cpu_us, evaluar, obtener_perfil

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "modulo1", "codigo_py")
    ),
)
try:
    from simulador_planificacion import (
        CONJUNTO_EQUIPO,
        CONJUNTO_OFICIAL,
        fcfs,
    )
except ImportError:
    CONJUNTO_OFICIAL = [("P1", 0, 5, 2), ("P2", 1, 8, 2), ("P3", 2, 16, 3), ("P4", 3, 22, 3)]
    CONJUNTO_EQUIPO = [("Q1", 0, 4, 2), ("Q2", 1, 11, 2), ("Q3", 2, 13, 2), ("Q4", 4, 18, 3), ("Q5", 6, 21, 3)]

    def fcfs(procesos):
        class Metrica:
            def __init__(self, fin):
                self.fin = fin
        m = {}
        for p in procesos:
            pid = p[0] if isinstance(p, tuple) else p.id
            fin = p[2] if isinstance(p, tuple) else getattr(p, "fin", 0)
            m[pid] = Metrica(fin)
        return None, m

FALLOS_M3 = {
    "FIFO": 15,
    "LRU": 12,
    "Optimo": 9,
}


def solicitudes_por_pedido(proceso, fin_instante: int, perfil_nombre: str = "delifiis"):
    
    perfil = obtener_perfil(perfil_nombre)
    llegada = proceso.llegada if hasattr(proceso, "llegada") else proceso[1]
    pid = proceso.id if hasattr(proceso, "id") else proceso[0]

    solicitudes = []
    if perfil_nombre == "ppt_control":
        disp = perfil["dispositivos"]["disco"]
        solicitudes.append((llegada, pid, "disco", disp["bytes"], disp["us_por_byte"]))
    else:
        t_disp = perfil["dispositivos"]["teclado"]
        d_disp = perfil["dispositivos"]["disco"]
        r_disp = perfil["dispositivos"]["red"]

        solicitudes.append((llegada, pid, "teclado", t_disp["bytes"], t_disp["us_por_byte"]))
        solicitudes.append((llegada, pid, "disco", d_disp["bytes"], d_disp["us_por_byte"]))
        solicitudes.append((fin_instante, pid, "red", r_disp["bytes"], r_disp["us_por_byte"]))

    return solicitudes


def cpu_por_politica(conjunto_procesos, perfil_nombre: str, politica: str):
    
    perfil = obtener_perfil(perfil_nombre)
    _, metricas = fcfs(conjunto_procesos)

    total_cpu_us = 0.0
    saturado_global = False

    for p in conjunto_procesos:
        pid = p.id if hasattr(p, "id") else p[0]
        fin = metricas[pid].fin if pid in metricas else (p[2] if isinstance(p, tuple) else 0)
        solicitudes = solicitudes_por_pedido(p, fin, perfil_nombre)

        for _, _, disp_nombre, n_bytes, us_por_byte in solicitudes:
            if politica == "todo_votacion":
                metodo = "votacion"
            elif politica == "todo_interrupciones":
                metodo = "interrupciones"
            elif politica == "todo_dma":
                metodo = "dma"
            elif politica == "recomendada":
                if disp_nombre == "teclado":
                    metodo = "interrupciones"
                else:
                    metodo = "dma"
            else:
                raise ValueError(f"Politica desconocida: {politica}")

            res = evaluar(metodo, n_bytes, us_por_byte, perfil)
            total_cpu_us += res["costo_us"]
            if res["saturado"]:
                saturado_global = True

    return total_cpu_us, saturado_global


def cpu_por_fallos(perfil_nombre: str, fallos: int):
    
    perfil = obtener_perfil(perfil_nombre)
    d_disp = perfil["dispositivos"]["disco"]
    bytes_bloque = d_disp["bytes"]
    us_por_byte = d_disp["us_por_byte"]

    res_vot = evaluar("votacion", bytes_bloque, us_por_byte, perfil)
    res_int = evaluar("interrupciones", bytes_bloque, us_por_byte, perfil)
    res_dma = evaluar("dma", bytes_bloque, us_por_byte, perfil)

    return {
        "votacion": (fallos * res_vot["costo_us"], res_vot["saturado"]),
        "interrupciones": (fallos * res_int["costo_us"], res_int["saturado"]),
        "dma": (fallos * res_dma["costo_us"], res_dma["saturado"]),
    }


def verificar() -> list[tuple[str, bool]]:
    pruebas = []

    v_p, s_v = cpu_por_politica(CONJUNTO_OFICIAL, "delifiis", "todo_votacion")
    i_p, s_i = cpu_por_politica(CONJUNTO_OFICIAL, "delifiis", "todo_interrupciones")
    d_p, s_d = cpu_por_politica(CONJUNTO_OFICIAL, "delifiis", "todo_dma")
    r_p, s_r = cpu_por_politica(CONJUNTO_OFICIAL, "delifiis", "recomendada")

    pruebas.append(("delifiis P1-P4 votacion (471 536 us)", abs(v_p - 471536.0) < 1e-4 and not s_v))
    pruebas.append(("delifiis P1-P4 interrupciones (188 059.2 us, SATURADO)", abs(i_p - 188059.2) < 1e-4 and s_i))
    pruebas.append(("delifiis P1-P4 dma (456.0 us)", abs(d_p - 456.0) < 1e-4 and not s_d))
    pruebas.append(("delifiis P1-P4 recomendada (337.6 us)", abs(r_p - 337.6) < 1e-4 and not s_r))

    v_q, _ = cpu_por_politica(CONJUNTO_EQUIPO, "delifiis", "todo_votacion")
    i_q, s_iq = cpu_por_politica(CONJUNTO_EQUIPO, "delifiis", "todo_interrupciones")
    d_q, _ = cpu_por_politica(CONJUNTO_EQUIPO, "delifiis", "todo_dma")
    r_q, _ = cpu_por_politica(CONJUNTO_EQUIPO, "delifiis", "recomendada")

    pruebas.append(("delifiis Q1-Q5 votacion (589 420 us)", abs(v_q - 589420.0) < 1e-4))
    pruebas.append(("delifiis Q1-Q5 interrupciones (235 074 us, SATURADO)", abs(i_q - 235074.0) < 1e-4 and s_iq))
    pruebas.append(("delifiis Q1-Q5 dma (570.0 us)", abs(d_q - 570.0) < 1e-4))
    pruebas.append(("delifiis Q1-Q5 recomendada (422.0 us)", abs(r_q - 422.0) < 1e-4))

    v_ppt, _ = cpu_por_politica(CONJUNTO_OFICIAL, "ppt_control", "todo_votacion")
    i_ppt, _ = cpu_por_politica(CONJUNTO_OFICIAL, "ppt_control", "todo_interrupciones")
    d_ppt, _ = cpu_por_politica(CONJUNTO_OFICIAL, "ppt_control", "todo_dma")

    pruebas.append(("ppt_control P1-P4 votacion (163 840 us)", abs(v_ppt - 163840.0) < 1e-4))
    pruebas.append(("ppt_control P1-P4 interrupciones (90 112 us)", abs(i_ppt - 90112.0) < 1e-4))
    pruebas.append(("ppt_control P1-P4 dma (100 us)", abs(d_ppt - 100.0) < 1e-4))

    f_fifo = cpu_por_fallos("ppt_control", FALLOS_M3["FIFO"])
    pruebas.append(("Fallos FIFO ppt_control votacion (614 400 us)", abs(f_fifo["votacion"][0] - 614400.0) < 1e-4))
    pruebas.append(("Fallos FIFO ppt_control interrupciones (337 920 us)", abs(f_fifo["interrupciones"][0] - 337920.0) < 1e-4))
    pruebas.append(("Fallos FIFO ppt_control dma (375 us)", abs(f_fifo["dma"][0] - 375.0) < 1e-4))

    return pruebas


def main() -> int:
    print("=== MODULO 4 - INTEGRACION CON M1 Y M3 ===")
    pruebas = verificar()
    correctas = 0
    for desc, cumple in pruebas:
        estado = "OK" if cumple else "FALLO"
        if cumple:
            correctas += 1
        print(f"[{estado}] {desc}")

    print(f"\nVerificaciones correctas: {correctas}/{len(pruebas)}")
    return 0 if correctas == len(pruebas) else 1


if __name__ == "__main__":
    raise SystemExit(main())
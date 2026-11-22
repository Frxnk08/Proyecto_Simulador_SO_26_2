"""Modulo 5 (semana 12) - virt_comun.py
Caso: DeliFIIS. Rutas a M1/M3/M4/M5, valores de CONTROL y utilidades compartidas
por los archivos virt_*.py. Sin logica de algoritmos. Salida sin tildes (Windows).
"""

from __future__ import annotations

import os
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
for _carpeta in ("modulo5", "modulo4", "modulo3", os.path.join("modulo1", "codigo_py")):
    _ruta = os.path.abspath(os.path.join(_AQUI, "..", _carpeta))
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

# Reutiliza lo de semanas anteriores (no se redefine)
from sec_comun import herramienta_disponible, es_linux, imprimir_verificaciones  # noqa: E402,F401
from simulador_planificacion import CONJUNTO_OFICIAL  # noqa: E402

TAM_PAGINA = 4096          # bytes por marco/estante (acuerdo de M3)
MB_POR_ESTANTE = 256       # VALOR PROPIO (supuesto del equipo): 1 estante de M1 = 256 MB

# ---- Valores de CONTROL (PPT semana 12 y practica dirigida; NO cambiar) ----
CONTROL = {
    "ppt": {"total_mb": 16 * 1024, "reserva_mb": 2 * 1024, "apps": {"app": 512},
            "so_invitado_mb": 2048, "sobrecarga_mb": 50},
    "practica": {"total_mb": 32 * 1024, "reserva_mb": 4 * 1024,
                 "apps": {"Polleria": 1024, "Chifa": 768, "Pedidos web": 512},
                 "so_invitado_mb": 2048, "sobrecarga_mb": 60},
    "ulimit_kb": {102400: "MemoryError", 307200: "OK"},   # reserva de 200 MB
}


def es_root() -> bool:
    """True si el proceso es root (en Windows siempre False)."""
    return hasattr(os, "geteuid") and os.geteuid() == 0


def servicios_delifiis(mb_por_estante: int = MB_POR_ESTANTE) -> dict[str, dict]:
    """Un servicio por pedido de M1: {id: {descripcion, tamano, mb}} con mb = tamano * mb_por_estante."""
    return {p.id: {"descripcion": p.descripcion, "tamano": p.tamano, "mb": p.tamano * mb_por_estante}
            for p in CONJUNTO_OFICIAL}


def verificar():
    s = servicios_delifiis()
    return [
        ("4 servicios, uno por pedido P1-P4 de M1", list(s) == ["P1", "P2", "P3", "P4"]),
        ("memoria propia: P1=512, P2=512, P3=768, P4=768 MB",
         [s[k]["mb"] for k in s] == [512, 512, 768, 768]),
        ("control practica: 28 672 MB disponibles",
         CONTROL["practica"]["total_mb"] - CONTROL["practica"]["reserva_mb"] == 28672),
        ("control ppt: 14 336 MB disponibles",
         CONTROL["ppt"]["total_mb"] - CONTROL["ppt"]["reserva_mb"] == 14336),
        ("es_root() devuelve bool", isinstance(es_root(), bool)),
    ]


def main():
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())
"""Modulo 4 (semana 10) - fs_comun.py
Caso: DeliFIIS. Constantes, datos de control (practica dirigida semana 10) y
estructura Inodo compartidos por los archivos fs_*.py. Sin logica de algoritmos.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

# Rutas a M1 (planificador) y M3 (paginacion, reemplazo) para poder reutilizarlos
_AQUI = os.path.dirname(os.path.abspath(__file__))
for _ruta in (
    os.path.join(_AQUI, "..", "modulo1", "codigo_py"),
    os.path.join(_AQUI, "..", "modulo3"),
):
    _ruta = os.path.abspath(_ruta)
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

# ---- Constantes del modelo (valores asumidos con fines didacticos) ----
TAM_BLOQUE = 4096          # bytes por bloque (igual que TAM_PAGINA de M3 y es_disco)
TAM_PUNTERO = 4            # bytes por puntero
NUM_BLOQUES_CONTROL = 16   # disco de la practica dirigida

# ---- Datos de la practica dirigida (valores de CONTROL) ----
DISCO_CONTROL = ["A", "A", "A", "B", "B", None, None, None,
                 "C", "C", "C", None, None, None, None, None]
FAT_CONTROL = {4: 7, 7: 2, 2: "FIN", 9: "FIN"}
USUARIOS = {"chef": ["cocineros"], "ayudante": ["cocineros"], "visitante": []}

CONTROL = {
    # lecturas para leer el bloque k (k = 1, 3, 5) de un archivo de 5 bloques
    "lecturas": {"contigua": [1, 1, 1], "enlazada": [1, 3, 5], "indexada": [2, 2, 2]},
    "libres_y_mayor_hueco": (8, 5),                    # archivo D de 6 bloques NO cabe
    "interna": {10240: (3, 12288, 2048), 4097: (2, 8192, 4095)},  # (bloques, reservado, desperdicio)
    "punteros_por_indice": 1024,
    "max_archivo_un_indice": 4 * 1024 * 1024,          # 4 MB
    "fat_8gb": (2097152, 8 * 1024 * 1024),             # (entradas, bytes de la tabla) = 8 MB
    "cadena_fat_4": [4, 7, 2],
    # (permisos octal, {usuario: (lee, escribe)})
    "matriz_permisos": {
        "ceviche.txt": (0o640, {"chef": (True, True), "ayudante": (True, False), "visitante": (False, False)}),
        "stock.csv": (0o660, {"chef": (True, True), "ayudante": (True, True), "visitante": (False, False)}),
    },
    "umask": {"022": (0o644, 0o755), "077": (0o600, 0o700)},  # (archivo, directorio)
}


@dataclass
class Inodo:
    """Metadatos de un archivo. El NOMBRE no va aqui: vive en el directorio."""

    numero: int
    tipo: str = "archivo"          # archivo | directorio | simbolico
    tamano: int = 0                # bytes
    propietario: str = "chef"
    grupo: str = "cocineros"
    permisos: int = 0o640
    enlaces: int = 1               # cantidad de nombres que apuntan a este inodo
    bloques: list = field(default_factory=list)
    destino: str | None = None     # solo para enlaces simbolicos (la ruta)


def bloques_necesarios(tamano_bytes: int) -> int:
    """Bloques enteros que ocupa un archivo (techo de tamano / TAM_BLOQUE)."""
    if tamano_bytes < 0:
        raise ValueError("El tamano no puede ser negativo")
    return (tamano_bytes + TAM_BLOQUE - 1) // TAM_BLOQUE


def fichas_delifiis():
    """Perfil delifiis: una ficha de receta por pedido de M1 (tamano = bloques)."""
    from simulador_planificacion import CONJUNTO_OFICIAL
    return [(p.id, p.descripcion, p.tamano) for p in CONJUNTO_OFICIAL]


def imprimir_verificaciones(verificaciones) -> int:
    """Imprime [OK]/[FALLO] por cada (descripcion, cumple) y devuelve 0 si todo ok."""
    for descripcion, cumple in verificaciones:
        print(f"[{'OK' if cumple else 'FALLO'}] {descripcion}")
    ok = sum(1 for _, c in verificaciones if c)
    print(f"Verificaciones correctas: {ok}/{len(verificaciones)}")
    return 0 if ok == len(verificaciones) else 1
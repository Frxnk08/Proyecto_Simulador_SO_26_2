"""Modulo 5 (semana 12) - virt_aislamiento.py
Caso: DeliFIIS. Rol 2: aislamiento por namespaces y proceso clone en C.
Salida sin tildes (Windows).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)

from virt_comun import es_linux, es_root, herramienta_disponible, imprimir_verificaciones, servicios_delifiis

_RUTA_C = os.path.join(_AQUI, "aislar.c")
_RUTA_BIN_AISLAR = os.path.join(_AQUI, "aislar")
_RUTA_PREPARAR_SRC = os.path.abspath(os.path.join(_AQUI, "..", "modulo1", "codigo_c", "preparar_pedido.c"))
_RUTA_PREPARAR_BIN = os.path.abspath(os.path.join(_AQUI, "..", "modulo1", "codigo_c", "preparar_pedido"))


def compilar_aislar() -> str | None:
    """Si hay gcc, compila preparar_pedido y aislar. Devuelve ruta o None."""
    if not herramienta_disponible("gcc"):
        return None

    if not os.path.exists(_RUTA_PREPARAR_BIN):
        if os.path.exists(_RUTA_PREPARAR_SRC):
            cmd = ["gcc", "-Wall", "-Wextra", "-O2", _RUTA_PREPARAR_SRC, "-o", _RUTA_PREPARAR_BIN]
            res = subprocess.run(cmd, capture_output=True)
            if res.returncode != 0:
                return None
        else:
            return None

    necesita_compilar = not os.path.exists(_RUTA_BIN_AISLAR)
    if not necesita_compilar and os.path.exists(_RUTA_C):
        necesita_compilar = os.path.getmtime(_RUTA_C) > os.path.getmtime(_RUTA_BIN_AISLAR)

    if necesita_compilar:
        cmd = ["gcc", "-Wall", "-Wextra", "-O2", _RUTA_C, "-o", _RUTA_BIN_AISLAR]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0:
            return None

    return _RUTA_BIN_AISLAR


def motivo_omision() -> str | None:
    """None si es Linux, hay gcc y es_root(); si no, motivo descriptivo."""
    if not es_linux():
        return "no es Linux"
    if not herramienta_disponible("gcc"):
        return "falta gcc"
    if not es_root():
        return "requiere root (usa sudo)"
    return None


def validar_registros(registros: list[dict], ids: list[str]) -> list[str]:
    """Valida los registros devueltos por aislar. Pura, funciona en Windows."""
    errores = []
    if not isinstance(registros, list):
        return ["los registros deben ser una lista"]
    if len(registros) != len(ids):
        errores.append(f"cantidad de registros ({len(registros)}) no coincide con ids ({len(ids)})")
        return errores

    pids_anfitrion = set()
    for idx, (reg, esperado_id) in enumerate(zip(registros, ids)):
        if not isinstance(reg, dict):
            errores.append(f"registro {idx} no es un diccionario")
            continue

        r_id = reg.get("id")
        if r_id != esperado_id:
            errores.append(f"registro {idx}: id '{r_id}' no coincide con esperado '{esperado_id}'")

        pid_anfitrion = reg.get("pid_anfitrion")
        if not isinstance(pid_anfitrion, int) or pid_anfitrion <= 1:
            errores.append(f"registro {r_id}: pid_anfitrion ({pid_anfitrion}) debe ser un entero mayor que 1")
        elif pid_anfitrion in pids_anfitrion:
            errores.append(f"registro {r_id}: pid_anfitrion {pid_anfitrion} repetido")
        else:
            pids_anfitrion.add(pid_anfitrion)

        pid_ns = reg.get("pid_namespace")
        if pid_ns != 1:
            errores.append(f"registro {r_id}: pid_namespace ({pid_ns}) debe ser 1")

        esperado_host = f"delifiis-{esperado_id}"
        r_host = reg.get("hostname")
        if r_host != esperado_host:
            errores.append(f"registro {r_id}: hostname '{r_host}' debe ser '{esperado_host}'")

    return errores


def ejecutar_aislamiento(ids: list[str] | None = None) -> list[dict] | None:
    """Ejecuta aislar con subprocess y devuelve lista o None si se omite."""
    if motivo_omision() is not None:
        return None
    if ids is None:
        ids = list(servicios_delifiis())

    bin_aislar = compilar_aislar()
    if not bin_aislar:
        return None

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        ruta_tmp_json = tmp.name

    try:
        cmd = [bin_aislar, ruta_tmp_json, _RUTA_PREPARAR_BIN, *ids]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if res.returncode == 77 or res.returncode != 0:
            return None
        if not os.path.exists(ruta_tmp_json) or os.path.getsize(ruta_tmp_json) == 0:
            return None
        with open(ruta_tmp_json, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
    finally:
        if os.path.exists(ruta_tmp_json):
            try:
                os.remove(ruta_tmp_json)
            except OSError:
                pass


def kernel_compartido() -> bool | None:
    """True si el kernel es compartido (uname anfitrion == uname unshare)."""
    if not es_linux() or not es_root():
        return None
    try:
        k_host = subprocess.run(["uname", "-r"], capture_output=True, text=True, check=True).stdout.strip()
        k_ns = subprocess.run(
            ["unshare", "--uts", "--pid", "--fork", "--mount-proc", "uname", "-r"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        return k_host == k_ns
    except Exception:
        return None


def verificar() -> list[tuple[str, bool]]:
    """Verifica reglas de validacion y pruebas reales si hay root."""
    ej_correctos = [
        {"id": "P1", "pid_anfitrion": 1001, "pid_namespace": 1, "hostname": "delifiis-P1"},
        {"id": "P2", "pid_anfitrion": 1002, "pid_namespace": 1, "hostname": "delifiis-P2"},
        {"id": "P3", "pid_anfitrion": 1003, "pid_namespace": 1, "hostname": "delifiis-P3"},
        {"id": "P4", "pid_anfitrion": 1004, "pid_namespace": 1, "hostname": "delifiis-P4"},
    ]
    ej_pid_ns_7 = [
        {"id": "P1", "pid_anfitrion": 1001, "pid_namespace": 7, "hostname": "delifiis-P1"},
        {"id": "P2", "pid_anfitrion": 1002, "pid_namespace": 1, "hostname": "delifiis-P2"},
        {"id": "P3", "pid_anfitrion": 1003, "pid_namespace": 1, "hostname": "delifiis-P3"},
        {"id": "P4", "pid_anfitrion": 1004, "pid_namespace": 1, "hostname": "delifiis-P4"},
    ]
    ej_host_mal = [
        {"id": "P1", "pid_anfitrion": 1001, "pid_namespace": 1, "hostname": "servidor-P1"},
        {"id": "P2", "pid_anfitrion": 1002, "pid_namespace": 1, "hostname": "delifiis-P2"},
        {"id": "P3", "pid_anfitrion": 1003, "pid_namespace": 1, "hostname": "delifiis-P3"},
        {"id": "P4", "pid_anfitrion": 1004, "pid_namespace": 1, "hostname": "delifiis-P4"},
    ]
    ej_pid_rep = [
        {"id": "P1", "pid_anfitrion": 1001, "pid_namespace": 1, "hostname": "delifiis-P1"},
        {"id": "P2", "pid_anfitrion": 1001, "pid_namespace": 1, "hostname": "delifiis-P2"},
        {"id": "P3", "pid_anfitrion": 1003, "pid_namespace": 1, "hostname": "delifiis-P3"},
        {"id": "P4", "pid_anfitrion": 1004, "pid_namespace": 1, "hostname": "delifiis-P4"},
    ]

    ids_delifiis = ["P1", "P2", "P3", "P4"]

    tests: list[tuple[str, bool]] = [
        ("validar_registros acepta registros correctos", len(validar_registros(ej_correctos, ids_delifiis)) == 0),
        ("validar_registros rechaza pid_namespace distinto de 1", len(validar_registros(ej_pid_ns_7, ids_delifiis)) > 0),
        ("validar_registros rechaza hostname que no coincide con delifiis-ID", len(validar_registros(ej_host_mal, ids_delifiis)) > 0),
        ("validar_registros rechaza pid_anfitrion repetido", len(validar_registros(ej_pid_rep, ids_delifiis)) > 0),
    ]

    motivo = motivo_omision()
    if motivo is None:
        regs = ejecutar_aislamiento()
        tests.extend([
            ("ejecutar_aislamiento() devuelve 4 registros", regs is not None and len(regs) == 4),
            ("validar_registros() sin errores en ejecucion real", regs is not None and len(validar_registros(regs, ids_delifiis)) == 0),
            ("kernel_compartido() confirma que el contenedor usa el mismo kernel", kernel_compartido() is True),
        ])

    return tests


def main() -> int:
    print("=== MODULO 5 (SEMANA 12): AISLAMIENTO POR NAMESPACES ===")
    motivo = motivo_omision()
    if motivo:
        print(f"[OMITIDO] ejecucion real de namespaces omitida ({motivo})")
    print("\n=== VERIFICACION ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())

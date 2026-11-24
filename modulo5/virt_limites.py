from __future__ import annotations

import math
import os
import subprocess
import sys

from virt_comun import (
    CONTROL,
    es_linux,
    imprimir_verificaciones,
    servicios_delifiis,
)

CODIGO_SALIDA_OOM = 137
PROPIOS = {"holgura": 1.25}


def cuota_sugerida_mb(mb_app: int | float, holgura: float = PROPIOS["holgura"]) -> int:
    """Calcula la cuota sugerida en MB redondeada hacia arriba."""
    if mb_app <= 0:
        raise ValueError("La memoria base de la aplicacion debe ser mayor que cero")
    if holgura < 1:
        raise ValueError("La holgura debe ser mayor o igual a 1")
    return math.ceil(mb_app * holgura)


def cuotas_delifiis(holgura: float = PROPIOS["holgura"]) -> dict[str, int]:
    """Devuelve {id_servicio: cuota_mb} para los servicios propios P1-P4."""
    servicios = servicios_delifiis()
    return {
        pid: cuota_sugerida_mb(datos["mb"], holgura)
        for pid, datos in servicios.items()
    }


def probar_ulimit(limite_kb: int, reserva_mb: int = 200) -> str | None:
    """Prueba RLIMIT_AS en un subproceso de Python (solo Linux).

    Devuelve 'OK', 'MemoryError', 'ERROR' o None si no es Linux.
    """
    if not es_linux():
        return None

    import resource

    codigo = (
        f"buf = bytearray({reserva_mb} * 1024 * 1024)\n"
        "print('OK')\n"
    )
    limite_bytes = limite_kb * 1024

    def _fijar_limite() -> None:
        resource.setrlimit(resource.RLIMIT_AS, (limite_bytes, limite_bytes))

    proc = subprocess.run(
        [sys.executable, "-c", codigo],
        preexec_fn=_fijar_limite,
        capture_output=True,
        text=True,
    )

    if proc.returncode == 0 and "OK" in proc.stdout:
        return "OK"
    if "MemoryError" in proc.stderr:
        return "MemoryError"
    return "ERROR"


def info_cgroup() -> dict[str, int | str | None]:
    """Inspecciona la version de cgroups, ruta actual y memory.max (solo lectura)."""
    if not es_linux():
        return {"version": None, "ruta": None, "memory_max": None}

    version: int | None = None
    if os.path.exists("/sys/fs/cgroup/cgroup.controllers"):
        version = 2
    elif os.path.exists("/sys/fs/cgroup/memory"):
        version = 1

    ruta: str | None = None
    if os.path.exists("/proc/self/cgroup"):
        try:
            with open("/proc/self/cgroup", "r", encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if linea.startswith("0::"):
                        ruta = linea.split("::", 1)[1]
                        break
        except OSError:
            ruta = None

    memory_max: str | None = None
    if version == 2 and ruta is not None:
        ruta_limpia = ruta.lstrip("/")
        ruta_mem = (
            os.path.join("/sys/fs/cgroup", ruta_limpia, "memory.max")
            if ruta_limpia
            else "/sys/fs/cgroup/memory.max"
        )
        if os.path.exists(ruta_mem):
            try:
                with open(ruta_mem, "r", encoding="utf-8") as f:
                    memory_max = f.read().strip()
            except OSError:
                memory_max = None

    return {"version": version, "ruta": ruta, "memory_max": memory_max}


def verificar() -> list[tuple[str, bool]]:
    """Verifica cuotas propias, validaciones, cgroup y ulimit en Linux."""
    pruebas: list[tuple[str, bool]] = []

    pruebas.append((
        "propio: cuota_sugerida_mb(512) == 640 y cuota_sugerida_mb(768) == 960",
        cuota_sugerida_mb(512) == 640 and cuota_sugerida_mb(768) == 960,
    ))

    err_mb = False
    try:
        cuota_sugerida_mb(0)
    except ValueError:
        err_mb = True

    err_holgura = False
    try:
        cuota_sugerida_mb(512, holgura=0.9)
    except ValueError:
        err_holgura = True

    pruebas.append((
        "validacion: ValueError si mb_app <= 0 o holgura < 1",
        err_mb and err_holgura,
    ))

    cuotas = cuotas_delifiis()
    pruebas.append((
        "propio: cuotas_delifiis() == P1:640, P2:640, P3:960, P4:960 (total 3200 MB)",
        cuotas == {"P1": 640, "P2": 640, "P3": 960, "P4": 960} and sum(cuotas.values()) == 3200,
    ))

    cg = info_cgroup()
    pruebas.append((
        "info_cgroup() devuelve claves version, ruta y memory_max",
        set(cg.keys()) == {"version", "ruta", "memory_max"},
    ))

    if es_linux():
        res_100 = probar_ulimit(102400)
        res_300 = probar_ulimit(307200)
        pruebas.append((
            "control (Linux): ulimit 102 400 KB -> MemoryError",
            res_100 == CONTROL["ulimit_kb"][102400],
        ))
        pruebas.append((
            "control (Linux): ulimit 307 200 KB -> OK",
            res_300 == CONTROL["ulimit_kb"][307200],
        ))

    return pruebas


def main() -> int:
    print("=== MODULO 5 (SEMANA 12) - LIMITES DE RECURSOS (ULIMIT Y CGROUPS) ===")
    cuotas = cuotas_delifiis()
    print(f"[propio] Holgura={PROPIOS['holgura']} -> Cuotas: {cuotas} (Total: {sum(cuotas.values())} MB)")
    print(f"[info] Codigo salida OOM Killer: {CODIGO_SALIDA_OOM}")
    print(f"[info] Cgroup detectado: {info_cgroup()}")

    if not es_linux():
        print("[OMITIDO] probar_ulimit requiere entorno Linux (WSL o VM)")

    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())
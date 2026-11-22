"""Modulo 5 (semana 12) - virt_jaula.py
Caso: DeliFIIS. Rol 2: jaula chroot con las fichas reales y verificacion de integridad.
Salida sin tildes (Windows).
"""

from __future__ import annotations

import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile

_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)
for _d in ("modulo4", "modulo5"):
    _p = os.path.abspath(os.path.join(_AQUI, "..", _d))
    if _p not in sys.path:
        sys.path.insert(0, _p)

from virt_comun import es_linux, es_root, herramienta_disponible, imprimir_verificaciones
from sec_cifrado import huella

try:
    from modulo4.fs_integracion import SistemaArchivosIntegrado
except ImportError:
    from fs_integracion import SistemaArchivosIntegrado  # type: ignore

_RUTA_ACCESO_SRC = os.path.join(_AQUI, "acceso_real.c")
_RUTA_ACCESO_BIN = os.path.join(_AQUI, "acceso_real")

# Valores esperados de las 4 fichas (segun tabla 4 de la semana 12)
TABLA_FICHAS_ESPERADAS = {
    "/cocina/recetas/fichas/ficha_P1.txt": {"tamano": 75, "modo": 0o640, "huella_16": "d27a687dff1b1207"},
    "/cocina/recetas/fichas/ficha_P2.txt": {"tamano": 78, "modo": 0o640, "huella_16": "87160aff41420e6e"},
    "/cocina/recetas/fichas/ficha_P3.txt": {"tamano": 73, "modo": 0o640, "huella_16": "f166fbb2571aed18"},
    "/cocina/recetas/fichas/ficha_P4.txt": {"tamano": 75, "modo": 0o640, "huella_16": "a4337608a56526af"},
}


def resolver_en_jaula(raiz: str, ruta: str) -> str:
    """Normaliza ruta como si raiz fuera /; .. nunca sale de la raiz. Pura."""
    norm = posixpath.normpath(posixpath.join("/", ruta))
    if norm == "/":
        return posixpath.normpath(raiz)
    return posixpath.join(posixpath.normpath(raiz), norm.lstrip("/"))


def fichas_para_jaula() -> dict[str, tuple[bytes, int]]:
    """Extrae las 4 fichas de S10 con su contenido y modo de permisos."""
    sfa = SistemaArchivosIntegrado()
    resultado = {}
    for pid in ("P1", "P2", "P3", "P4"):
        ruta = f"/cocina/recetas/fichas/ficha_{pid}.txt"
        res = sfa.abrir_ficha(ruta, "chef", "r")
        cont = res["contenido"] if isinstance(res["contenido"], bytes) else res["contenido"].encode("utf-8")
        modo = res["inodo"].permisos
        resultado[ruta] = (cont, modo)
    return resultado


def motivo_omision() -> str | None:
    """None si es Linux, hay gcc y es_root(); si no, motivo descriptivo."""
    if not es_linux():
        return "no es Linux"
    if not herramienta_disponible("gcc"):
        return "falta gcc"
    if not es_root():
        return "requiere root (usa sudo)"
    return None


def compilar_acceso_real() -> str | None:
    """Compila modulo5/acceso_real.c si gcc esta disponible."""
    if not herramienta_disponible("gcc"):
        return None
    necesita = not os.path.exists(_RUTA_ACCESO_BIN)
    if not necesita and os.path.exists(_RUTA_ACCESO_SRC):
        necesita = os.path.getmtime(_RUTA_ACCESO_SRC) > os.path.getmtime(_RUTA_ACCESO_BIN)
    if necesita:
        cmd = ["gcc", "-Wall", "-Wextra", "-O2", _RUTA_ACCESO_SRC, "-o", _RUTA_ACCESO_BIN]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0:
            return None
    return _RUTA_ACCESO_BIN


def _copiar_con_dependencias(binario: str, destino_bin_dir: str, raiz_jaula: str) -> bool:
    """Copia un binario y sus bibliotecas dinamicas resueltas por ldd."""
    if not os.path.exists(binario):
        return False
    os.makedirs(destino_bin_dir, exist_ok=True)
    shutil.copy2(binario, destino_bin_dir)

    try:
        ldd_out = subprocess.run(["ldd", binario], capture_output=True, text=True).stdout
        rutas_lib = re.findall(r"(/[\w.\-]+(?:/[\w.\-]+)+)", ldd_out)
        for lib in rutas_lib:
            if os.path.exists(lib) and os.path.isfile(lib):
                rel_dir = os.path.dirname(lib).lstrip("/")
                target_dir = os.path.join(raiz_jaula, rel_dir)
                os.makedirs(target_dir, exist_ok=True)
                target_file = os.path.join(target_dir, os.path.basename(lib))
                if not os.path.exists(target_file):
                    shutil.copy2(lib, target_file)
    except Exception:
        pass
    return True


def abrir_en_jaula(ruta: str) -> dict | None:
    """Abre y comprueba una ficha dentro de un chroot real. Solo Linux + root + gcc."""
    if motivo_omision() is not None:
        return None

    bin_acceso = compilar_acceso_real()
    if not bin_acceso:
        return None

    fichas = fichas_para_jaula()
    if ruta not in fichas:
        return None

    contenido_esperado, _ = fichas[ruta]
    h16_esperada = huella(contenido_esperado)[:16]

    jaula = tempfile.mkdtemp(prefix="jaula_", dir="/tmp")
    try:
        bin_dir = os.path.join(jaula, "bin")
        os.makedirs(bin_dir, exist_ok=True)

        for b in ("/bin/cat", "/bin/ls", bin_acceso):
            _copiar_con_dependencias(b, bin_dir, jaula)

        for r_ficha, (datos_bytes, modo_int) in fichas.items():
            destino_real = resolver_en_jaula(jaula, r_ficha)
            os.makedirs(os.path.dirname(destino_real), exist_ok=True)
            with open(destino_real, "wb") as f:
                f.write(datos_bytes)
            os.chmod(destino_real, modo_int)

        # 1. Leer contenido con cat dentro de chroot
        res_cat = subprocess.run(["chroot", jaula, "/bin/cat", ruta], capture_output=True)
        contenido_leido = res_cat.stdout
        h16_leida = huella(contenido_leido)[:16] if res_cat.returncode == 0 else ""

        # 2. Verificar que /home no exista
        res_ls = subprocess.run(["chroot", jaula, "/bin/ls", "/home"], capture_output=True)
        home_visible = (res_ls.returncode == 0)

        # 3. Consultar modo con acceso_real
        res_acc = subprocess.run(["chroot", jaula, "/bin/acceso_real", ruta], capture_output=True, text=True)
        salida_acc = res_acc.stdout.strip()
        partes = salida_acc.split()
        modo_en_jaula = partes[1] if len(partes) >= 2 else ""

        return {
            "ruta": ruta,
            "huella_16": h16_leida,
            "huella_coincide": (h16_leida == h16_esperada),
            "modo_en_jaula": modo_en_jaula,
            "home_visible": home_visible,
        }
    except Exception:
        return None
    finally:
        shutil.rmtree(jaula, ignore_errors=True)


def verificar() -> list[tuple[str, bool]]:
    """Verifica resolucion de rutas, metadatos de fichas y chroot si hay root."""
    tests: list[tuple[str, bool]] = [
        ("resolver_en_jaula bloquea escape .. a /etc/passwd",
         resolver_en_jaula("/tmp/j", "/cocina/../../etc/passwd") == "/tmp/j/etc/passwd"),
        ("resolver_en_jaula normaliza componentes intermedios",
         resolver_en_jaula("/tmp/j", "/a/./b") == "/tmp/j/a/b"),
        ("resolver_en_jaula procesa ruta relativa desde la raiz",
         resolver_en_jaula("/tmp/j", "x") == "/tmp/j/x"),
        ("resolver_en_jaula resuelve raiz exacta",
         resolver_en_jaula("/tmp/j", "/") == "/tmp/j"),
    ]

    fichas = fichas_para_jaula()
    for ruta, esp in TABLA_FICHAS_ESPERADAS.items():
        nom = os.path.basename(ruta)
        cont, modo = fichas[ruta]
        h16 = huella(cont)[:16]
        tests.extend([
            (f"{nom}: tamano {esp['tamano']} bytes", len(cont) == esp["tamano"]),
            (f"{nom}: modo octal 0o640", modo == esp["modo"]),
            (f"{nom}: huella 16 hex coincide ({esp['huella_16']})", h16 == esp["huella_16"]),
        ])

    motivo = motivo_omision()
    if motivo is None:
        for ruta in TABLA_FICHAS_ESPERADAS:
            nom = os.path.basename(ruta)
            info = abrir_en_jaula(ruta)
            tests.extend([
                (f"{nom}: huella intacta dentro de la jaula chroot",
                 info is not None and info["huella_coincide"] is True),
                (f"{nom}: modo 640 verificado por acceso_real en jaula",
                 info is not None and info["modo_en_jaula"] == "640"),
                (f"{nom}: /home no visible dentro del chroot",
                 info is not None and info["home_visible"] is False),
            ])

    return tests


def main() -> int:
    print("=== MODULO 5 (SEMANA 12): JAULA CHROOT E INTEGRIDAD ===")
    motivo = motivo_omision()
    if motivo:
        print(f"[OMITIDO] pruebas reales en chroot omitidas ({motivo})")
    print("\n=== VERIFICACION ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())

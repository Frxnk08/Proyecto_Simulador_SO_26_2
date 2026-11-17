"""Modulo 5 (semana 11) - Contrasenas y autenticacion.
Caso: DeliFIIS. Rol 3: Leonel.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)

from sec_comun import CONTROL, SAL_1, SAL_2, imprimir_verificaciones

CLAVES_DEMO = {
    "chef": "Chef-Demo-2026",
    "ayudante": "ceviche123",
    "visitante": "ceviche123",
}


def hash_sha256(clave: str) -> str:
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


def hash_pbkdf2(clave: str, sal: bytes, iteraciones: int = 100_000) -> str:
    return hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal, iteraciones).hex()


def crear_almacen(claves: dict[str, str], iteraciones: int = 100_000) -> dict:
    almacen = {}
    for usuario, clave in claves.items():
        sal = os.urandom(16)
        almacen[usuario] = {
            "sal": sal,
            "hash": hash_pbkdf2(clave, sal, iteraciones),
            "iter": iteraciones,
        }
    return almacen


def autenticar(almacen: dict, usuario: str, clave: str) -> bool:
    if not isinstance(almacen, dict) or usuario not in almacen:
        return False
    reg = almacen[usuario]
    h_calc = hash_pbkdf2(clave, reg["sal"], reg.get("iter", 100_000))
    return hmac.compare_digest(h_calc, reg["hash"])


def tiempo_fuerza_bruta(simbolos: int, largo: int, velocidad: int = 10**9) -> float:
    return (simbolos ** largo) / velocidad


def verificar() -> list[tuple[str, bool]]:
    almacen = crear_almacen(CLAVES_DEMO)
    h_sal1 = hash_pbkdf2(CONTROL["clave"], SAL_1)
    h_sal2 = hash_pbkdf2(CONTROL["clave"], SAL_2)

    return [
        ("SHA-256 de control coincide (55e006c7...)", hash_sha256(CONTROL["clave"]).startswith(CONTROL["sha256_16"])),
        ("PBKDF2 con sal 1 coincide (d1dc65b6...)", h_sal1.startswith(CONTROL["pbkdf2_16"]["sal1"])),
        ("PBKDF2 con sal 2 coincide (708b03c6...)", h_sal2.startswith(CONTROL["pbkdf2_16"]["sal2"])),
        ("SHA-256 sin sal repite el mismo hash", hash_sha256("abc") == hash_sha256("abc")),
        ("PBKDF2 con sales distintas produce hashes diferentes", h_sal1 != h_sal2),
        ("almacen: registros con sal, hash e iter", all("sal" in v and "hash" in v for v in almacen.values())),
        ("almacen: clave compartida da hashes distintos por la sal", almacen["ayudante"]["hash"] != almacen["visitante"]["hash"]),
        ("autenticar usuarios validos devuelve True", all(autenticar(almacen, u, c) for u, c in CLAVES_DEMO.items())),
        ("autenticar clave incorrecta devuelve False", not autenticar(almacen, "chef", "clave-falsa")),
        ("autenticar usuario inexistente devuelve False", not autenticar(almacen, "nadie", "123")),
        ("combinaciones fuerza bruta coinciden con control", all(s ** l == comb for s, l, comb in CONTROL["fuerza_bruta"].values())),
        ("tiempos fuerza bruta control (3.5 min y 2.53 dias)", round(tiempo_fuerza_bruta(26, 8) / 60, 1) == 3.5 and round(tiempo_fuerza_bruta(62, 8) / 86400, 2) == 2.53),
        ("caso propio: 14 minusculas resiste mas de 2000 anios", tiempo_fuerza_bruta(26, 14) / (86400 * 365.25) > 2000),
    ]


def main() -> int:
    print("=== MODULO 5: CONTRASENAS Y HASH (DeliFIIS) ===")
    almacen = crear_almacen(CLAVES_DEMO)
    for u, c in CLAVES_DEMO.items():
        print(f"Usuario: {u:<10} Clave: {c:<16} -> {'OK' if autenticar(almacen, u, c) else 'FALLO'}")
    print("\n=== VERIFICACION ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())

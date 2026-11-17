"""Modulo 5 (semana 11) - Cifrado, integridad y firmas.
Caso: DeliFIIS. Rol 3: Leonel.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)

from sec_comun import CONTROL, herramienta_disponible, imprimir_verificaciones

CORREO_CHEF = "chef@delifiis.test"


def huella(datos: bytes | str) -> str:
    if isinstance(datos, str):
        datos = datos.encode("utf-8")
    return hashlib.sha256(datos).hexdigest()


def manifiesto(sfa, rutas: list[str]) -> dict[str, str]:
    return {r: huella(sfa.abrir_ficha(r, "chef", "r").get("contenido", b"")) for r in rutas}


def _ejecutar_gpg(args: list[str], entrada: bytes = b"", homedir: str | None = None) -> subprocess.CompletedProcess:
    if not herramienta_disponible("gpg"):
        raise RuntimeError("GPG no disponible")
    cmd = ["gpg"] + (["--homedir", homedir] if homedir else []) + args
    return subprocess.run(cmd, input=entrada, capture_output=True, env=dict(os.environ, LC_ALL="C"))


def crear_llavero(homedir: str, email: str = CORREO_CHEF) -> bool:
    return _ejecutar_gpg(["--batch", "--pinentry-mode", "loopback", "--passphrase", "",
                          "--quick-generate-key", email, "default", "default", "never"], homedir=homedir).returncode == 0


def cifrar_simetrico(datos: bytes, clave: str, homedir: str) -> bytes:
    return _ejecutar_gpg(["--batch", "--yes", "--pinentry-mode", "loopback",
                          "--passphrase", clave, "-c", "--cipher-algo", "AES256"], entrada=datos, homedir=homedir).stdout


def descifrar_simetrico(datos: bytes, clave: str, homedir: str) -> bytes:
    r = _ejecutar_gpg(["--batch", "--pinentry-mode", "loopback", "--passphrase", clave, "-d"], entrada=datos, homedir=homedir)
    if r.returncode != 0:
        raise ValueError(r.stderr.decode("utf-8", errors="ignore"))
    return r.stdout


def cifrar_asimetrico(datos: bytes, receptor: str, homedir: str) -> bytes:
    return _ejecutar_gpg(["--batch", "--yes", "--trust-model", "always", "--armor", "-r", receptor, "-e"], entrada=datos, homedir=homedir).stdout


def descifrar_asimetrico(datos: bytes, homedir: str) -> bytes:
    return _ejecutar_gpg(["--batch", "--pinentry-mode", "loopback", "--passphrase", "", "-d"], entrada=datos, homedir=homedir).stdout


def firmar(datos: bytes, usuario: str, homedir: str) -> bytes:
    return _ejecutar_gpg(["--batch", "--yes", "--pinentry-mode", "loopback",
                          "--passphrase", "", "--armor", "--detach-sign", "-u", usuario], entrada=datos, homedir=homedir).stdout


def verificar_firma(datos: bytes, firma: bytes, homedir: str) -> bool:
    p_in, p_sig = os.path.join(homedir, "doc.tmp"), os.path.join(homedir, "doc.sig")
    try:
        with open(p_in, "wb") as f1, open(p_sig, "wb") as f2:
            f1.write(datos); f2.write(firma)
        return _ejecutar_gpg(["--batch", "--verify", p_sig, p_in], homedir=homedir).returncode == 0
    finally:
        for p in (p_in, p_sig):
            if os.path.exists(p): os.remove(p)


def verificar() -> list[tuple[str, bool]]:
    try:
        from modulo4.fs_integracion import SistemaArchivosIntegrado
    except ImportError:
        from fs_integracion import SistemaArchivosIntegrado  # type: ignore
    sfa = SistemaArchivosIntegrado()
    rutas = ["/cocina/recetas/fichas/ficha_P1.txt", "/cocina/recetas/entradas/ceviche.txt"]
    man = manifiesto(sfa, rutas)

    tests = [
        ("huella genera hash de 64 caracteres", len(huella(b"receta")) == 64),
        ("modificar un caracter cambia completamente la huella", huella(b"receta") != huella(b"receta!")),
        ("manifiesto de fichas DeliFIIS coincide (P1 y ceviche)", man[rutas[0]].startswith("d27a687d") and man[rutas[1]].startswith("ef040120")),
    ]

    if herramienta_disponible("gpg"):
        h = tempfile.mkdtemp()
        try:
            crear_llavero(h, CORREO_CHEF)
            cif = cifrar_simetrico(b"secreto", "clave123", h)
            dec = descifrar_simetrico(cif, "clave123", h)
            cif_asym = cifrar_asimetrico(b"confidencial", CORREO_CHEF, h)
            dec_asym = descifrar_asimetrico(cif_asym, h)
            sig = firmar(b"documento", CORREO_CHEF, h)
            tests.extend([
                ("gpg simetrico AES-256 cifra y descifra OK", dec == b"secreto"),
                ("gpg asimetrico cifra y descifra con par de claves", dec_asym == b"confidencial"),
                ("gpg firma valida con datos intactos y rechaza alterados", verificar_firma(b"documento", sig, h) and not verificar_firma(b"alterado", sig, h)),
            ])
        finally:
            shutil.rmtree(h, ignore_errors=True)
    else:
        tests.append(("herramienta gpg no instalada: omitido sin error en Windows", True))

    return tests


def main() -> int:
    print("=== MODULO 5: CIFRADO E INTEGRIDAD (DeliFIIS) ===")
    print(f"Huella SHA-256 de ejemplo: {huella(b'DeliFIIS')}")
    print(f"GPG disponible en PATH: {'SI' if herramienta_disponible('gpg') else 'NO (modo simulacion)'}")
    print("\n=== VERIFICACION ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())

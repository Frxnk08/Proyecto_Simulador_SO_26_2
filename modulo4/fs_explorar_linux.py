
from __future__ import annotations

import os
import shutil
import stat
import tempfile

from fs_comun import CONTROL, imprimir_verificaciones


def es_entorno_linux() -> bool:
    """Devuelve True si el sistema operativo soporta llamadas POSIX reales."""
    return os.name == "posix"


def ejecutar_pruebas_reales() -> list[tuple[str, bool]]:
    """Ejecuta las pruebas reales en /tmp mediante tempfile.mkdtemp()."""
    pruebas: list[tuple[str, bool]] = []
    dir_temporal = tempfile.mkdtemp(prefix="delifiis_s10_")
    umask_original = os.umask(0o022)

    try:
        ruta_ceviche = os.path.join(dir_temporal, "ceviche.txt")
        ruta_dur = os.path.join(dir_temporal, "dur.txt")
        ruta_sim = os.path.join(dir_temporal, "sim.txt")

        contenido = "Receta DeliFIIS en sistema de archivos real"
        with open(ruta_ceviche, "w", encoding="utf-8") as f:
            f.write(contenido)

        os.link(ruta_ceviche, ruta_dur)
        os.symlink(ruta_ceviche, ruta_sim)

        st_orig = os.stat(ruta_ceviche)
        st_dur = os.stat(ruta_dur)
        st_sim = os.lstat(ruta_sim)

        pruebas.append((
            "Linux real: dur.txt comparte st_ino y st_nlink == 2",
            st_orig.st_ino == st_dur.st_ino and st_orig.st_nlink == 2,
        ))
        pruebas.append((
            "Linux real: sim.txt tiene st_ino distinto y es symlink",
            st_sim.st_ino != st_orig.st_ino and stat.S_ISLNK(st_sim.st_mode),
        ))

        os.unlink(ruta_ceviche)

        with open(ruta_dur, "r", encoding="utf-8") as f:
            lectura_dur = f.read()
        st_dur_despues = os.stat(ruta_dur)

        pruebas.append((
            "Linux real: dur.txt sigue leyendo tras borrar original y st_nlink == 1",
            lectura_dur == contenido and st_dur_despues.st_nlink == 1,
        ))

        sim_roto = False
        try:
            with open(ruta_sim, "r", encoding="utf-8") as f:
                f.read()
        except FileNotFoundError:
            sim_roto = True

        pruebas.append((
            "Linux real: sim.txt queda roto (FileNotFoundError) tras borrar original",
            sim_roto,
        ))

        os.chmod(ruta_dur, 0o640)
        modo_ceviche = stat.S_IMODE(os.stat(ruta_dur).st_mode)
        esperado_ceviche = CONTROL["matriz_permisos"]["ceviche.txt"][0]
        pruebas.append((
            "Linux real: chmod 640 verificado contra control",
            modo_ceviche == esperado_ceviche,
        ))

        ruta_stock = os.path.join(dir_temporal, "stock.csv")
        with open(ruta_stock, "w", encoding="utf-8") as f:
            f.write("insumo,cantidad\n")
        os.chmod(ruta_stock, 0o660)
        modo_stock = stat.S_IMODE(os.stat(ruta_stock).st_mode)
        esperado_stock = CONTROL["matriz_permisos"]["stock.csv"][0]
        pruebas.append((
            "Linux real: chmod 660 verificado contra control",
            modo_stock == esperado_stock,
        ))

        os.umask(0o022)
        f_022 = os.path.join(dir_temporal, "arch_022.txt")
        d_022 = os.path.join(dir_temporal, "dir_022")
        fd = os.open(f_022, os.O_CREAT | os.O_WRONLY, 0o666)
        os.close(fd)
        os.mkdir(d_022, 0o777)

        m_f022 = stat.S_IMODE(os.stat(f_022).st_mode)
        m_d022 = stat.S_IMODE(os.stat(d_022).st_mode)
        esp_f022, esp_d022 = CONTROL["umask"]["022"]
        pruebas.append((
            "Linux real: umask 022 genera archivo 644 y directorio 755",
            m_f022 == esp_f022 and m_d022 == esp_d022,
        ))

        os.umask(0o077)
        f_077 = os.path.join(dir_temporal, "arch_077.txt")
        d_077 = os.path.join(dir_temporal, "dir_077")
        fd2 = os.open(f_077, os.O_CREAT | os.O_WRONLY, 0o666)
        os.close(fd2)
        os.mkdir(d_077, 0o777)

        m_f077 = stat.S_IMODE(os.stat(f_077).st_mode)
        m_d077 = stat.S_IMODE(os.stat(d_077).st_mode)
        esp_f077, esp_d077 = CONTROL["umask"]["077"]
        pruebas.append((
            "Linux real: umask 077 genera archivo 600 y directorio 700",
            m_f077 == esp_f077 and m_d077 == esp_d077,
        ))

    finally:
        os.umask(umask_original)
        shutil.rmtree(dir_temporal, ignore_errors=True)

    return pruebas


def verificar() -> list[tuple[str, bool]]:
    """Ejecuta pruebas en Linux; en Windows avisa y retorna verificacion aprobada."""
    if not es_entorno_linux():
        print("[aviso] Entorno no POSIX (Windows): ejecutar en WSL, VM o LabEx para pruebas reales.")
        return [("Entorno Windows detectado: ejecucion real omitida sin error", True)]
    return ejecutar_pruebas_reales()


def main() -> int:
    print("=== MODULO 4 (SEMANA 10) - EXPLORACION REAL EN LINUX ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())
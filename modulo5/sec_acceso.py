from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from sec_comun import (
    CONTROL,
    USUARIOS,
    es_linux,
    herramienta_disponible,
    imprimir_verificaciones,
)

try:
    import fs_permisos
except ImportError:
    fs_permisos = None

try:
    from fs_integracion import SistemaArchivosIntegrado
except ImportError:
    SistemaArchivosIntegrado = None


PROPIOS = {
    "matriz": {
        "/cocina/recetas/entradas/ceviche.txt": {
            "chef": (True, True),
            "ayudante": (True, False),
            "visitante": (False, False),
        },
        "/cocina/inventario/stock.csv": {
            "chef": (True, True),
            "ayudante": (True, True),
            "visitante": (False, False),
        },
        "/cocina/recetas/fichas/ficha_P1.txt": {
            "chef": (True, True),
            "ayudante": (True, False),
            "visitante": (False, False),
        },
        "/cocina/recetas/fichas/ficha_P2.txt": {
            "chef": (True, True),
            "ayudante": (True, False),
            "visitante": (False, False),
        },
        "/cocina/recetas/fichas/ficha_P3.txt": {
            "chef": (True, True),
            "ayudante": (True, False),
            "visitante": (False, False),
        },
        "/cocina/recetas/fichas/ficha_P4.txt": {
            "chef": (True, True),
            "ayudante": (True, False),
            "visitante": (False, False),
        },
        "/cocina/finanzas/caja.log": {
            "chef": (True, False),
            "ayudante": (False, False),
            "visitante": (False, False),
        },
        "/cocina/pedidos/buzon_pedidos.txt": {
            "chef": (True, False),
            "ayudante": (False, True),
            "visitante": (False, False),
        },
        "/cocina/recetas/menu_publico.txt": {
            "chef": (True, True),
            "ayudante": (True, False),
            "visitante": (True, False),
        },
    },
    "nuevos_s10": [
        ("/cocina/finanzas/caja.log", b"total_dia=1450.00\n", [0], 0o400),
        ("/cocina/pedidos/buzon_pedidos.txt", b"pedido_mesa_4\n", [1], 0o420),
        ("/cocina/recetas/menu_publico.txt", b"Ceviche, Lomo, Causa\n", [2], 0o644),
    ],
}

MATRIZ_DELIFIIS = PROPIOS["matriz"]


def acl_desde_matriz(
    matriz: dict[str, dict[str, tuple[bool, bool]]],
) -> dict[str, dict[str, tuple[str, ...]]]:
    """Vista por archivo (columna): {archivo: {usuario: ('leer', 'escribir')}}."""
    acl: dict[str, dict[str, tuple[str, ...]]] = {}
    for archivo, fila in matriz.items():
        entradas: dict[str, tuple[str, ...]] = {}
        for usuario, (lee, escribe) in fila.items():
            acciones: list[str] = []
            if lee:
                acciones.append("leer")
            if escribe:
                acciones.append("escribir")
            if acciones:
                entradas[usuario] = tuple(acciones)
        acl[archivo] = entradas
    return acl


def capacidades_desde_matriz(
    matriz: dict[str, dict[str, tuple[bool, bool]]],
) -> dict[str, dict[str, tuple[str, ...]]]:
    """Vista por usuario (fila): {usuario: {archivo: ('leer', 'escribir')}}."""
    caps: dict[str, dict[str, tuple[str, ...]]] = {u: {} for u in USUARIOS}
    for archivo, fila in matriz.items():
        for usuario, (lee, escribe) in fila.items():
            if usuario not in caps:
                caps[usuario] = {}
            acciones: list[str] = []
            if lee:
                acciones.append("leer")
            if escribe:
                acciones.append("escribir")
            if acciones:
                caps[usuario][archivo] = tuple(acciones)
    return caps


def modo_desde_matriz(fila: dict[str, tuple[bool, bool]]) -> int:
    """Convierte permisos (lee, escribe) de chef/ayudante/visitante a octal (x=0)."""
    def _bits(perm: tuple[bool, bool]) -> int:
        lee, escribe = perm
        return (4 if lee else 0) + (2 if escribe else 0)

    u_bits = _bits(fila.get("chef", (False, False)))
    g_bits = _bits(fila.get("ayudante", (False, False)))
    o_bits = _bits(fila.get("visitante", (False, False)))
    return (u_bits << 6) | (g_bits << 3) | o_bits


def matriz_esperada(ruta: str) -> dict[str, tuple[bool, bool]] | None:
    """Interfaz publica (Seccion 3): devuelve {usuario: (lee, escribe)} o None."""
    fila = MATRIZ_DELIFIIS.get(ruta)
    return dict(fila) if fila is not None else None


def consultar_kernel(rutas: list[str]) -> dict[str, tuple[int, bool, bool]]:
    """Compila acceso_real.c en /tmp y consulta stat/access al kernel de Linux."""
    if not (es_linux() and herramienta_disponible("gcc")):
        return {}

    aqui = os.path.dirname(os.path.abspath(__file__))
    fuente_c = os.path.join(aqui, "acceso_real.c")
    if not os.path.exists(fuente_c):
        return {}

    dir_temp = tempfile.mkdtemp(prefix="sec_acceso_")
    binario = os.path.join(dir_temp, "acceso_real")
    resultados: dict[str, tuple[int, bool, bool]] = {}

    try:
        subprocess.run(
            ["gcc", "-Wall", "-Wextra", "-O2", fuente_c, "-o", binario],
            check=True,
            capture_output=True,
            text=True,
        )
        proc = subprocess.run(
            [binario, *rutas],
            check=True,
            capture_output=True,
            text=True,
        )
        for linea in proc.stdout.strip().splitlines():
            partes = linea.split()
            if len(partes) == 4:
                ruta_out, modo_str, lee_str, esc_str = partes
                resultados[ruta_out] = (
                    int(modo_str, 8),
                    lee_str == "SI",
                    esc_str == "SI",
                )
    finally:
        shutil.rmtree(dir_temp, ignore_errors=True)

    return resultados


def verificar() -> list[tuple[str, bool]]:
    """Verifica ACL, capacidades, modos octales, S10 y kernel Linux."""
    pruebas: list[tuple[str, bool]] = []

    modos_calc = {
        arch: modo_desde_matriz(fila)
        for arch, fila in CONTROL["matriz"].items()
    }
    pruebas.append((
        "CONTROL: modos octales receta.txt(640), stock.csv(660), caja.log(400)",
        modos_calc == CONTROL["modos"],
    ))

    acl_ctrl = acl_desde_matriz(CONTROL["matriz"])
    caps_ctrl = capacidades_desde_matriz(CONTROL["matriz"])
    pruebas.append((
        "CONTROL: ACL de receta.txt coincide",
        acl_ctrl.get("receta.txt") == CONTROL["acl_receta"],
    ))
    pruebas.append((
        "CONTROL: capacidades de ayudante coinciden",
        caps_ctrl.get("ayudante") == CONTROL["capacidades_ayudante"],
    ))

    if fs_permisos is not None and hasattr(fs_permisos, "matriz"):
        ida_vuelta_ok = True
        for _, fila in list(CONTROL["matriz"].items()) + list(MATRIZ_DELIFIIS.items()):
            modo = modo_desde_matriz(fila)
            if fs_permisos.matriz(modo) != fila:
                ida_vuelta_ok = False
                break
        pruebas.append((
            "Ida y vuelta matriz -> modo -> matriz con fs_permisos.matriz",
            ida_vuelta_ok,
        ))
    else:
        print("[aviso] fs_permisos no disponible; se omite ida y vuelta")

    pruebas.append((
        "Interfaz matriz_esperada: buzon_pedidos.txt (420) y ruta inexistente (None)",
        matriz_esperada("/cocina/pedidos/buzon_pedidos.txt")
        == {"chef": (True, False), "ayudante": (False, True), "visitante": (False, False)}
        and matriz_esperada("/cocina/no_existe.txt") is None,
    ))

    if SistemaArchivosIntegrado is not None:
        sfa = SistemaArchivosIntegrado()
        for ruta_nueva, contenido, bloques, perm in PROPIOS["nuevos_s10"]:
            sfa.agregar_archivo(ruta_nueva, contenido, bloques, permisos=perm)
        sfa.disco.reiniciar_contadores()

        inodos_ok = True
        for ruta, fila in MATRIZ_DELIFIIS.items():
            info = sfa.abrir_ficha(ruta, "chef", "r")
            if info["inodo"].permisos != modo_desde_matriz(fila):
                inodos_ok = False
                break
        pruebas.append((
            "S10 SistemaArchivosIntegrado: permisos de las 9 rutas coinciden",
            inodos_ok,
        ))
    else:
        print("[aviso] fs_integracion no disponible; se omite prueba S10")

    if es_linux() and herramienta_disponible("gcc"):
        dir_prueba = tempfile.mkdtemp(prefix="delifiis_kernel_")
        try:
            casos_kernel = [
                ("ceviche.txt", "/cocina/recetas/entradas/ceviche.txt"),
                ("stock.csv", "/cocina/inventario/stock.csv"),
                ("ficha_P1.txt", "/cocina/recetas/fichas/ficha_P1.txt"),
                ("caja.log", "/cocina/finanzas/caja.log"),
                ("buzon_pedidos.txt", "/cocina/pedidos/buzon_pedidos.txt"),
                ("menu_publico.txt", "/cocina/recetas/menu_publico.txt"),
            ]
            rutas_fisicas: list[str] = []
            esperado_kernel: dict[str, tuple[int, bool, bool]] = {}

            for nombre_f, ruta_logica in casos_kernel:
                ruta_f = os.path.join(dir_prueba, nombre_f)
                with open(ruta_f, "w", encoding="utf-8") as f:
                    f.write("datos\n")
                fila = MATRIZ_DELIFIIS[ruta_logica]
                modo = modo_desde_matriz(fila)
                os.chmod(ruta_f, modo)
                rutas_fisicas.append(ruta_f)
                lee_chef, esc_chef = fila["chef"]
                if os.geteuid() == 0:
                    esc_chef = True
                esperado_kernel[ruta_f] = (modo, lee_chef, esc_chef)

            res_kernel = consultar_kernel(rutas_fisicas)
            pruebas.append((
                "Linux real (acceso_real.c): modos y permisos de chef coinciden con kernel",
                res_kernel == esperado_kernel,
            ))
        finally:
            shutil.rmtree(dir_prueba, ignore_errors=True)
    else:
        print("[aviso] Linux o gcc no disponible; se omite prueba de acceso_real.c")

    return pruebas


def main() -> int:
    print("=== MODULO 5 (SEMANA 11) - CONTROL DE ACCESO ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())
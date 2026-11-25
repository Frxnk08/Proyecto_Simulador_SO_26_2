"""Modulo 5 (semana 12) - Comparador general de virtualizacion.

Caso DeliFIIS. Carga nueve modulos mediante importlib, ejecuta sus funciones
verificar() y comprueba que aislar.c compile cuando gcc esta disponible.
La compilacion se realiza en un directorio temporal y el binario no se ejecuta.
"""

from __future__ import annotations

import importlib
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace


_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)


MODULOS_VIRTUALIZACION = [
    ("Datos comunes", "virt_comun"),
    ("Capacidad del servidor", "virt_capacidad"),
    ("Hipervisores y recomendacion", "virt_hipervisores"),
    ("Aislamiento con namespaces", "virt_aislamiento"),
    ("Jaula chroot", "virt_jaula"),
    ("Limites de recursos", "virt_limites"),
    ("Cuotas de memoria", "virt_cuotas_memoria"),
    ("Comandos de despliegue", "virt_comandos"),
    ("Integracion de virtualizacion", "virt_integracion"),
]

ESTADOS = {"OK", "PENDIENTE", "OMITIDO", "FALLO"}


def _resultado(nombre, etiqueta, estado, mensaje="", pruebas=None):
    if estado not in ESTADOS:
        raise ValueError("estado desconocido: %s" % estado)
    pruebas = [] if pruebas is None else pruebas
    return {
        "nombre": nombre,
        "etiqueta": etiqueta,
        "estado": estado,
        "mensaje": mensaje,
        "pruebas": pruebas,
        "correctas": sum(1 for _descripcion, cumple in pruebas if cumple),
        "total": len(pruebas),
    }


def evaluar_modulo(etiqueta, nombre, importador=importlib.import_module):
    """Importa un modulo y evalua verificar(), sin detener a los demas."""
    try:
        modulo = importador(nombre)
    except ModuleNotFoundError as error:
        if error.name == nombre:
            return _resultado(
                nombre, etiqueta, "PENDIENTE",
                "%s.py aun no esta disponible" % nombre,
            )
        return _resultado(
            nombre, etiqueta, "FALLO",
            "dependencia ausente al importar: %s" % (error.name or error),
        )
    except Exception as error:
        return _resultado(
            nombre, etiqueta, "FALLO",
            "error inesperado al importar: %s" % error,
        )

    verificar_modulo = getattr(modulo, "verificar", None)
    if not callable(verificar_modulo):
        return _resultado(
            nombre, etiqueta, "FALLO", "no define verificar()",
        )

    try:
        obtenidas = verificar_modulo()
        if not isinstance(obtenidas, (list, tuple)) or not obtenidas:
            return _resultado(
                nombre, etiqueta, "FALLO",
                "verificar() no devolvio una lista no vacia",
            )

        pruebas = []
        for indice, prueba in enumerate(obtenidas, 1):
            if not isinstance(prueba, (list, tuple)) or len(prueba) != 2:
                return _resultado(
                    nombre, etiqueta, "FALLO",
                    "verificacion %d tiene formato invalido" % indice,
                )
            descripcion, cumple = prueba
            pruebas.append((str(descripcion), bool(cumple)))
    except Exception as error:
        return _resultado(
            nombre, etiqueta, "FALLO",
            "verificar() lanzo una excepcion: %s" % error,
        )

    estado = "OK" if all(cumple for _descripcion, cumple in pruebas) else "FALLO"
    mensaje = "%d/%d verificaciones correctas" % (
        sum(1 for _descripcion, cumple in pruebas if cumple), len(pruebas)
    )
    return _resultado(nombre, etiqueta, estado, mensaje, pruebas)


def verificar_modulos(modulos=None, importador=importlib.import_module):
    """Devuelve el resultado de los nueve modulos en el orden acordado."""
    seleccion = MODULOS_VIRTUALIZACION if modulos is None else modulos
    return [
        evaluar_modulo(etiqueta, nombre, importador)
        for etiqueta, nombre in seleccion
    ]


def comprobar_aislar_c(
        ruta=None, buscar_gcc=shutil.which, ejecutar=subprocess.run,
        detectar_sistema=platform.system):
    """Compila aislar.c en temporal si gcc existe; nunca ejecuta el binario."""
    fuente = ruta or os.path.join(_AQUI, "aislar.c")
    if not os.path.isfile(fuente):
        return {
            "estado": "PENDIENTE",
            "mensaje": "aislar.c aun no esta disponible",
            "comando": None,
        }

    sistema = str(detectar_sistema()).strip() or "desconocido"
    if sistema.lower() != "linux":
        return {
            "estado": "OMITIDO",
            "mensaje": (
                "sistema %s incompatible; aislar.c requiere un compilador Linux"
                % sistema
            ),
            "comando": None,
        }

    gcc = buscar_gcc("gcc")
    if not gcc:
        return {
            "estado": "OMITIDO",
            "mensaje": "Linux sin gcc; compilacion no comprobada",
            "comando": None,
        }

    try:
        with tempfile.TemporaryDirectory(prefix="delifiis_aislar_") as temporal:
            salida = os.path.join(temporal, "aislar")
            comando = [gcc, "-Wall", "-Wextra", "-O2", fuente, "-o", salida]
            proceso = ejecutar(
                comando,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if proceso.returncode == 0:
                return {
                    "estado": "OK",
                    "mensaje": "aislar.c compila con -Wall -Wextra -O2",
                    "comando": comando,
                }
            diagnostico = (proceso.stderr or proceso.stdout or "sin diagnostico").strip()
            primera_linea = diagnostico.splitlines()[0] if diagnostico else "sin diagnostico"
            return {
                "estado": "FALLO",
                "mensaje": "aislar.c no compila: %s" % primera_linea,
                "comando": comando,
            }
    except subprocess.TimeoutExpired:
        return {
            "estado": "FALLO",
            "mensaje": "la compilacion de aislar.c excedio 30 segundos",
            "comando": None,
        }
    except Exception as error:
        return {
            "estado": "FALLO",
            "mensaje": "no se pudo comprobar aislar.c: %s" % error,
            "comando": None,
        }


def verificar():
    """Pruebas deterministas del clasificador y del conteo del comparador."""
    modulo_ok = SimpleNamespace(verificar=lambda: [("correcta", True)])
    modulo_fallo = SimpleNamespace(verificar=lambda: [("incorrecta", False)])
    modulo_sin_verificar = SimpleNamespace()

    def importar_ok(_nombre):
        return modulo_ok

    def importar_fallo(_nombre):
        return modulo_fallo

    def importar_sin_verificar(_nombre):
        return modulo_sin_verificar

    def importar_ausente(nombre):
        raise ModuleNotFoundError("modulo ausente", name=nombre)

    def importar_dependencia(_nombre):
        raise ModuleNotFoundError("dependencia ausente", name="dependencia_interna")

    def importar_excepcion(_nombre):
        raise RuntimeError("error simulado")

    uno = [("Prueba", "modulo_prueba")]
    r_ok = verificar_modulos(uno, importar_ok)[0]
    r_fallo = verificar_modulos(uno, importar_fallo)[0]
    r_sin = verificar_modulos(uno, importar_sin_verificar)[0]
    r_ausente = verificar_modulos(uno, importar_ausente)[0]
    r_dependencia = verificar_modulos(uno, importar_dependencia)[0]
    r_excepcion = verificar_modulos(uno, importar_excepcion)[0]

    fuente_c = os.path.join(_AQUI, "aislar.c")

    class ProcesoSimulado:
        def __init__(self, returncode, stderr=""):
            self.returncode = returncode
            self.stderr = stderr
            self.stdout = ""

    def ejecucion_prohibida(*_args, **_kwargs):
        raise AssertionError("no se debe invocar gcc fuera de Linux")

    def compilacion_correcta(*_args, **_kwargs):
        return ProcesoSimulado(0)

    def compilacion_fallida(*_args, **_kwargs):
        return ProcesoSimulado(1, "error C simulado")

    c_ausente = comprobar_aislar_c(
        os.path.join(_AQUI, "aislar_ausente.c"),
        detectar_sistema=lambda: "Linux",
    )
    c_windows = comprobar_aislar_c(
        fuente_c, buscar_gcc=lambda _nombre: "gcc.exe",
        ejecutar=ejecucion_prohibida, detectar_sistema=lambda: "Windows",
    )
    c_linux_sin_gcc = comprobar_aislar_c(
        fuente_c, buscar_gcc=lambda _nombre: None,
        detectar_sistema=lambda: "Linux",
    )
    c_linux_ok = comprobar_aislar_c(
        fuente_c, buscar_gcc=lambda _nombre: "gcc",
        ejecutar=compilacion_correcta, detectar_sistema=lambda: "Linux",
    )
    c_linux_fallo = comprobar_aislar_c(
        fuente_c, buscar_gcc=lambda _nombre: "gcc",
        ejecutar=compilacion_fallida, detectar_sistema=lambda: "Linux",
    )

    return [
        ("se comparan exactamente nueve modulos", len(MODULOS_VIRTUALIZACION) == 9),
        ("un modulo correcto produce OK y cuenta una prueba",
         r_ok["estado"] == "OK" and r_ok["correctas"] == 1 and r_ok["total"] == 1),
        ("una verificacion falsa produce FALLO", r_fallo["estado"] == "FALLO"),
        ("un modulo sin verificar() produce FALLO", r_sin["estado"] == "FALLO"),
        ("un modulo inexistente produce PENDIENTE", r_ausente["estado"] == "PENDIENTE"),
        ("una dependencia ausente produce FALLO", r_dependencia["estado"] == "FALLO"),
        ("una excepcion inesperada produce FALLO", r_excepcion["estado"] == "FALLO"),
        ("aislar.c ausente produce PENDIENTE", c_ausente["estado"] == "PENDIENTE"),
        ("Windows con gcc nativo produce OMITIDO", c_windows["estado"] == "OMITIDO"),
        ("Linux sin gcc produce OMITIDO", c_linux_sin_gcc["estado"] == "OMITIDO"),
        ("Linux con compilacion correcta produce OK", c_linux_ok["estado"] == "OK"),
        ("Linux con error real de compilacion produce FALLO",
         c_linux_fallo["estado"] == "FALLO"
         and "error C simulado" in c_linux_fallo["mensaje"]),
    ]


def _imprimir_resultado_modulo(resultado):
    print("[%s] %s (%s.py): %s" % (
        resultado["estado"], resultado["etiqueta"],
        resultado["nombre"], resultado["mensaje"],
    ))
    if resultado["estado"] in ("OK", "FALLO") and resultado["pruebas"]:
        for descripcion, cumple in resultado["pruebas"]:
            print("  [%s] %s" % ("OK" if cumple else "FALLO", descripcion))


def main():
    print("===============================================================")
    print("  MODULO 5: COMPARACION GENERAL DE VIRTUALIZACION - DeliFIIS")
    print("===============================================================\n")

    resultados = verificar_modulos()
    for resultado in resultados:
        _imprimir_resultado_modulo(resultado)
        print()

    comprobacion_c = comprobar_aislar_c()
    print("[%s] aislar.c: %s\n" % (
        comprobacion_c["estado"], comprobacion_c["mensaje"]
    ))

    internas = verificar()
    correctas_internas = sum(1 for _descripcion, cumple in internas if cumple)
    print("Verificaciones internas del comparador: %d/%d" % (
        correctas_internas, len(internas)
    ))

    modulos_ok = sum(1 for resultado in resultados if resultado["estado"] == "OK")
    pruebas_correctas = sum(resultado["correctas"] for resultado in resultados)
    pruebas_totales = sum(resultado["total"] for resultado in resultados)
    pendientes = [r["nombre"] for r in resultados if r["estado"] == "PENDIENTE"]
    fallidos = [r["nombre"] for r in resultados if r["estado"] == "FALLO"]

    print("Verificaciones de modulos: %d/%d" % (pruebas_correctas, pruebas_totales))
    print("Modulos verificados con exito: %d / %d" % (
        modulos_ok, len(MODULOS_VIRTUALIZACION)
    ))
    if pendientes:
        print("Modulos pendientes: %s" % ", ".join(pendientes))
    if fallidos:
        print("Modulos con fallo: %s" % ", ".join(fallidos))

    internas_ok = correctas_internas == len(internas)
    hay_fallo = bool(fallidos) or comprobacion_c["estado"] == "FALLO" or not internas_ok
    hay_pendiente = bool(pendientes) or comprobacion_c["estado"] == "PENDIENTE"

    if hay_fallo:
        print("RESULTADO: FALLO")
        return 1
    if modulos_ok == len(MODULOS_VIRTUALIZACION) and not hay_pendiente:
        print("RESULTADO: OK")
        return 0
    print("RESULTADO: PARCIAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

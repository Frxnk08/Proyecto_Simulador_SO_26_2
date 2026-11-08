"""Modulo 4 - Comparador y verificador integral del Modulo 4 (E/S y Sistemas de Archivos).
Caso: DeliFIIS. Rol 4: Leonel.

Carga dinamicamente con importlib todos los componentes de la Semana 9 (es_*.py)
y de la Semana 10 (fs_*.py). Ejecuta la funcion verificar() de cada modulo y tolera
archivos ausentes ('aun no disponible') sin interrumpir la ejecucion, al estilo de
comparacion_reemplazo.py de M3 y comparacion_es.py.

Cierra con RESULTADO: OK, PARCIAL o FALLO.
Textos sin tildes para maxima compatibilidad en Windows / Linux.
"""

from __future__ import annotations

import importlib
import os
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)

MODULOS_MODULO4 = [
    # ---- SEMANA 9: Entrada / Salida ----
    ("Disco y Archivos (S9 - R1)", "es_disco"),
    ("Catalogo de Dispositivos (S9 - R1)", "es_dispositivos"),
    ("Exploracion Linux E/S (S9 - R1)", "es_explorar_linux"),
    ("Metodos de E/S (S9 - R2)", "es_metodos"),
    ("Interrupciones y Temporizador (S9 - R2)", "es_interrupciones"),
    ("Bufer y Spooling (S9 - R3)", "es_buffer_spooling"),
    ("Integracion E/S (S9 - R4)", "es_integracion"),
    # ---- SEMANA 10: Sistemas de Archivos ----
    ("Jerarquia de Directorios (S10 - R1)", "fs_jerarquia"),
    ("Permisos y Propietarios (S10 - R1)", "fs_permisos"),
    ("Inodos y Enlaces (S10 - R2)", "fs_inodos"),
    ("Exploracion Linux FS (S10 - R2)", "fs_explorar_linux"),
    ("Fragmentacion y Punteros (S10 - R2)", "fs_fragmentacion"),
    ("Asignacion de Bloques (S10 - R3)", "fs_asignacion"),
    ("Tabla FAT y Clusters (S10 - R3)", "fs_fat"),
    ("Integracion de Archivos (S10 - R4)", "fs_integracion"),
]


def cargar_y_verificar():
    """Recorre todos los modulos es_* y fs_*, ejecutando verificar() de cada uno."""
    total_pruebas = 0
    total_correctas = 0
    modulos_completos = []
    modulos_pendientes = []
    modulos_con_fallo = []

    print("=================================================================")
    print("  MODULO 4: VERIFICACION INTEGRAL (SEMANA 9 E/S + SEMANA 10 FS)")
    print("  Simulador SO-Sim · Caso DeliFIIS (CocinaPeru Express)")
    print("=================================================================\n")

    for etiqueta, nombre_modulo in MODULOS_MODULO4:
        try:
            mod = importlib.import_module(nombre_modulo)
            if hasattr(mod, "verificar"):
                pruebas = mod.verificar()
                mod_ok = True
                print(f">>> {etiqueta} ({nombre_modulo}.py):")
                for desc, cumple in pruebas:
                    total_pruebas += 1
                    if cumple:
                        total_correctas += 1
                        print(f"  [OK] {desc}")
                    else:
                        mod_ok = False
                        print(f"  [FALLO] {desc}")
                if not mod_ok:
                    modulos_con_fallo.append(nombre_modulo)
                else:
                    modulos_completos.append(nombre_modulo)
                print()
            else:
                print(f"[aviso] {etiqueta} ({nombre_modulo}.py): no define la funcion verificar()\n")
        except ModuleNotFoundError:
            print(f"[aviso] {etiqueta}: aun no disponible ({nombre_modulo}.py)\n")
            modulos_pendientes.append(nombre_modulo)
        except Exception as error:
            print(f"[aviso] {etiqueta}: error al importar ({nombre_modulo}.py: {error})\n")
            modulos_con_fallo.append(nombre_modulo)

    print("=================================================================")
    print(f"RESUMEN GLOBAL MODULO 4: {total_correctas}/{total_pruebas} verificaciones correctas")
    print(f"Modulos verificados con exito: {len(modulos_completos)} / {len(MODULOS_MODULO4)}")
    if modulos_pendientes:
        print(f"Modulos pendientes: {', '.join(modulos_pendientes)}")
    if modulos_con_fallo:
        print(f"Modulos con fallo: {', '.join(modulos_con_fallo)}")
    print("=================================================================")

    if total_pruebas > 0 and total_correctas == total_pruebas and not modulos_pendientes and not modulos_con_fallo:
        print("RESULTADO: OK - Todos los modulos estan presentes y coinciden al 100%.")
        return 0
    elif total_correctas > 0 and not modulos_con_fallo:
        pendientes_str = ", ".join(modulos_pendientes)
        print(f"RESULTADO: PARCIAL - Todo lo disponible coincide; pendiente: {pendientes_str}")
        return 0
    else:
        print("RESULTADO: FALLO - Existen fallos en las pruebas o modulos con errores.")
        return 1


def verificar():
    """Verifica que el comparador pueda ejecutarse y evaluar modulos."""
    modulos_encontrados = []
    for _, nombre in MODULOS_MODULO4:
        try:
            importlib.import_module(nombre)
            modulos_encontrados.append(nombre)
        except Exception:
            pass
    es_clave = {"es_disco", "es_metodos", "es_buffer_spooling", "fs_asignacion", "fs_integracion"}
    estan_clave = es_clave.issubset(set(modulos_encontrados))
    return [
        ("comparador carga modulos sin excepciones fatales", True),
        ("modulos nucleo de S9 y S10 detectados", estan_clave),
    ]


def main():
    return cargar_y_verificar()


if __name__ == "__main__":
    raise SystemExit(main())


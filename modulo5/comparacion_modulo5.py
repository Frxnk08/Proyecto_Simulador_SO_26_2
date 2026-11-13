"""Modulo 5 - Comparador y verificador integral del Modulo 5 (Seguridad y Proteccion).
Caso: DeliFIIS. Rol 4: Franco.

Carga con importlib los archivos sec_*.py de la semana 11, ejecuta la funcion
verificar() de cada uno y tolera archivos ausentes ('aun no disponible') sin
interrumpir la ejecucion, igual que comparacion_modulo4.py.

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

MODULOS_MODULO5 = [
    # ---- SEMANA 11: Seguridad y Proteccion ----
    ("Amenazas e Incidentes (S11 - R1)", "sec_amenazas"),
    ("Firewall (S11 - R1)", "sec_firewall"),
    ("Control de Acceso (S11 - R2)", "sec_acceso"),
    ("Contrasenas y Hash (S11 - R3)", "sec_contrasenas"),
    ("Cifrado, Firma y GPG (S11 - R3)", "sec_cifrado"),
    ("Integracion de Seguridad (S11 - R4)", "sec_integracion"),
]


def cargar_y_verificar():
    """Recorre los sec_*.py, ejecutando verificar() de cada uno."""
    total_pruebas = 0
    total_correctas = 0
    completos, pendientes, con_fallo = [], [], []

    print("=================================================================")
    print("  MODULO 5: VERIFICACION INTEGRAL (SEMANA 11 SEGURIDAD Y PROTECCION)")
    print("  Simulador SO-Sim - Caso DeliFIIS")
    print("=================================================================\n")

    for etiqueta, nombre_modulo in MODULOS_MODULO5:
        try:
            mod = importlib.import_module(nombre_modulo)
        except ModuleNotFoundError as error:
            if error.name == nombre_modulo:
                print(f"[aviso] {etiqueta}: aun no disponible ({nombre_modulo}.py)\n")
                pendientes.append(nombre_modulo)
            else:  # el modulo existe pero le falta otra dependencia
                print(f"[aviso] {etiqueta}: error al importar ({nombre_modulo}.py: {error})\n")
                con_fallo.append(nombre_modulo)
            continue
        except Exception as error:
            print(f"[aviso] {etiqueta}: error al importar ({nombre_modulo}.py: {error})\n")
            con_fallo.append(nombre_modulo)
            continue

        if not hasattr(mod, "verificar"):
            print(f"[aviso] {etiqueta} ({nombre_modulo}.py): no define la funcion verificar()\n")
            continue
        try:
            pruebas = mod.verificar()
        except Exception as error:
            print(f"[aviso] {etiqueta}: verificar() fallo con una excepcion ({error})\n")
            con_fallo.append(nombre_modulo)
            continue

        ok_modulo = True
        print(f">>> {etiqueta} ({nombre_modulo}.py):")
        for desc, cumple in pruebas:
            total_pruebas += 1
            if cumple:
                total_correctas += 1
                print(f"  [OK] {desc}")
            else:
                ok_modulo = False
                print(f"  [FALLO] {desc}")
        (completos if ok_modulo else con_fallo).append(nombre_modulo)
        print()

    print("=================================================================")
    print(f"RESUMEN GLOBAL MODULO 5: {total_correctas}/{total_pruebas} verificaciones correctas")
    print(f"Modulos verificados con exito: {len(completos)} / {len(MODULOS_MODULO5)}")
    if pendientes:
        print(f"Modulos pendientes: {', '.join(pendientes)}")
    if con_fallo:
        print(f"Modulos con fallo: {', '.join(con_fallo)}")
    print("=================================================================")

    if total_pruebas > 0 and total_correctas == total_pruebas and not pendientes and not con_fallo:
        print("RESULTADO: OK - Todos los modulos estan presentes y coinciden al 100%.")
        return 0
    if total_correctas > 0 and not con_fallo:
        print(f"RESULTADO: PARCIAL - Todo lo disponible coincide; pendiente: {', '.join(pendientes)}")
        return 0
    print("RESULTADO: FALLO - Existen fallos en las pruebas o modulos con errores.")
    return 1


def verificar():
    """Verifica que el comparador pueda ejecutarse y que sec_comun tenga los valores de control."""
    try:
        import sec_comun
        control_ok = all(k in sec_comun.CONTROL for k in ("sha256_16", "fuerza_bruta", "matriz", "modos", "reglas", "gpg"))
    except Exception:
        control_ok = False
    return [
        ("sec_comun expone los valores de control de la semana 11", control_ok),
        ("lista de modulos del M5 definida (6 archivos de verificacion)", len(MODULOS_MODULO5) == 6),
    ]


def main():
    return cargar_y_verificar()


if __name__ == "__main__":
    raise SystemExit(main())
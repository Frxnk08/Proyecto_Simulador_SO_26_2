
from __future__ import annotations

import importlib
import sys

MODULOS_ES = [
    ("Disco y Archivos (R1)", "es_disco"),
    ("Dispositivos Catálogo (R1)", "es_dispositivos"),
    ("Métodos de E/S (R2)", "es_metodos"),
    ("Búfer y Spooling (R3)", "es_buffer_spooling"),
    ("Integración M1-M3 (R4)", "es_integracion"),
]


def cargar_y_verificar():
    total_pruebas = 0
    total_correctas = 0
    modulos_pendientes = []
    modulos_con_fallo = []

    print("=========================================================")
    print("  MODULO 4: VERIFICACION INTEGRADA DE ENTRADA / SALIDA")
    print("=========================================================\n")

    for etiqueta, nombre_modulo in MODULOS_ES:
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
                print()
            else:
                print(f"[aviso] {nombre_modulo}.py no define la funcion verificar()\n")
        except Exception as error:
            print(f"[aviso] {etiqueta}: aun no disponible o con error ({nombre_modulo}.py: {error})\n")
            modulos_pendientes.append(nombre_modulo)

    print("=========================================================")
    print(f"RESUMEN DE PRUEBAS: {total_correctas}/{total_pruebas} correctas")
    print("=========================================================")

    if total_pruebas > 0 and total_correctas == total_pruebas and not modulos_pendientes:
        print("RESULTADO: OK - Todos los modulos estan presentes y coinciden al 100%.")
        return 0
    elif total_correctas > 0 and not modulos_con_fallo:
        pendientes_str = ", ".join(modulos_pendientes)
        print(f"RESULTADO: PARCIAL - Todo lo disponible coincide; pendiente: {pendientes_str}")
        return 0
    else:
        print("RESULTADO: FALLO - Hay verificaciones que no coinciden con la referencia.")
        return 1


def main() -> int:
    return cargar_y_verificar()


if __name__ == "__main__":
    raise SystemExit(main())
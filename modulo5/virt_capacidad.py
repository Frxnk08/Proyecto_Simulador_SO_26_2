"""Modulo 5 (semana 12) - virt_capacidad.py
Caso: DeliFIIS. Rol 1: cuantos servicios caben en un servidor con maquinas
virtuales (VM) y con contenedores (Parte B de la practica dirigida).
Perfiles: CONTROL (PPT y practica del docente) y PROPIO (valores del equipo).
Salida sin tildes (Windows).
"""

from __future__ import annotations

from virt_comun import CONTROL, imprimir_verificaciones, servicios_delifiis

# Valores PROPIOS del equipo (supuestos didacticos, distintos de los de control)
PROPIOS = {
    "total_mb": 24 * 1024,
    "reserva_mb": 4 * 1024,
    "so_invitado_mb": 1536,
    "sobrecarga_mb": 40,
}


def calcular_capacidad(total_mb, reserva_mb, apps, so_invitado_mb, sobrecarga_mb):
    """Devuelve un dict con la capacidad del servidor para VM y contenedores.

    apps: {nombre: MB que usa la aplicacion}. Un 'juego' es una copia completa
    de todas las aplicaciones.
    """
    if not apps:
        raise ValueError("apps no puede estar vacio")
    valores = [total_mb, so_invitado_mb, sobrecarga_mb, *apps.values()]
    if any(v <= 0 for v in valores):
        raise ValueError("todos los valores deben ser mayores que cero")
    if reserva_mb < 0 or reserva_mb >= total_mb:
        raise ValueError("la reserva debe ser menor que la memoria total")

    disponible = total_mb - reserva_mb
    juego_vm = sum(so_invitado_mb + mb for mb in apps.values())
    juego_ct = sum(sobrecarga_mb + mb for mb in apps.values())
    juegos_vm = disponible // juego_vm
    juegos_ct = disponible // juego_ct
    return {
        "disponible": disponible,
        "juego_vm": juego_vm,
        "juegos_vm": juegos_vm,
        "sobra_vm": disponible - juegos_vm * juego_vm,
        "juego_ct": juego_ct,
        "juegos_ct": juegos_ct,
        "sobra_ct": disponible - juegos_ct * juego_ct,
        "veces": round(juegos_ct / juegos_vm, 2) if juegos_vm else None,
    }


def capacidad_control(nombre):
    """nombre: 'ppt' (ejemplo de la PPT) o 'practica' (Parte B de la practica)."""
    if nombre not in ("ppt", "practica"):
        raise ValueError("el perfil de control debe ser 'ppt' o 'practica'")
    c = CONTROL[nombre]
    return calcular_capacidad(c["total_mb"], c["reserva_mb"], c["apps"],
                              c["so_invitado_mb"], c["sobrecarga_mb"])


def capacidad_propia():
    """Perfil PROPIO: las apps salen de los pedidos P1-P4 de M1 (tamano x MB por estante)."""
    apps = {id_: s["mb"] for id_, s in servicios_delifiis().items()}
    return calcular_capacidad(PROPIOS["total_mb"], PROPIOS["reserva_mb"], apps,
                              PROPIOS["so_invitado_mb"], PROPIOS["sobrecarga_mb"])


# Valores esperados (ver el Doc de la semana 12)
ESPERADO = {
    "ppt": {"disponible": 14336, "juego_vm": 2560, "juegos_vm": 5, "sobra_vm": 1536,
            "juego_ct": 562, "juegos_ct": 25, "sobra_ct": 286, "veces": 5.0},
    "practica": {"disponible": 28672, "juego_vm": 8448, "juegos_vm": 3, "sobra_vm": 3328,
                 "juego_ct": 2484, "juegos_ct": 11, "sobra_ct": 1348, "veces": 3.67},
    "propio": {"disponible": 20480, "juego_vm": 8704, "juegos_vm": 2, "sobra_vm": 3072,
               "juego_ct": 2720, "juegos_ct": 7, "sobra_ct": 1440, "veces": 3.5},
}


def _lanza_value_error(funcion, *args):
    try:
        funcion(*args)
    except ValueError:
        return True
    return False


def verificar():
    resultados = {
        "ppt": capacidad_control("ppt"),
        "practica": capacidad_control("practica"),
        "propio": capacidad_propia(),
    }
    etiquetas = {"ppt": "control PPT", "practica": "control practica", "propio": "propio DeliFIIS"}
    ver = []
    for perfil, esperado in ESPERADO.items():
        obtenido = resultados[perfil]
        for clave, valor in esperado.items():
            ver.append((f"{etiquetas[perfil]}: {clave} = {valor}", obtenido[clave] == valor))
        ver.append((f"{etiquetas[perfil]}: lo que sobra es menor que un juego",
                    obtenido["sobra_vm"] < obtenido["juego_vm"]
                    and obtenido["sobra_ct"] < obtenido["juego_ct"]))
    p = CONTROL["practica"]
    args = (p["total_mb"], p["reserva_mb"], p["apps"], p["so_invitado_mb"], p["sobrecarga_mb"])
    ver.append(("ValueError con apps vacio",
                _lanza_value_error(calcular_capacidad, args[0], args[1], {}, args[3], args[4])))
    ver.append(("ValueError con un valor menor o igual a cero",
                _lanza_value_error(calcular_capacidad, args[0], args[1], {"x": 0}, args[3], args[4])))
    ver.append(("ValueError con reserva mayor o igual que el total",
                _lanza_value_error(calcular_capacidad, 1000, 1000, {"x": 100}, 50, 10)))
    return ver


def _imprimir(titulo, r):
    print(f"\n{titulo}")
    print("-" * 64)
    print(f"Memoria disponible          : {r['disponible']:>8} MB")
    print(f"Juego completo en VM        : {r['juego_vm']:>8} MB -> caben {r['juegos_vm']:>2} (sobran {r['sobra_vm']} MB)")
    print(f"Juego completo en contened. : {r['juego_ct']:>8} MB -> caben {r['juegos_ct']:>2} (sobran {r['sobra_ct']} MB)")
    print(f"Contenedores caben {r['veces']} veces mas juegos que las VM")


def main():
    print("=== VIRTUALIZACION: CAPACIDAD DEL SERVIDOR (VM vs contenedores) ===")
    print("Perfiles de CONTROL (PPT y practica del docente) y PROPIO (valores del equipo).")
    _imprimir("[CONTROL] PPT: 16 GB, reserva 2 GB, app de 512 MB", capacidad_control("ppt"))
    _imprimir("[CONTROL] Practica: 32 GB, reserva 4 GB, 3 apps", capacidad_control("practica"))
    _imprimir("[PROPIO] DeliFIIS: 24 GB, reserva 4 GB, apps P1-P4 de M1", capacidad_propia())
    print("\nNota: contenedores caben mas, pero comparten el kernel del anfitrion:")
    print("se pierde aislamiento. Valores didacticos (simulacion educativa).\n")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())
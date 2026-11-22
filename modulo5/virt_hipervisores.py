"""Modulo 5 (semana 12) - virt_hipervisores.py
Caso: DeliFIIS. Rol 1: tipo de hipervisor y decision VM o contenedor
(Parte A de la practica dirigida).
Perfiles: CONTROL (PPT/practica del docente) y PROPIO (casos de DeliFIIS).
Salida sin tildes (Windows).
"""

from __future__ import annotations

from virt_comun import imprimir_verificaciones

# ---- CONTROL: clasificacion de la PPT de la semana 12 ----
# KVM convierte el kernel de Linux en un hipervisor tipo 1.
HIPERVISORES = {
    "VMware ESXi": 1,
    "Oracle VirtualBox": 2,
    "Microsoft Hyper-V": 1,
    "KVM": 1,
    "Xen": 1,
    "VMware Workstation": 2,
}

CLAVES = ("otro_kernel", "aislamiento_fuerte", "codigo_no_confiable", "escalado_rapido")

_RAZONES_VM = {
    "otro_kernel": "necesita otro kernel o SO distinto del anfitrion",
    "aislamiento_fuerte": "requiere aislamiento fuerte (frontera de hardware virtual)",
    "codigo_no_confiable": "ejecuta codigo no confiable: conviene la frontera de la VM",
}


def tipo_hipervisor(nombre):
    """Devuelve 1 (bare-metal) o 2 (alojado). Sin distinguir mayusculas."""
    buscado = str(nombre).strip().lower()
    for clave, tipo in HIPERVISORES.items():
        if clave.lower() == buscado:
            return tipo
    raise ValueError(f"hipervisor desconocido: {nombre!r}")


def recomendar(req):
    """req: dict de booleanos con claves de CLAVES (por defecto False).

    Devuelve ("VM" | "contenedor", [razones]).
    """
    desconocidas = set(req) - set(CLAVES)
    if desconocidas:
        raise ValueError(f"claves desconocidas: {sorted(desconocidas)}")
    razones_vm = [_RAZONES_VM[c] for c in CLAVES[:3] if req.get(c, False)]
    if razones_vm:
        return "VM", razones_vm
    if req.get("escalado_rapido", False):
        return "contenedor", ["necesita crear y eliminar copias en segundos (arranque rapido)"]
    return "contenedor", ["mismo kernel y carga liviana"]


# ---- Escenarios de CONTROL (practica, Parte A) ----
# Respuestas esperadas deducidas de la PPT (el docente no publica solucion).
ESCENARIOS_CONTROL = [
    ("Windows y Linux a la vez en una laptop", {"otro_kernel": True}, "VM"),
    ("30 copias del servicio de pedidos que se crean o eliminan en segundos",
     {"escalado_rapido": True}, "contenedor"),
    ("Analizar un programa sospechoso sin arriesgar el servidor",
     {"codigo_no_confiable": True}, "VM"),
    ("Sistema contable heredado con kernel y SO antiguos", {"otro_kernel": True}, "VM"),
]

# ---- Escenarios PROPIOS (valores del equipo, caso DeliFIIS) ----
ESCENARIOS_PROPIOS = [
    ("E1 replicar el servicio de pedidos P1-P4 segun la demanda",
     {"escalado_rapido": True}, "contenedor"),
    ("E2 servidor de caja con caja.log (modo 400, confidencial, semana 11)",
     {"aislamiento_fuerte": True}, "VM"),
    ("E3 probar una ficha descargada sospechosa",
     {"codigo_no_confiable": True}, "VM"),
    ("E4 sucursal con inventario antiguo que exige otro kernel",
     {"otro_kernel": True}, "VM"),
    ("E5 menu_publico.txt (644) servido por web",
     {"escalado_rapido": True}, "contenedor"),
]


def _lanza_value_error(funcion, *args):
    try:
        funcion(*args)
    except ValueError:
        return True
    return False


def verificar():
    ver = []
    esperados = {"VMware ESXi": 1, "Oracle VirtualBox": 2, "Microsoft Hyper-V": 1,
                 "KVM": 1, "Xen": 1, "VMware Workstation": 2}
    for nombre, tipo in esperados.items():
        ver.append((f"control: {nombre} es tipo {tipo}", tipo_hipervisor(nombre) == tipo))
    ver.append(("tipo_hipervisor ignora mayusculas (kvm)", tipo_hipervisor("kvm") == 1))
    for i, (texto, req, esperado) in enumerate(ESCENARIOS_CONTROL, 1):
        ver.append((f"control escenario {i}: {esperado}", recomendar(req)[0] == esperado))
    for texto, req, esperado in ESCENARIOS_PROPIOS:
        ver.append((f"propio {texto[:2]}: {esperado}", recomendar(req)[0] == esperado))
    ver.append(("sin requisitos: contenedor por carga liviana",
                recomendar({}) == ("contenedor", ["mismo kernel y carga liviana"])))
    ver.append(("ValueError con hipervisor desconocido", _lanza_value_error(tipo_hipervisor, "Docker")))
    ver.append(("ValueError con clave desconocida", _lanza_value_error(recomendar, {"gpu": True})))
    return ver


def main():
    print("=== VIRTUALIZACION: HIPERVISORES Y ESCENARIOS ===")
    print("\n[CONTROL] Tipo de hipervisor (PPT semana 12):")
    for nombre in HIPERVISORES:
        t = tipo_hipervisor(nombre)
        print(f"  {nombre:<20} tipo {t} ({'bare-metal' if t == 1 else 'alojado'})")
    for titulo, escenarios in (("[CONTROL] Escenarios de la practica (Parte A):", ESCENARIOS_CONTROL),
                               ("[PROPIO] Escenarios de DeliFIIS:", ESCENARIOS_PROPIOS)):
        print(f"\n{titulo}")
        for texto, req, _ in escenarios:
            decision, razones = recomendar(req)
            print(f"  {texto}\n    -> {decision}: {razones[0]}")
    print()
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())
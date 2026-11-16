"""Modulo 5 (semana 11) - Amenazas e incidentes de seguridad.
Caso: DeliFIIS. Rol 1: clasificacion CIA y auditoria de accesos denegados.
"""

from __future__ import annotations

from sec_comun import CONTROL, imprimir_verificaciones
from fs_integracion import SistemaArchivosIntegrado


# Valores de CONTROL de la practica dirigida. No describen permisos nuevos del
# proyecto: son escenarios didacticos que deben conservarse tal como se piden.
INCIDENTES_CONTROL = [
    {
        "descripcion": "La contrasena ceviche123 fue adivinada",
        "amenaza": "Fuerza bruta",
        "vulnerabilidad": "Contrasena debil",
        "propiedad": "Confidencialidad",
        "control": "Contrasena robusta, hash con sal y segundo factor",
    },
    {
        "descripcion": "Un correo falso del banco solicita credenciales",
        "amenaza": "Phishing o ingenieria social",
        "vulnerabilidad": "Entrega de credenciales",
        "propiedad": "Confidencialidad",
        "control": "Capacitacion y autenticacion multifactor",
    },
    {
        "descripcion": "Pedidos falsos saturan la ventanilla",
        "amenaza": "Denegacion de servicio",
        "vulnerabilidad": "Falta de filtrado o limite de tasa",
        "propiedad": "Disponibilidad",
        "control": "Firewall y limitacion de solicitudes",
    },
    {
        "descripcion": "El ayudante modifica stock.csv cuando solo debia leer",
        "amenaza": "Escalada de privilegios o permisos excesivos",
        "vulnerabilidad": "Permisos mayores que los requeridos por el escenario",
        "propiedad": "Integridad",
        "control": "Minimo privilegio",
        "nota": (
            "Caso didactico: en la matriz real de Semana 10 stock.csv usa 660 "
            "y el ayudante si puede escribir. No se cambian esos permisos."
        ),
    },
    {
        "descripcion": "Un programa descargado contiene una puerta trasera",
        "amenaza": "Malware",
        "vulnerabilidad": "Software no verificado",
        "propiedad": "Confidencialidad / Integridad / Disponibilidad",
        "control": "Verificacion de hashes o firmas y minimo privilegio",
    },
]


# Valores PROPIOS del equipo, conectados con los modulos anteriores de SO-Sim.
INCIDENTES_DELIFIIS = [
    {
        "descripcion": "Dos hilos modifican el stock sin sincronizacion",
        "amenaza": "Condicion de carrera",
        "vulnerabilidad": "Actualizacion concurrente sin exclusion mutua",
        "propiedad": "Integridad",
        "control": "Mutex o semaforo",
    },
    {
        "descripcion": "Un visitante intenta leer una ficha protegida",
        "amenaza": "Acceso no autorizado",
        "vulnerabilidad": "Usuario sin permisos sobre la ficha",
        "propiedad": "Confidencialidad",
        "control": "Permisos 640 y rechazo con PermissionError",
    },
    {
        "descripcion": "Un proceso accede fuera del limite de memoria",
        "amenaza": "Acceso fuera de limites",
        "vulnerabilidad": "Direccion no validada",
        "propiedad": "Integridad",
        "control": "Proteccion base-limite",
    },
    {
        "descripcion": "Se intenta trafico hacia tcp/3306",
        "amenaza": "Acceso de red no autorizado a la base de datos",
        "vulnerabilidad": "Puerto de base de datos expuesto",
        "propiedad": "Confidencialidad",
        "control": "Politica firewall DROP",
    },
    {
        "descripcion": "Una ficha o pedido es modificado sin autorizacion",
        "amenaza": "Alteracion de datos",
        "vulnerabilidad": "Contenido sin comprobacion criptografica",
        "propiedad": "Integridad",
        "control": "SHA-256 y firma",
    },
]


def clasificar_evento(usuario, operacion, permitido, ruta=""):
    """Crea un evento CIA para un acceso denegado; los permitidos no se auditan."""
    if permitido:
        return None
    if operacion == "r":
        amenaza = "lectura no autorizada"
        propiedad = "Confidencialidad"
    elif operacion == "w":
        amenaza = "escritura no autorizada"
        propiedad = "Integridad"
    else:
        amenaza = "operacion no autorizada"
        propiedad = "Disponibilidad"
    return {
        "usuario": usuario,
        "operacion": operacion,
        "ruta": ruta,
        "amenaza": amenaza,
        "propiedad": propiedad,
    }


def _intento_real_denegado():
    """Ejecuta un rechazo real de S10 y devuelve (error, evento, lecturas)."""
    sistema = SistemaArchivosIntegrado()
    sistema.disco.reiniciar_contadores()
    ruta = "/cocina/recetas/fichas/ficha_P1.txt"
    try:
        sistema.abrir_ficha(ruta, usuario="visitante", operacion="r")
    except PermissionError as error:
        evento = clasificar_evento("visitante", "r", False, ruta)
        return error, evento, sistema.disco.accesos_lectura
    return None, None, sistema.disco.accesos_lectura


def _incidentes_completos(incidentes):
    campos = {"descripcion", "amenaza", "vulnerabilidad", "propiedad", "control"}
    return all(campos <= set(incidente) and all(incidente[c] for c in campos)
               for incidente in incidentes)


def verificar():
    lectura = clasificar_evento("visitante", "r", False, "/ficha")
    escritura = clasificar_evento("ayudante", "w", False, "/ficha")
    error, evento_real, lecturas = _intento_real_denegado()
    propiedades_control = [incidente["propiedad"] for incidente in INCIDENTES_CONTROL]
    propiedades_propias = [incidente["propiedad"] for incidente in INCIDENTES_DELIFIIS]
    escenario_stock = INCIDENTES_CONTROL[3]

    return [
        ("los cinco incidentes de CONTROL estan presentes y completos",
         len(INCIDENTES_CONTROL) == 5 and _incidentes_completos(INCIDENTES_CONTROL)),
        ("CONTROL clasifica confidencialidad, integridad y disponibilidad",
         propiedades_control == [
             "Confidencialidad", "Confidencialidad", "Disponibilidad",
             "Integridad", "Confidencialidad / Integridad / Disponibilidad",
         ]),
        ("lectura denegada produce Confidencialidad",
         lectura is not None and lectura["propiedad"] == "Confidencialidad"
         and lectura["amenaza"] == "lectura no autorizada"),
        ("escritura denegada produce Integridad",
         escritura is not None and escritura["propiedad"] == "Integridad"
         and escritura["amenaza"] == "escritura no autorizada"),
        ("una operacion permitida no genera incidente",
         clasificar_evento("chef", "r", True, "/ficha") is None),
        ("el evento conserva usuario, operacion y ruta",
         lectura is not None and (lectura["usuario"], lectura["operacion"], lectura["ruta"])
         == ("visitante", "r", "/ficha")),
        ("lectura real del visitante produce PermissionError antes de leer disco",
         isinstance(error, PermissionError) and lecturas == 0),
        ("el PermissionError real se clasifica como Confidencialidad",
         evento_real is not None and evento_real["propiedad"] == "Confidencialidad"),
        ("los cinco incidentes PROPIOS de DeliFIIS estan completos",
         len(INCIDENTES_DELIFIIS) == 5 and _incidentes_completos(INCIDENTES_DELIFIIS)),
        ("los incidentes propios cubren integridad y confidencialidad",
         propiedades_propias == [
             "Integridad", "Confidencialidad", "Integridad",
             "Confidencialidad", "Integridad",
         ]),
        ("el caso tcp/3306 propone politica firewall DROP",
         INCIDENTES_DELIFIIS[3]["control"] == "Politica firewall DROP"),
        ("la inconsistencia didactica de stock.csv queda documentada sin cambiar 660",
         "Semana 10" in escenario_stock.get("nota", "")
         and CONTROL["matriz"]["stock.csv"]["ayudante"][1] is True),
    ]


def _imprimir_incidentes(titulo, incidentes):
    print("\n" + titulo)
    for numero, incidente in enumerate(incidentes, 1):
        print("%d. %s" % (numero, incidente["descripcion"]))
        print("   Amenaza: %s | Propiedad: %s" %
              (incidente["amenaza"], incidente["propiedad"]))
        print("   Control: %s" % incidente["control"])
        if "nota" in incidente:
            print("   Nota: %s" % incidente["nota"])


def main():
    print("=== AMENAZAS E INCIDENTES - DeliFIIS ===")
    _imprimir_incidentes("--- Valores de CONTROL ---", INCIDENTES_CONTROL)
    _imprimir_incidentes("--- Incidentes PROPIOS de DeliFIIS ---", INCIDENTES_DELIFIIS)

    error, evento, lecturas = _intento_real_denegado()
    print("\n--- Auditoria real de permisos (Semana 10) ---")
    print("PermissionError: %s" % ("SI" if error else "NO"))
    print("Lecturas de disco: %d" % lecturas)
    print("Evento: %s" % evento)

    print("\n=== VERIFICACION ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())

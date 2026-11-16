"""Modulo 5 (semana 11) - Firewall educativo con reglas ordenadas.
Caso: DeliFIIS. Rol 1: evaluacion logica y generacion segura de comandos.
"""

from __future__ import annotations

import re

from sec_comun import CONTROL, imprimir_verificaciones
from simulador_planificacion import CONJUNTO_OFICIAL


# Valores PROPIOS del equipo. Son distintos de las reglas CONTROL del docente.
REGLAS_DELIFIIS = [
    ("tcp", 22, "ACCEPT"),
    ("tcp", 443, "ACCEPT"),
    ("tcp", 80, "DROP"),
    ("tcp", 3306, "DROP"),
    ("tcp", 8080, "DROP"),
]
POLITICA_DELIFIIS = "DROP"
ACCIONES = {"ACCEPT", "DROP"}


def _validar_paquete(proto, puerto):
    if not isinstance(proto, str) or not proto:
        raise ValueError("El protocolo no puede estar vacio")
    if not isinstance(puerto, int) or isinstance(puerto, bool) or not 1 <= puerto <= 65535:
        raise ValueError("El puerto debe ser un entero entre 1 y 65535")


def _validar_regla(regla):
    if not isinstance(regla, (tuple, list)) or len(regla) != 3:
        raise ValueError("Cada regla debe ser (protocolo, puerto, accion)")
    proto, puerto, accion = regla
    _validar_paquete(proto, puerto)
    if accion not in ACCIONES:
        raise ValueError("Accion invalida: %r" % (accion,))


def evaluar(proto, puerto, reglas=None, politica=None):
    """Aplica la primera regla coincidente o la politica predeterminada."""
    _validar_paquete(proto, puerto)
    reglas_activas = CONTROL["reglas"] if reglas is None else reglas
    politica_activa = CONTROL["politica"] if politica is None else politica
    if politica_activa not in ACCIONES:
        raise ValueError("Politica invalida: %r" % (politica_activa,))
    protocolo = proto.lower()
    for regla in reglas_activas:
        _validar_regla(regla)
        regla_proto, regla_puerto, accion = regla
        if protocolo == regla_proto.lower() and puerto == regla_puerto:
            return accion
    return politica_activa


def paquetes_desde_pedidos(procesos):
    """Genera un paquete HTTPS logico por cada pedido del planificador."""
    return [("tcp", 443) for _proceso in procesos]


def comandos_iptables(reglas, cadena):
    """Genera comandos de texto; nunca los ejecuta ni conecta la cadena a INPUT."""
    if not isinstance(cadena, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", cadena):
        raise ValueError("Nombre de cadena iptables invalido")
    for regla in reglas:
        _validar_regla(regla)
    comandos = [
        "iptables -N %s" % cadena,
        "iptables -A %s -i lo -j ACCEPT" % cadena,
        ("iptables -A %s -m conntrack --ctstate "
         "ESTABLISHED,RELATED -j ACCEPT" % cadena),
    ]
    for proto, puerto, accion in reglas:
        comandos.append(
            "iptables -A %s -p %s --dport %d -j %s"
            % (cadena, proto.lower(), puerto, accion)
        )
    comandos.append("iptables -A %s -j DROP" % cadena)
    return comandos


def costo_dma_paquetes(cantidad, bytes_por_paquete=1500):
    """Costo didactico reutilizado de Semana 9; no es tiempo real de red."""
    if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad < 0:
        raise ValueError("La cantidad de paquetes debe ser un entero no negativo")
    if not isinstance(bytes_por_paquete, int) or bytes_por_paquete <= 0:
        raise ValueError("El tamano del paquete debe ser positivo")
    from es_comun import evaluar as evaluar_es, obtener_perfil

    perfil = obtener_perfil("delifiis")
    red = perfil["dispositivos"]["red"]
    por_paquete = evaluar_es(
        "dma", bytes_por_paquete, red["us_por_byte"], perfil
    )["costo_us"]
    return por_paquete, cantidad * por_paquete


def verificar():
    resultados_control = {
        paquete: evaluar(paquete[0], paquete[1])
        for paquete in CONTROL["paquetes"]
    }
    regla_8080 = list(CONTROL["reglas"]) + [("tcp", 8080, "ACCEPT")]
    orden_22 = [("tcp", 22, "DROP")] + list(CONTROL["reglas"])
    paquetes = paquetes_desde_pedidos(CONJUNTO_OFICIAL)
    decisiones_pedidos = [
        evaluar(proto, puerto, REGLAS_DELIFIIS, POLITICA_DELIFIIS)
        for proto, puerto in paquetes
    ]
    comandos = comandos_iptables(CONTROL["reglas"], "COCINA")
    por_paquete, total_dma = costo_dma_paquetes(len(paquetes))

    return [
        ("todos los paquetes de CONTROL coinciden",
         resultados_control == CONTROL["paquetes"]),
        ("una regla adicional permite tcp/8080",
         evaluar("tcp", 8080, regla_8080, "DROP") == "ACCEPT"),
        ("la primera coincidencia demuestra el orden: tcp/22 -> DROP",
         evaluar("tcp", 22, orden_22, "DROP") == "DROP"),
        ("politica ACCEPT deja pasar tcp/23 sin regla",
         evaluar("tcp", 23, CONTROL["reglas"], "ACCEPT") == "ACCEPT"),
        ("politica ACCEPT deja pasar udp/53 sin regla",
         evaluar("udp", 53, CONTROL["reglas"], "ACCEPT") == "ACCEPT"),
        ("politica CONTROL DROP bloquea paquetes sin coincidencia",
         evaluar("tcp", 23) == "DROP" and evaluar("udp", 53) == "DROP"),
        ("perfil DeliFIIS permite tcp/22 y tcp/443",
         evaluar("tcp", 22, REGLAS_DELIFIIS, POLITICA_DELIFIIS) == "ACCEPT"
         and evaluar("tcp", 443, REGLAS_DELIFIIS, POLITICA_DELIFIIS) == "ACCEPT"),
        ("perfil DeliFIIS bloquea tcp/80, tcp/3306 y tcp/8080",
         all(evaluar("tcp", puerto, REGLAS_DELIFIIS, POLITICA_DELIFIIS) == "DROP"
             for puerto in (80, 3306, 8080))),
        ("P1-P4 generan cuatro paquetes logicos tcp/443",
         len(paquetes) == 4 and paquetes == [("tcp", 443)] * 4),
        ("los cuatro pedidos oficiales son aceptados por DeliFIIS",
         decisiones_pedidos == ["ACCEPT"] * 4),
        ("se generan ocho comandos iptables para la cadena COCINA",
         len(comandos) == 8),
        ("iptables crea COCINA, permite loopback y conexiones establecidas",
         comandos[:3] == [
             "iptables -N COCINA",
             "iptables -A COCINA -i lo -j ACCEPT",
             ("iptables -A COCINA -m conntrack --ctstate "
              "ESTABLISHED,RELATED -j ACCEPT"),
         ]),
        ("iptables conserva el orden de las cuatro reglas CONTROL",
         ["--dport %d -j %s" % (puerto, accion)
          for _proto, puerto, accion in CONTROL["reglas"]]
         == [" ".join(comando.split()[-4:]) for comando in comandos[3:7]]),
        ("iptables termina en DROP sin conectar la cadena a INPUT",
         comandos[-1] == "iptables -A COCINA -j DROP"
         and all(" INPUT" not in comando and "-I " not in comando for comando in comandos)),
        ("DMA didactico: 38 us por paquete y 152 us para cuatro",
         por_paquete == 38 and total_dma == 152),
    ]


def _imprimir_tabla(titulo, reglas, politica, paquetes):
    print("\n" + titulo)
    print("%-8s %-8s %-8s" % ("Proto", "Puerto", "Decision"))
    for proto, puerto in paquetes:
        print("%-8s %-8d %-8s" %
              (proto, puerto, evaluar(proto, puerto, reglas, politica)))


def main():
    print("=== FIREWALL EDUCATIVO - DeliFIIS ===")
    _imprimir_tabla(
        "--- Valores de CONTROL ---",
        CONTROL["reglas"], CONTROL["politica"], list(CONTROL["paquetes"]),
    )
    _imprimir_tabla(
        "--- Perfil PROPIO DeliFIIS ---",
        REGLAS_DELIFIIS, POLITICA_DELIFIIS,
        [("tcp", puerto) for puerto in (22, 443, 80, 3306, 8080)],
    )

    paquetes = paquetes_desde_pedidos(CONJUNTO_OFICIAL)
    por_paquete, total = costo_dma_paquetes(len(paquetes))
    print("\nPedidos oficiales: %d paquetes tcp/443 aceptados" % len(paquetes))
    print("Costo DMA simulado: %s us por paquete, %s us total (no es tiempo real)" %
          (por_paquete, total))

    print("\n--- Comandos para prueba MANUAL en Linux/WSL/VM ---")
    print("No se ejecutan y la cadena COCINA no se conecta a INPUT.")
    for comando in comandos_iptables(CONTROL["reglas"], "COCINA"):
        print(comando)

    print("\n=== VERIFICACION ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())

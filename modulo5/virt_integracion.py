"""Modulo 5 (semana 12) - Integracion de virtualizacion.
Caso: DeliFIIS. Rol 4: plan de despliegue, memoria, aislamiento y seguridad.

La integracion consume las interfaces de los otros roles mediante ganchos. Los
comandos Docker solo se generan como texto: este archivo nunca ejecuta Docker,
sudo, VirtualBox ni comandos de administracion del sistema.
"""

from __future__ import annotations

import importlib
import os
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)

from virt_comun import imprimir_verificaciones  # noqa: E402


GANCHOS = {
    "servicios": ("virt_comun", "servicios_delifiis"),
    "capacidad": ("virt_capacidad", "capacidad_propia"),
    "recomendar": ("virt_hipervisores", "recomendar"),
    "simular_lru": ("reemplazo_lru", "simular"),
    "evaluar_firewall": ("sec_firewall", "evaluar"),
    "motivo_aislamiento": ("virt_aislamiento", "motivo_omision"),
    "ejecutar_aislamiento": ("virt_aislamiento", "ejecutar_aislamiento"),
    "validar_registros": ("virt_aislamiento", "validar_registros"),
    "motivo_jaula": ("virt_jaula", "motivo_omision"),
    "abrir_en_jaula": ("virt_jaula", "abrir_en_jaula"),
    "fichas_esperadas": ("virt_jaula", "TABLA_FICHAS_ESPERADAS"),
}

ESTADOS = {"OK", "PENDIENTE", "OMITIDO", "INCONSISTENTE", "ERROR"}
_PRIORIDAD_ESTADO = {"OK": 0, "OMITIDO": 1, "PENDIENTE": 2,
                     "INCONSISTENTE": 3, "ERROR": 4}
_ERRORES = {}

# Politica PROPIA de integracion: reservar 25 % de margen sobre la memoria de
# aplicacion calculada por virt_comun. No son cuotas hardcodeadas por pedido.
MARGEN_CUOTA_NUM = 5
MARGEN_CUOTA_DEN = 4


def cargar_ganchos(hooks=None):
    """Carga dependencias tolerantes; hooks parciales tienen prioridad."""
    ganchos = {}
    for nombre, (modulo, atributo) in GANCHOS.items():
        if hooks is not None and nombre in hooks:
            ganchos[nombre] = hooks[nombre]
            continue
        try:
            ganchos[nombre] = getattr(importlib.import_module(modulo), atributo)
        except ModuleNotFoundError as error:
            if error.name != modulo:
                _ERRORES[nombre] = "%s.%s: %s" % (modulo, atributo, error)
            ganchos[nombre] = None
        except Exception as error:
            _ERRORES[nombre] = "%s.%s: %s" % (modulo, atributo, error)
            ganchos[nombre] = None
    return ganchos


def _combinar_estado(actual, nuevo):
    if nuevo not in ESTADOS:
        raise ValueError("Estado desconocido: %s" % nuevo)
    return nuevo if _PRIORIDAD_ESTADO[nuevo] > _PRIORIDAD_ESTADO[actual] else actual


def _cuota_mb(memoria_app_mb):
    if not isinstance(memoria_app_mb, int) or isinstance(memoria_app_mb, bool) or memoria_app_mb <= 0:
        raise ValueError("La memoria de aplicacion debe ser un entero positivo")
    return (memoria_app_mb * MARGEN_CUOTA_NUM + MARGEN_CUOTA_DEN - 1) // MARGEN_CUOTA_DEN


def _comando_docker(pid, cuota_mb):
    """Genera texto reproducible; no llama a subprocess ni a Docker."""
    nombre = "delifiis-%s" % pid.lower()
    imagen = "delifiis/pedido:%s" % pid.lower()
    return "docker run -d --name %s --memory %dm --cpus 1 %s" % (
        nombre, cuota_mb, imagen
    )


def _paso(pasos, nombre, estado, detalle):
    if estado not in ESTADOS:
        raise ValueError("Estado desconocido: %s" % estado)
    pasos.append((nombre, estado, detalle))


def planificar_despliegue(hooks=None):
    """Devuelve (filas, pasos) sin ejecutar despliegues ni comandos privilegiados."""
    g = cargar_ganchos(hooks)
    filas = []
    pasos = []

    # 1. Servicios oficiales P1-P4.
    servicios = {}
    if g["servicios"] is None:
        _paso(pasos, "servicios", "PENDIENTE", "falta virt_comun.servicios_delifiis")
    else:
        try:
            servicios = g["servicios"]()
            estado = "OK" if servicios else "INCONSISTENTE"
            _paso(pasos, "servicios", estado, "%d servicios disponibles" % len(servicios))
        except Exception as error:
            _paso(pasos, "servicios", "ERROR", str(error))

    # 2. Plan individual: tipo, cuota, marcos, LRU y comando Docker textual.
    for pid, datos in servicios.items():
        estado = "OK"
        detalles = []
        fila = {
            "pedido": pid,
            "descripcion": datos.get("descripcion", ""),
            "tipo": None,
            "cuota_mb": None,
            "marcos": None,
            "fallos_lru": None,
            "oom_sin_swap": None,
            "comando_docker": None,
        }

        try:
            fila["cuota_mb"] = _cuota_mb(datos["mb"])
            marcos = datos["tamano"]
            if not isinstance(marcos, int) or isinstance(marcos, bool) or marcos <= 0:
                raise ValueError("tamano/marcos invalido para %s" % pid)
            fila["marcos"] = marcos
        except Exception as error:
            estado = "ERROR"
            detalles.append("datos: %s" % error)

        if g["recomendar"] is None:
            estado = _combinar_estado(estado, "PENDIENTE")
            detalles.append("falta virt_hipervisores.recomendar")
        else:
            try:
                tipo, razones = g["recomendar"]({"escalado_rapido": True})
                fila["tipo"] = tipo
                detalles.append("%s: %s" % (tipo, razones[0] if razones else "sin detalle"))
                if tipo != "contenedor":
                    estado = _combinar_estado(estado, "INCONSISTENTE")
            except Exception as error:
                estado = _combinar_estado(estado, "ERROR")
                detalles.append("recomendacion: %s" % error)

        if fila["marcos"] is not None:
            referencias = list(range(1, fila["marcos"] + 1))
            if g["simular_lru"] is None:
                estado = _combinar_estado(estado, "PENDIENTE")
                detalles.append("falta reemplazo_lru.simular")
            else:
                try:
                    fallos, _traza = g["simular_lru"](referencias, fila["marcos"])
                    # Un fallo de pagina o un reemplazo LRU no es OOM. La
                    # interfaz real no informa OOM: solo una MemoryError
                    # explicita de la dependencia representa esa condicion.
                    if (not isinstance(fallos, int) or isinstance(fallos, bool)
                            or fallos < 0 or fallos > len(referencias)):
                        estado = _combinar_estado(estado, "INCONSISTENTE")
                        detalles.append("LRU devolvio una cantidad de fallos invalida")
                    else:
                        fila["fallos_lru"] = fallos
                        fila["oom_sin_swap"] = False
                        detalles.append("LRU=%d fallos" % fallos)
                except MemoryError as error:
                    fila["oom_sin_swap"] = True
                    estado = _combinar_estado(estado, "INCONSISTENTE")
                    detalles.append("OOM sin swap informado: %s" % error)
                except Exception as error:
                    estado = _combinar_estado(estado, "ERROR")
                    detalles.append("LRU: %s" % error)

        if fila["tipo"] == "contenedor" and fila["cuota_mb"] is not None:
            fila["comando_docker"] = _comando_docker(pid, fila["cuota_mb"])
        fila["estado"] = estado
        filas.append(fila)
        _paso(pasos, "pedido %s" % pid, estado, "; ".join(detalles) or "sin detalle")

    # 3. Capacidad global.
    asignada = sum(f["cuota_mb"] or 0 for f in filas)
    if g["capacidad"] is None:
        _paso(pasos, "capacidad", "PENDIENTE", "falta virt_capacidad.capacidad_propia")
    else:
        try:
            capacidad = g["capacidad"]()
            disponible = capacidad["disponible"]
            estado = "OK" if asignada <= disponible else "INCONSISTENTE"
            _paso(pasos, "capacidad", estado,
                   "asignada=%d MB disponible=%d MB" % (asignada, disponible))
        except Exception as error:
            _paso(pasos, "capacidad", "ERROR", str(error))

    # 4. Politica de firewall de Semana 11.
    if g["evaluar_firewall"] is None:
        _paso(pasos, "firewall", "PENDIENTE", "falta sec_firewall.evaluar")
    else:
        try:
            d443 = g["evaluar_firewall"]("tcp", 443)
            d3306 = g["evaluar_firewall"]("tcp", 3306)
            estado = "OK" if (d443, d3306) == ("ACCEPT", "DROP") else "INCONSISTENTE"
            _paso(pasos, "firewall", estado, "tcp/443=%s tcp/3306=%s" % (d443, d3306))
        except Exception as error:
            _paso(pasos, "firewall", "ERROR", str(error))

    ids = [fila["pedido"] for fila in filas]

    # 5. Namespaces: se ejecuta solo si el propio modulo confirma disponibilidad.
    necesarios_aislamiento = ("motivo_aislamiento", "ejecutar_aislamiento", "validar_registros")
    if any(g[n] is None for n in necesarios_aislamiento):
        _paso(pasos, "aislamiento", "PENDIENTE", "faltan ganchos de virt_aislamiento")
    else:
        try:
            motivo = g["motivo_aislamiento"]()
            if motivo:
                _paso(pasos, "aislamiento", "OMITIDO", motivo)
            else:
                registros = g["ejecutar_aislamiento"](ids)
                if registros is None:
                    _paso(pasos, "aislamiento", "INCONSISTENTE", "sin registros")
                else:
                    errores = g["validar_registros"](registros, ids)
                    estado = "OK" if not errores else "INCONSISTENTE"
                    _paso(pasos, "aislamiento", estado,
                           "namespaces validos" if not errores else "; ".join(errores))
        except Exception as error:
            _paso(pasos, "aislamiento", "ERROR", str(error))

    # 6. Jaula chroot: no se invoca si falta Linux, root o herramienta.
    necesarios_jaula = ("motivo_jaula", "abrir_en_jaula", "fichas_esperadas")
    if any(g[n] is None for n in necesarios_jaula):
        _paso(pasos, "jaula", "PENDIENTE", "faltan ganchos de virt_jaula")
    else:
        try:
            motivo = g["motivo_jaula"]()
            if motivo:
                _paso(pasos, "jaula", "OMITIDO", motivo)
            else:
                resultados = [g["abrir_en_jaula"](ruta) for ruta in g["fichas_esperadas"]]
                correcto = bool(resultados) and all(
                    info is not None and info.get("huella_coincide") is True
                    for info in resultados
                )
                _paso(pasos, "jaula", "OK" if correcto else "INCONSISTENTE",
                       "huellas intactas" if correcto else "fallo de integridad")
        except Exception as error:
            _paso(pasos, "jaula", "ERROR", str(error))

    return filas, pasos


def ganchos_de_prueba():
    """Dependencias deterministas con los valores esperados del proyecto."""
    servicios = {
        "P1": {"descripcion": "Lomo Saltado", "tamano": 2, "mb": 512},
        "P2": {"descripcion": "Ceviche Clasico", "tamano": 2, "mb": 512},
        "P3": {"descripcion": "Anticuchos", "tamano": 3, "mb": 768},
        "P4": {"descripcion": "Causa Limena", "tamano": 3, "mb": 768},
    }
    rutas = {
        "/cocina/recetas/fichas/ficha_%s.txt" % pid: {}
        for pid in servicios
    }

    def simular_lru(referencias, marcos):
        if marcos <= 0:
            raise ValueError("marcos debe ser positivo")
        return len(set(referencias)), []

    def registros(ids):
        return [
            {"id": pid, "pid_anfitrion": 1000 + i,
             "pid_namespace": 1, "hostname": "delifiis-%s" % pid}
            for i, pid in enumerate(ids, 1)
        ]

    def validar(registros_obtenidos, ids):
        if [r.get("id") for r in registros_obtenidos] != ids:
            return ["ids no coinciden"]
        if any(r.get("pid_namespace") != 1 for r in registros_obtenidos):
            return ["pid namespace invalido"]
        return []

    return {
        "servicios": lambda: servicios,
        "capacidad": lambda: {"disponible": 20480},
        "recomendar": lambda req: (
            "contenedor", ["escalado rapido"]
        ) if req.get("escalado_rapido") else ("VM", ["aislamiento"]),
        "simular_lru": simular_lru,
        "evaluar_firewall": lambda proto, puerto: (
            "ACCEPT" if (proto, puerto) == ("tcp", 443) else "DROP"
        ),
        "motivo_aislamiento": lambda: None,
        "ejecutar_aislamiento": registros,
        "validar_registros": validar,
        "motivo_jaula": lambda: None,
        "abrir_en_jaula": lambda ruta: {"ruta": ruta, "huella_coincide": True},
        "fichas_esperadas": rutas,
    }


def _estado_de(pasos, nombre):
    return next((estado for paso, estado, _detalle in pasos if paso == nombre), None)


def verificar():
    fake = ganchos_de_prueba()
    filas, pasos = planificar_despliegue(fake)
    cuotas = [f["cuota_mb"] for f in filas]
    marcos = [f["marcos"] for f in filas]
    fallos = [f["fallos_lru"] for f in filas]

    sin_firewall = dict(fake)
    sin_firewall["evaluar_firewall"] = None
    _filas_p, pasos_p = planificar_despliegue(sin_firewall)

    poca_memoria = dict(fake)
    poca_memoria["capacidad"] = lambda: {"disponible": 1000}
    _filas_i, pasos_i = planificar_despliegue(poca_memoria)

    con_error = dict(fake)

    def falla(_req):
        raise RuntimeError("fallo simulado")

    con_error["recomendar"] = falla
    filas_e, pasos_e = planificar_despliegue(con_error)

    con_oom = dict(fake)

    def oom_simulado(referencias, marcos):
        if marcos == 2:
            raise MemoryError("senal OOM simulada por el gancho de prueba")
        return len(set(referencias)), []

    con_oom["simular_lru"] = oom_simulado
    filas_oom, pasos_oom = planificar_despliegue(con_oom)

    lru_invalido = dict(fake)
    lru_invalido["simular_lru"] = lambda _referencias, _marcos: (-1, [])
    filas_lru_invalido, _pasos_lru_invalido = planificar_despliegue(lru_invalido)

    return [
        ("integracion de prueba genera P1-P4",
         [f["pedido"] for f in filas] == ["P1", "P2", "P3", "P4"]),
        ("cuotas esperadas: 640, 640, 960, 960 MB", cuotas == [640, 640, 960, 960]),
        ("marcos esperados: 2, 2, 3, 3", marcos == [2, 2, 3, 3]),
        ("fallos LRU esperados: 2, 2, 3, 3", fallos == [2, 2, 3, 3]),
        ("memoria asignada total = 3200 MB", sum(cuotas) == 3200),
        ("marcos totales = 10", sum(marcos) == 10),
        ("fallos LRU totales = 10", sum(fallos) == 10),
        ("los cuatro servicios usan contenedores",
         all(f["tipo"] == "contenedor" for f in filas)),
        ("se generan cuatro comandos Docker como texto",
         all(isinstance(f["comando_docker"], str)
             and f["comando_docker"].startswith("docker run ") for f in filas)),
        ("ningun servicio termina por falta de memoria sin swap",
         all(f["oom_sin_swap"] is False for f in filas)),
        ("capacidad: 3200 MB no exceden 20480 MB",
         _estado_de(pasos, "capacidad") == "OK"),
        ("firewall de prueba acepta 443 y bloquea 3306",
         _estado_de(pasos, "firewall") == "OK"),
        ("aislamiento y jaula simulados quedan OK",
         _estado_de(pasos, "aislamiento") == "OK"
         and _estado_de(pasos, "jaula") == "OK"),
        ("integracion completa de prueba no tiene estados anormales",
         all(estado == "OK" for _paso, estado, _detalle in pasos)),
        ("un gancho ausente produce PENDIENTE",
         _estado_de(pasos_p, "firewall") == "PENDIENTE"),
        ("capacidad de 1000 MB produce INCONSISTENTE",
         _estado_de(pasos_i, "capacidad") == "INCONSISTENTE"),
        ("una excepcion de dependencia produce ERROR sin bloquear",
         any(estado == "ERROR" for _paso, estado, _detalle in pasos_e)
         and len(filas_e) == 4
         and _estado_de(pasos_e, "capacidad") == "OK"),
        ("una senal OOM simulada se detecta sin confundirla con reemplazo LRU",
         [f["oom_sin_swap"] for f in filas_oom] == [True, True, False, False]
         and all(f["estado"] == "INCONSISTENTE" for f in filas_oom[:2])
         and _estado_de(pasos_oom, "capacidad") == "OK"),
        ("un resultado LRU invalido se marca INCONSISTENTE",
         all(f["estado"] == "INCONSISTENTE" for f in filas_lru_invalido)
         and all(f["fallos_lru"] is None for f in filas_lru_invalido)
         and all(f["oom_sin_swap"] is None for f in filas_lru_invalido)),
    ]


def main():
    print("=== INTEGRACION DE VIRTUALIZACION - DeliFIIS ===")
    filas, pasos = planificar_despliegue()

    print("\n--- Plan por pedido ---")
    print("%-4s %-11s %9s %7s %10s %-14s" %
          ("ID", "Tipo", "Cuota MB", "Marcos", "Fallos LRU", "Estado"))
    for fila in filas:
        print("%-4s %-11s %9s %7s %10s %-14s" % (
            fila["pedido"],
            fila["tipo"] or "-",
            fila["cuota_mb"] or "-",
            fila["marcos"] or "-",
            fila["fallos_lru"] if fila["fallos_lru"] is not None else "-",
            fila["estado"],
        ))
        if fila["comando_docker"]:
            print("     Docker (NO EJECUTADO): %s" % fila["comando_docker"])

    print("\n--- Comprobaciones globales ---")
    for nombre, estado, detalle in pasos:
        print("%-18s %-14s %s" % (nombre, estado, detalle))

    print("\n=== VERIFICACION ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())

"""Simulador de planificacion de procesos - Modulo 1: Torre de Control
Caso: CocinaPeru Express

Permite planificar pedidos mediante cuatro algoritmos:
- FCFS (First-Come, First-Served)
- SJF no expropiativo (Shortest Job First)
- Round Robin con quantum configurable
- Prioridad no expropiativa (menor numero = mayor prioridad)

Admite entrada de datos desde:
1. Archivo 'pedidos.json' (generado por el programa en C)
2. Conjunto oficial de referencia P1-P4 (con verificacion automatica de los 5 valores)
3. Conjunto alternativo propuesto por el equipo
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import deque
from dataclasses import dataclass
from typing import Callable, Sequence


@dataclass(frozen=True)
class Proceso:
    """Pedido/proceso que interactua con el planificador."""

    id: str
    llegada: int
    duracion: int
    prioridad: int
    pid: int | None = None
    descripcion: str = ""


@dataclass(frozen=True)
class Metrica:
    """Metricas de ejecucion y rendimiento por proceso."""

    inicio: int
    fin: int
    espera: int
    respuesta: int
    retorno: int


Tramo = tuple[str, int, int]
Resultado = tuple[list[Tramo], dict[str, Metrica]]

# Conjunto oficial de referencia de la practica (P1 a P4)
CONJUNTO_OFICIAL: tuple[Proceso, ...] = (
    Proceso("P1", llegada=0, duracion=5, prioridad=3, pid=1001, descripcion="Lomo Saltado"),
    Proceso("P2", llegada=1, duracion=3, prioridad=4, pid=1002, descripcion="Ceviche Clasico"),
    Proceso("P3", llegada=2, duracion=8, prioridad=1, pid=1003, descripcion="Anticuchos"),
    Proceso("P4", llegada=3, duracion=6, prioridad=2, pid=1004, descripcion="Causa Limena"),
)

# Segundo conjunto propuesto por el equipo
CONJUNTO_EQUIPO: tuple[Proceso, ...] = (
    Proceso("Q1", llegada=0, duracion=4, prioridad=2, pid=2001, descripcion="Arroz con Pollo"),
    Proceso("Q2", llegada=1, duracion=7, prioridad=4, pid=2002, descripcion="Aji de Gallina"),
    Proceso("Q3", llegada=2, duracion=2, prioridad=1, pid=2003, descripcion="Papa Rellena"),
    Proceso("Q4", llegada=4, duracion=5, prioridad=3, pid=2004, descripcion="Seco de Res"),
    Proceso("Q5", llegada=6, duracion=3, prioridad=2, pid=2005, descripcion="Tacu Tacu"),
)


def cargar_pedidos_json(ruta: str) -> list[Proceso]:
    """Carga los pedidos generados por el programa en C desde un archivo JSON."""
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"No se encontro el archivo de pedidos en: {ruta}")

    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)

    if not isinstance(datos, list):
        raise ValueError("El JSON debe contener un arreglo de objetos de pedidos.")

    procesos: list[Proceso] = []
    for item in datos:
        p = Proceso(
            id=str(item["id"]),
            llegada=int(item["llegada"]),
            duracion=int(item["duracion"]),
            prioridad=int(item["prioridad"]),
            pid=int(item["pid"]) if "pid" in item else None,
            descripcion=str(item.get("descripcion", "")),
        )
        procesos.append(p)

    validar_procesos(procesos)
    return procesos


def validar_procesos(procesos: Sequence[Proceso]) -> None:
    """Verifica precondiciones para garantizar consistencia en la planificacion."""
    if not procesos:
        raise ValueError("Se requiere al menos un proceso para planificar.")

    ids: set[str] = set()
    for p in procesos:
        if not p.id or p.id in ids:
            raise ValueError(f"ID vacio o duplicado: {p.id!r}")
        if p.llegada < 0:
            raise ValueError(f"El tiempo de llegada de {p.id} no puede ser negativo.")
        if p.duracion <= 0:
            raise ValueError(f"La duracion de {p.id} debe ser mayor que cero.")
        ids.add(p.id)


def metricas_no_expropiativo(proceso: Proceso, inicio: int, fin: int) -> Metrica:
    """Calcula las metricas para politicas no expropiativas."""
    espera = inicio - proceso.llegada
    return Metrica(
        inicio=inicio,
        fin=fin,
        espera=espera,
        respuesta=espera,
        retorno=fin - proceso.llegada,
    )


def fcfs(procesos: Sequence[Proceso]) -> Resultado:
    """First-Come, First-Served: ordena estrictamente por tiempo de llegada."""
    validar_procesos(procesos)
    tiempo, gantt, metricas = 0, [], {}

    for proceso in sorted(procesos, key=lambda p: (p.llegada, p.id)):
        if tiempo < proceso.llegada:
            gantt.append(("IDLE", tiempo, proceso.llegada))
            tiempo = proceso.llegada
        inicio = tiempo
        tiempo += proceso.duracion
        gantt.append((proceso.id, inicio, tiempo))
        metricas[proceso.id] = metricas_no_expropiativo(proceso, inicio, tiempo)

    return gantt, metricas


def _no_expropiativo(
    procesos: Sequence[Proceso],
    criterio: Callable[[Proceso], tuple],
) -> Resultado:
    """Motor comun para SJF y Prioridad no expropiativos."""
    validar_procesos(procesos)
    pendientes = list(procesos)
    tiempo, gantt, metricas = 0, [], {}

    while pendientes:
        listos = [p for p in pendientes if p.llegada <= tiempo]
        if not listos:
            siguiente = min(p.llegada for p in pendientes)
            gantt.append(("IDLE", tiempo, siguiente))
            tiempo = siguiente
            continue

        proceso = min(listos, key=criterio)
        inicio = tiempo
        tiempo += proceso.duracion
        gantt.append((proceso.id, inicio, tiempo))
        metricas[proceso.id] = metricas_no_expropiativo(proceso, inicio, tiempo)
        pendientes.remove(proceso)

    return gantt, metricas


def sjf_no_expropiativo(procesos: Sequence[Proceso]) -> Resultado:
    """Shortest Job First: selecciona el proceso con menor duracion de rafaga."""
    return _no_expropiativo(procesos, lambda p: (p.duracion, p.llegada, p.id))


def prioridad_no_expropiativa(procesos: Sequence[Proceso]) -> Resultado:
    """Prioridad: menor valor numerico indica mayor prioridad."""
    return _no_expropiativo(procesos, lambda p: (p.prioridad, p.llegada, p.id))


def round_robin(procesos: Sequence[Proceso], quantum: int = 4) -> Resultado:
    """Round Robin con cola FIFO y quantum configurable."""
    validar_procesos(procesos)
    if quantum <= 0:
        raise ValueError("El quantum debe ser mayor que cero.")

    restantes = {p.id: p.duracion for p in procesos}
    pendientes = sorted(procesos, key=lambda p: (p.llegada, p.id))
    cola: deque[str] = deque()
    primer_inicio: dict[str, int] = {}
    finales: dict[str, int] = {}
    gantt: list[Tramo] = []
    tiempo = 0
    indice = 0

    def encolar_llegadas(hasta: int) -> None:
        nonlocal indice
        while indice < len(pendientes) and pendientes[indice].llegada <= hasta:
            cola.append(pendientes[indice].id)
            indice += 1

    while cola or indice < len(pendientes):
        if not cola:
            siguiente = pendientes[indice].llegada
            if tiempo < siguiente:
                gantt.append(("IDLE", tiempo, siguiente))
                tiempo = siguiente
            encolar_llegadas(tiempo)
            continue

        pid = cola.popleft()
        inicio = tiempo
        primer_inicio.setdefault(pid, inicio)
        ejecucion = min(quantum, restantes[pid])
        tiempo += ejecucion
        restantes[pid] -= ejecucion
        gantt.append((pid, inicio, tiempo))

        # Llegadas ocurridas durante el quantum entran antes de reenviar el actual a la cola
        encolar_llegadas(tiempo)
        if restantes[pid] > 0:
            cola.append(pid)
        else:
            finales[pid] = tiempo

    metricas = {}
    for p in procesos:
        retorno = finales[p.id] - p.llegada
        metricas[p.id] = Metrica(
            inicio=primer_inicio[p.id],
            fin=finales[p.id],
            espera=retorno - p.duracion,
            respuesta=primer_inicio[p.id] - p.llegada,
            retorno=retorno,
        )
    return gantt, metricas


def promedio(metricas: dict[str, Metrica], atributo: str) -> float:
    return sum(getattr(m, atributo) for m in metricas.values()) / len(metricas)


def imprimir_procesos(procesos: Sequence[Proceso]) -> None:
    print("\nLista de Pedidos:")
    print(f"{'ID':<6}{'PID':>8}{'Llegada':>9}{'Duracion':>10}{'Prioridad':>11}  {'Descripcion':<20}")
    print("-" * 70)
    for p in procesos:
        pid_str = str(p.pid) if p.pid is not None else "-"
        print(f"{p.id:<6}{pid_str:>8}{p.llegada:>9}{p.duracion:>10}{p.prioridad:>11}  {p.descripcion:<20}")


def imprimir_resultado(nombre: str, resultado: Resultado) -> None:
    gantt, metricas = resultado
    secuencia = " -> ".join(pid for pid, _, _ in gantt if pid != "IDLE")
    print("\n" + "=" * 76)
    print(f"POLITICA: {nombre}")
    print("=" * 76)
    print(f"Orden de atencion : {secuencia}")
    print("Gantt textual     : " + " | ".join(f"{pid}[{ini}-{fin}]" for pid, ini, fin in gantt))
    print(f"\n{'ID':<6}{'Inicio':>8}{'Fin':>7}{'Espera':>9}{'Respuesta':>12}{'Retorno':>10}")
    print("-" * 55)
    for pid in sorted(metricas):
        m = metricas[pid]
        print(f"{pid:<6}{m.inicio:>8}{m.fin:>7}{m.espera:>9.2f}{m.respuesta:>12.2f}{m.retorno:>10.2f}")
    print("-" * 55)
    print(
        f"PROMEDIO{'':<6}{promedio(metricas, 'espera'):>9.2f}"
        f"{promedio(metricas, 'respuesta'):>12.2f}{promedio(metricas, 'retorno'):>10.2f}"
    )


def ejecutar_algoritmos(procesos: Sequence[Proceso], quantum: int) -> dict[str, Resultado]:
    resultados = {
        "FCFS": fcfs(procesos),
        "SJF no expropiativo": sjf_no_expropiativo(procesos),
        f"Round Robin (q={quantum})": round_robin(procesos, quantum),
        "Prioridad no expropiativa": prioridad_no_expropiativa(procesos),
    }
    for nombre, res in resultados.items():
        imprimir_resultado(nombre, res)
    return resultados


def imprimir_tabla_comparativa(resultados: dict[str, Resultado]) -> None:
    print("\n" + "=" * 80)
    print("TABLA COMPARATIVA DE RENDIMIENTO")
    print("=" * 80)
    print(f"{'Algoritmo':<30}{'Espera prom.':>14}{'Respuesta prom.':>18}{'Retorno prom.':>16}")
    print("-" * 80)
    for nombre, (_, metricas) in resultados.items():
        print(
            f"{nombre:<30}{promedio(metricas, 'espera'):>14.2f}"
            f"{promedio(metricas, 'respuesta'):>18.2f}{promedio(metricas, 'retorno'):>16.2f}"
        )


def imprimir_recomendacion(resultados: dict[str, Resultado]) -> None:
    menor_espera = min(resultados, key=lambda n: promedio(resultados[n][1], "espera"))
    menor_respuesta = min(resultados, key=lambda n: promedio(resultados[n][1], "respuesta"))
    print("\n" + "=" * 80)
    print("RECOMENDACION OPERATIVA PARA COCINAPERU EXPRESS:")
    print("=" * 80)
    print(f"- Para MINIMIZAR LA ESPERA TOTAL: Usar '{menor_espera}' "
          f"(Espera prom: {promedio(resultados[menor_espera][1], 'espera'):.2f}s).")
    print(f"- Para ATENCION INICIAL RAPIDA:   Usar '{menor_respuesta}' "
          f"(Respuesta prom: {promedio(resultados[menor_respuesta][1], 'respuesta'):.2f}s).")


def verificar_conjunto_oficial() -> None:
    """Verificacion automatica contra los 5 valores oficiales de referencia de la guia."""
    resultados = {
        "FCFS": fcfs(CONJUNTO_OFICIAL),
        "SJF": sjf_no_expropiativo(CONJUNTO_OFICIAL),
        "RR": round_robin(CONJUNTO_OFICIAL, quantum=4),
        "Prioridad": prioridad_no_expropiativa(CONJUNTO_OFICIAL),
    }
    verificaciones = (
        ("1. FCFS, espera promedio", promedio(resultados["FCFS"][1], "espera"), 5.75),
        ("2. SJF, espera promedio", promedio(resultados["SJF"][1], "espera"), 5.25),
        ("3. Round Robin (q=4), espera promedio", promedio(resultados["RR"][1], "espera"), 9.25),
        ("4. Round Robin (q=4), respuesta promedio", promedio(resultados["RR"][1], "respuesta"), 4.00),
        ("5. Prioridad, espera promedio", promedio(resultados["Prioridad"][1], "espera"), 7.75),
    )
    print("\n" + "#" * 80)
    print("VERIFICACION AUTOMATICA DE LOS 5 VALORES DE REFERENCIA (P1-P4)")
    print("#" * 80)
    todos_ok = True
    for etiqueta, obtenido, esperado in verificaciones:
        cumple = abs(obtenido - esperado) < 1e-4
        estado = "OK [CORRECTO]" if cumple else "FALLO"
        print(f"[{estado}] {etiqueta:<42}: Obtenido = {obtenido:.2f} | Esperado = {esperado:.2f}")
        if not cumple:
            todos_ok = False

    if todos_ok:
        print("\n=> EXITO: Todos los valores de referencia cuadran al 100%.")
    else:
        print("\n=> ADVERTENCIA: Hubo diferencias en los valores de referencia.")


def ejecutar_caso(nombre: str, procesos: Sequence[Proceso], quantum: int) -> dict[str, Resultado]:
    print("\n\n" + "#" * 80)
    print(nombre)
    print("#" * 80)
    imprimir_procesos(procesos)
    resultados = ejecutar_algoritmos(procesos, quantum)
    imprimir_tabla_comparativa(resultados)
    imprimir_recomendacion(resultados)
    return resultados


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulador de Planificacion de Procesos - CocinaPeru Express (SW407)"
    )
    parser.add_argument(
        "--archivo",
        type=str,
        default=None,
        help="Ruta al archivo pedidos.json generado por mostrador.c",
    )
    parser.add_argument(
        "--quantum",
        type=int,
        default=4,
        help="Quantum para el algoritmo Round Robin (por defecto: 4)",
    )
    parser.add_argument(
        "--verificar",
        action="store_true",
        help="Ejecuta unicamente la verificacion de los 5 valores de referencia",
    )
    argumentos = parser.parse_args()

    if argumentos.quantum <= 0:
        parser.error("--quantum debe ser un entero mayor que cero.")

    if argumentos.verificar:
        verificar_conjunto_oficial()
        return

    # Verificar siempre de antemano el conjunto oficial
    verificar_conjunto_oficial()

    # Si se especifica un archivo JSON o si existe pedidos.json por defecto
    ruta_json = argumentos.archivo
    if ruta_json is None and os.path.exists("pedidos.json"):
        ruta_json = "pedidos.json"

    if ruta_json and os.path.exists(ruta_json):
        print(f"\n[INFO] Cargando pedidos desde archivo externo: {ruta_json}")
        pedidos_cargados = cargar_pedidos_json(ruta_json)
        ejecutar_caso(f"CORRIDA CON DATOS REALES ({ruta_json})", pedidos_cargados, argumentos.quantum)
    else:
        # Corrida con los dos conjuntos integrados de la practica
        ejecutar_caso("CASO 1: CONJUNTO DE REFERENCIA OFICIAL (P1-P4)", CONJUNTO_OFICIAL, argumentos.quantum)
        ejecutar_caso("CASO 2: CONJUNTO PROPUESTO POR EL EQUIPO", CONJUNTO_EQUIPO, argumentos.quantum)


if __name__ == "__main__":
    main()

""" EL ARCHIVO pedidos.json es un json de ejemplo """
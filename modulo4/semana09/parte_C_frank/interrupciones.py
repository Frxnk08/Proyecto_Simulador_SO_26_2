"""Experimento educativo de interrupciones periodicas mediante SIGALRM."""

from __future__ import annotations

import argparse
import math
import os
import signal
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

DURACION_PREDETERMINADA = 3.25
PERIODOS_PREDETERMINADOS = (0.50, 0.25)
EJECUCIONES_PREDETERMINADAS = 3


@dataclass(frozen=True)
class ResultadoInterrupcion:
    """Mediciones obtenidas durante una ejecucion del temporizador."""

    numero: int
    periodo: float
    duracion_nominal: float
    avisos: tuple[float, ...]
    iteraciones_trabajo: int
    checksum: int
    temporizador_desactivado: bool


def validar_parametros(periodo: float, duracion: float, ejecuciones: int) -> None:
    """Valida los parametros temporales del experimento."""
    if not math.isfinite(periodo) or periodo <= 0:
        raise ValueError("El periodo debe ser un numero positivo y finito.")
    if not math.isfinite(duracion) or duracion <= 0:
        raise ValueError("La duracion debe ser un numero positivo y finito.")
    if ejecuciones <= 0:
        raise ValueError("La cantidad de ejecuciones debe ser mayor que cero.")


def verificar_compatibilidad_posix() -> None:
    """Comprueba que la plataforma ofrezca las primitivas POSIX necesarias."""
    requeridos = ("SIGALRM", "ITIMER_REAL", "setitimer", "getitimer")
    faltantes = [nombre for nombre in requeridos if not hasattr(signal, nombre)]
    if os.name != "posix" or faltantes:
        detalle = ", ".join(faltantes) if faltantes else "entorno no POSIX"
        raise OSError(
            "SIGALRM requiere Linux u otro entorno POSIX compatible "
            f"({detalle}). No se generaron mediciones simuladas."
        )


def prediccion_nominal(periodo: float, duracion: float) -> tuple[float, ...]:
    """Calcula los instantes teoricos programados dentro del intervalo nominal."""
    cantidad = math.floor((duracion / periodo) + 1e-12)
    return tuple(periodo * indice for indice in range(1, cantidad + 1))


def ejecutar_experimento(
    periodo: float,
    duracion: float = DURACION_PREDETERMINADA,
    numero: int = 1,
) -> ResultadoInterrupcion:
    """Ejecuta trabajo util mientras SIGALRM entrega avisos periodicos."""
    validar_parametros(periodo, duracion, 1)
    verificar_compatibilidad_posix()
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("Los manejadores de senales deben instalarse en el hilo principal.")

    avisos: list[float] = []
    inicio = 0.0

    def manejar_alarma(_numero_senal: int, _marco: object) -> None:
        avisos.append(time.perf_counter() - inicio)

    manejador_anterior = signal.getsignal(signal.SIGALRM)
    iteraciones = 0
    checksum = 0
    temporizador_desactivado = False
    inicio = time.perf_counter()

    try:
        signal.signal(signal.SIGALRM, manejar_alarma)
        signal.setitimer(signal.ITIMER_REAL, periodo, periodo)
        while time.perf_counter() - inicio < duracion:
            checksum = (checksum * 1_664_525 + 1_013_904_223) & 0xFFFFFFFF
            iteraciones += 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0, 0.0)
        restante, intervalo = signal.getitimer(signal.ITIMER_REAL)
        temporizador_desactivado = restante == 0.0 and intervalo == 0.0
        signal.signal(signal.SIGALRM, manejador_anterior)

    return ResultadoInterrupcion(
        numero=numero,
        periodo=periodo,
        duracion_nominal=duracion,
        avisos=tuple(avisos),
        iteraciones_trabajo=iteraciones,
        checksum=checksum,
        temporizador_desactivado=temporizador_desactivado,
    )


def formatear_resultados(resultados: Sequence[ResultadoInterrupcion]) -> str:
    """Genera una salida textual legible y separada por ejecucion."""
    lineas = [
        "SO-Sim / DeliFIIS - Parte C: interrupciones SIGALRM",
        "El contador de trabajo no equivale a un porcentaje de uso de CPU.",
    ]
    for resultado in resultados:
        instantes = ", ".join(f"{instante:.6f}" for instante in resultado.avisos)
        lineas.extend(
            (
                "",
                f"Periodo {resultado.periodo:.2f} s - ejecucion {resultado.numero}",
                f"Duracion nominal: {resultado.duracion_nominal:.2f} s",
                f"Avisos recibidos: {len(resultado.avisos)}",
                f"Instantes observados (s): [{instantes}]",
                f"Iteraciones de trabajo util: {resultado.iteraciones_trabajo}",
                f"Checksum de trabajo: {resultado.checksum}",
                "Temporizador desactivado: "
                + ("SI" if resultado.temporizador_desactivado else "NO"),
            )
        )
    return "\n".join(lineas) + "\n"


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mide avisos periodicos SIGALRM mientras se realiza trabajo util."
    )
    parser.add_argument(
        "--periodos",
        type=float,
        nargs="+",
        default=list(PERIODOS_PREDETERMINADOS),
        help="Periodos en segundos (por defecto: 0.50 0.25).",
    )
    parser.add_argument(
        "--duracion",
        type=float,
        default=DURACION_PREDETERMINADA,
        help="Duracion nominal por ejecucion (por defecto: 3.25).",
    )
    parser.add_argument(
        "--ejecuciones",
        type=int,
        default=EJECUCIONES_PREDETERMINADAS,
        help="Repeticiones por periodo (por defecto: 3).",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        help="Archivo UTF-8 opcional donde guardar la salida real.",
    )
    return parser


def main() -> None:
    parser = construir_parser()
    argumentos = parser.parse_args()
    try:
        for periodo in argumentos.periodos:
            validar_parametros(periodo, argumentos.duracion, argumentos.ejecuciones)
        verificar_compatibilidad_posix()
        resultados = [
            ejecutar_experimento(periodo, argumentos.duracion, numero)
            for periodo in argumentos.periodos
            for numero in range(1, argumentos.ejecuciones + 1)
        ]
    except (OSError, RuntimeError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n")

    texto = formatear_resultados(resultados)
    print(texto, end="")
    if argumentos.salida:
        argumentos.salida.parent.mkdir(parents=True, exist_ok=True)
        argumentos.salida.write_text(texto, encoding="utf-8")
        print(f"Evidencia guardada en: {argumentos.salida}")


if __name__ == "__main__":
    main()

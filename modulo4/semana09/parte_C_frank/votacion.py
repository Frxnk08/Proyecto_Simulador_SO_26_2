"""Version por polling que consulta continuamente el reloj durante 3,25 s."""

from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass
from pathlib import Path

DURACION_PREDETERMINADA = 3.25
PERIODO_PREDETERMINADO = 0.50


@dataclass(frozen=True)
class ResultadoVotacion:
    """Mediciones reales de una ejecucion con espera activa."""

    periodo: float
    duracion_nominal: float
    avisos: tuple[float, ...]
    consultas_reloj: int


def validar_parametros(periodo: float, duracion: float) -> None:
    """Rechaza periodos o duraciones invalidos."""
    if not math.isfinite(periodo) or periodo <= 0:
        raise ValueError("El periodo debe ser un numero positivo y finito.")
    if not math.isfinite(duracion) or duracion <= 0:
        raise ValueError("La duracion debe ser un numero positivo y finito.")


def ejecutar_votacion(
    periodo: float = PERIODO_PREDETERMINADO,
    duracion: float = DURACION_PREDETERMINADA,
) -> ResultadoVotacion:
    """Detecta vencimientos consultando el reloj en un bucle de espera activa."""
    validar_parametros(periodo, duracion)
    inicio = time.perf_counter()
    siguiente_aviso = periodo
    avisos: list[float] = []
    consultas = 0

    while True:
        transcurrido = time.perf_counter() - inicio
        consultas += 1

        while siguiente_aviso <= duracion + 1e-12 and transcurrido >= siguiente_aviso:
            avisos.append(transcurrido)
            siguiente_aviso += periodo

        if transcurrido >= duracion:
            break

    return ResultadoVotacion(
        periodo=periodo,
        duracion_nominal=duracion,
        avisos=tuple(avisos),
        consultas_reloj=consultas,
    )


def formatear_resultado(resultado: ResultadoVotacion) -> str:
    """Presenta los avisos y el costo observable de la espera activa."""
    instantes = ", ".join(f"{instante:.6f}" for instante in resultado.avisos)
    return "\n".join(
        (
            "SO-Sim / DeliFIIS - Parte C: votacion (polling)",
            "Metodo: espera activa; el programa vigila continuamente el reloj.",
            f"Periodo: {resultado.periodo:.2f} s",
            f"Duracion nominal: {resultado.duracion_nominal:.2f} s",
            f"Avisos detectados: {len(resultado.avisos)}",
            f"Instantes observados (s): [{instantes}]",
            f"Consultas al reloj: {resultado.consultas_reloj}",
            "",
        )
    )


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compara interrupciones con una espera activa basada en polling."
    )
    parser.add_argument(
        "--periodo",
        type=float,
        default=PERIODO_PREDETERMINADO,
        help="Periodo entre avisos en segundos (por defecto: 0.50).",
    )
    parser.add_argument(
        "--duracion",
        type=float,
        default=DURACION_PREDETERMINADA,
        help="Duracion total en segundos (por defecto: 3.25).",
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
        resultado = ejecutar_votacion(argumentos.periodo, argumentos.duracion)
    except ValueError as error:
        parser.error(str(error))

    texto = formatear_resultado(resultado)
    print(texto, end="")
    if argumentos.salida:
        argumentos.salida.parent.mkdir(parents=True, exist_ok=True)
        argumentos.salida.write_text(texto, encoding="utf-8")
        print(f"Evidencia guardada en: {argumentos.salida}")


if __name__ == "__main__":
    main()

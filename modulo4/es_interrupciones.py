"""Modulo 4 (semana 9) - Interrupciones y votacion. Caso: DeliFIIS.

Rol R2. Compara dos formas de detectar un aviso periodico:
- SIGALRM + setitimer: el programa sigue haciendo trabajo util entre avisos.
- votacion: el bucle consulta continuamente el reloj (espera activa).

SIGALRM solo esta disponible en Linux/macOS. En Windows el programa avisa y
continua con la version por votacion sin terminar con error.
Salida por consola sin tildes (Windows).
"""

from __future__ import annotations

import argparse
import math
import signal
import time


def soporta_sigalrm():
    return (
        hasattr(signal, 'SIGALRM')
        and hasattr(signal, 'setitimer')
        and hasattr(signal, 'ITIMER_REAL')
    )


def _validar_tiempos(periodo, duracion):
    if periodo <= 0:
        raise ValueError('periodo debe ser mayor que cero')
    if duracion <= 0:
        raise ValueError('duracion debe ser mayor que cero')


def avisos_teoricos(periodo, duracion):
    """Cantidad de avisos programados hasta duracion, incluyendo el limite exacto."""
    _validar_tiempos(periodo, duracion)
    return int(math.floor(duracion / periodo + 1e-12))


def ejecutar_interrupciones(periodo=0.5, duracion=3.25):
    """Ejecuta SIGALRM y devuelve (avisos, trabajo_util).

    Cada aviso es el instante observado desde el inicio. El contador trabajo_util
    solo mide iteraciones del bucle; no representa porcentaje de uso de CPU.
    """
    _validar_tiempos(periodo, duracion)
    if not soporta_sigalrm():
        return None

    avisos = []
    inicio = time.perf_counter()
    trabajo_util = 0

    def isr(signum, frame):
        del signum, frame
        avisos.append(time.perf_counter() - inicio)

    anterior = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, isr)
    try:
        signal.setitimer(signal.ITIMER_REAL, periodo, periodo)
        while time.perf_counter() - inicio < duracion:
            trabajo_util += 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, anterior)

    return avisos, trabajo_util


def ejecutar_votacion(periodo=0.5, duracion=3.25):
    """Consulta el reloj en cada vuelta y devuelve (avisos, consultas)."""
    _validar_tiempos(periodo, duracion)
    avisos = []
    consultas = 0
    inicio = time.perf_counter()
    siguiente = periodo

    while True:
        transcurrido = time.perf_counter() - inicio
        consultas += 1
        if transcurrido >= duracion:
            break
        while transcurrido >= siguiente and siguiente < duracion - 1e-12:
            avisos.append(transcurrido)
            siguiente += periodo

    return avisos, consultas


def _formatear_avisos(avisos):
    return '[' + ', '.join('%.3f' % t for t in avisos) + ']'


def verificar():
    """Devuelve [(descripcion, cumple)] para comparacion_es.py."""
    resultados = []

    def anotar(nombre, cumple):
        resultados.append((nombre, bool(cumple)))

    anotar(
        'teoria: 0.5 s durante 3.25 s -> 6 avisos',
        avisos_teoricos(0.5, 3.25) == 6,
    )
    anotar(
        'teoria: 0.25 s durante 3.25 s -> 13 avisos en el limite',
        avisos_teoricos(0.25, 3.25) == 13,
    )

    avisos_poll, consultas = ejecutar_votacion(0.02, 0.13)
    anotar('votacion escalada: registra 6 avisos', len(avisos_poll) == 6)
    anotar(
        'votacion: hace muchas mas consultas que avisos',
        consultas > len(avisos_poll),
    )

    if soporta_sigalrm():
        avisos_irq, trabajo = ejecutar_interrupciones(0.02, 0.13)
        anotar('SIGALRM escalado: registra 6 avisos', len(avisos_irq) == 6)
        anotar(
            'SIGALRM: el bucle realiza trabajo util entre avisos',
            trabajo > len(avisos_irq),
        )
        tolerancia = 0.012
        esperados = [0.02 * i for i in range(1, 7)]
        anotar(
            'SIGALRM: avisos cercanos a los instantes esperados',
            len(avisos_irq) == 6
            and all(
                abs(observado - esperado) <= tolerancia
                for observado, esperado in zip(avisos_irq, esperados)
            ),
        )
    return resultados


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Interrupciones y votacion del modulo 4 de DeliFIIS'
    )
    parser.add_argument(
        '--periodo',
        type=float,
        default=0.5,
        help='periodo entre avisos en segundos (default: 0.5)',
    )
    parser.add_argument(
        '--duracion',
        type=float,
        default=3.25,
        help='duracion total en segundos (default: 3.25)',
    )
    parser.add_argument(
        '--modo',
        choices=('interrupciones', 'votacion', 'ambos'),
        default='ambos',
    )
    args = parser.parse_args(argv)

    try:
        _validar_tiempos(args.periodo, args.duracion)
    except ValueError as error:
        parser.error(str(error))

    esperado = avisos_teoricos(args.periodo, args.duracion)
    print(
        'Periodo: %.3f s | Duracion: %.3f s | Avisos teoricos: %d'
        % (args.periodo, args.duracion, esperado)
    )

    if args.modo in ('interrupciones', 'ambos'):
        if not soporta_sigalrm():
            print(
                'AVISO: SIGALRM no esta disponible. '
                'Ejecuta esta parte en Linux, WSL, VM o LabEx.'
            )
        else:
            avisos, trabajo = ejecutar_interrupciones(
                args.periodo,
                args.duracion,
            )
            print('\n=== SIGALRM ===')
            print('Avisos recibidos: %d' % len(avisos))
            print('Instantes (s): %s' % _formatear_avisos(avisos))
            print('Trabajo util (iteraciones): %d' % trabajo)
            if len(avisos) != esperado:
                print(
                    'Nota: el ultimo aviso puede coincidir con el fin '
                    'de la prueba y quedar en %d o %d.'
                    % (max(0, esperado - 1), esperado)
                )

    if args.modo in ('votacion', 'ambos'):
        avisos, consultas = ejecutar_votacion(
            args.periodo,
            args.duracion,
        )
        print('\n=== VOTACION ===')
        print('Avisos detectados: %d' % len(avisos))
        print('Instantes observados (s): %s' % _formatear_avisos(avisos))
        print('Consultas al reloj: %d' % consultas)

    print('\n=== VERIFICACION DE es_interrupciones.py ===')
    resultados = verificar()
    for nombre, cumple in resultados:
        print('[%s] %s' % ('OK' if cumple else 'FALLO', nombre))
    ok = sum(1 for _, cumple in resultados if cumple)
    print('Verificaciones correctas: %d/%d' % (ok, len(resultados)))
    print('RESULTADO: %s' % ('OK' if ok == len(resultados) else 'FALLO'))
    return 0 if ok == len(resultados) else 1


if __name__ == '__main__':
    raise SystemExit(main())

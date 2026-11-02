"""Modulo 4 (semana 9) - Metodos de E/S del caso DeliFIIS.

Rol R2. Compara votacion, interrupciones por byte y DMA usando los perfiles
definidos en es_comun.py. Incluye el perfil de control de la PPT y el perfil
propio del equipo. Si el costo de CPU supera el tiempo disponible, el resultado
se marca como SATURADO y no se considera una alternativa viable.

Salida por consola sin tildes (Windows).
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from es_comun import (
    METODOS,
    PERFILES,
    evaluar,
    n_minimo_dma,
    obtener_perfil,
    umbral_votacion_vs_interrupciones_us,
)

TAMANOS_BARRIDO = (1, 2, 4, 5, 8, 64, 512, 1500, 4096, 65536)
VELOCIDADES_BARRIDO = (0.5, 1, 2, 4, 5.5, 8.4, 10, 50, 100000)


def resultados_transferencia(n_bytes, us_por_byte, perfil):
    """Devuelve el resultado de los tres metodos para una transferencia."""
    return {
        metodo: evaluar(metodo, n_bytes, us_por_byte, perfil)
        for metodo in METODOS
    }


def mejor_metodo(n_bytes, us_por_byte, perfil):
    """Metodo con menor costo de CPU entre los resultados no saturados."""
    resultados = resultados_transferencia(n_bytes, us_por_byte, perfil)
    viables = [r for r in resultados.values() if not r['saturado']]
    if not viables:
        return None
    return min(
        viables,
        key=lambda r: (r['costo_us'], METODOS.index(r['metodo']))
    )['metodo']


def tabla_dispositivos(perfil):
    """Devuelve filas con costo y porcentaje por dispositivo y metodo."""
    filas = []
    for nombre, datos in perfil['dispositivos'].items():
        for metodo in METODOS:
            resultado = evaluar(
                metodo,
                datos['bytes'],
                datos['us_por_byte'],
                perfil,
            )
            filas.append({
                'dispositivo': nombre,
                'bytes': datos['bytes'],
                'us_por_byte': datos['us_por_byte'],
                **resultado,
            })
    return filas


def barrido_tamanos(perfil, us_por_byte, tamanos=TAMANOS_BARRIDO):
    """Evalua los tres metodos para distintos tamanos de transferencia."""
    filas = []
    for n_bytes in tamanos:
        resultados = resultados_transferencia(n_bytes, us_por_byte, perfil)
        filas.append({
            'n_bytes': n_bytes,
            'us_por_byte': us_por_byte,
            'mejor': mejor_metodo(n_bytes, us_por_byte, perfil),
            'resultados': resultados,
        })
    return filas


def barrido_velocidad(perfil, n_bytes, tiempos=VELOCIDADES_BARRIDO):
    """Evalua los tres metodos para distintas velocidades del dispositivo."""
    filas = []
    for us_por_byte in tiempos:
        resultados = resultados_transferencia(n_bytes, us_por_byte, perfil)
        filas.append({
            'n_bytes': n_bytes,
            'us_por_byte': us_por_byte,
            'mejor': mejor_metodo(n_bytes, us_por_byte, perfil),
            'resultados': resultados,
        })
    return filas


def _fmt_numero(valor):
    if abs(valor - round(valor)) < 1e-9:
        return str(int(round(valor)))
    return ('%.4f' % valor).rstrip('0').rstrip('.')


def imprimir_tabla_dispositivos(nombre_perfil, perfil):
    print('\n=== PERFIL %s ===' % nombre_perfil)
    print(
        'Umbral votacion/interrupciones: %s us/byte'
        % _fmt_numero(umbral_votacion_vs_interrupciones_us(perfil))
    )
    print(
        'N minimo en que DMA gana a interrupciones: %d bytes'
        % n_minimo_dma(perfil)
    )
    print(
        '%-10s%-16s%14s%13s%12s'
        % ('Disp.', 'Metodo', 'CPU (us)', '% transf.', 'Estado')
    )
    print('-' * 65)
    for fila in tabla_dispositivos(perfil):
        estado = 'SATURADO' if fila['saturado'] else 'OK'
        print(
            '%-10s%-16s%14s%12.4f%%%12s'
            % (
                fila['dispositivo'],
                fila['metodo'],
                _fmt_numero(fila['costo_us']),
                fila['porcentaje'],
                estado,
            )
        )


def imprimir_barrido_tamanos(perfil, us_por_byte):
    print(
        '\n=== BARRIDO DE TAMANOS (%s us/byte) ==='
        % _fmt_numero(us_por_byte)
    )
    print(
        '%10s%16s%16s%16s%16s'
        % ('Bytes', 'Votacion', 'Interrupciones', 'DMA', 'Mejor')
    )
    print('-' * 74)
    for fila in barrido_tamanos(perfil, us_por_byte):
        costos = []
        for metodo in METODOS:
            resultado = fila['resultados'][metodo]
            texto = _fmt_numero(resultado['costo_us'])
            if resultado['saturado']:
                texto += '*'
            costos.append(texto)
        print(
            '%10d%16s%16s%16s%16s'
            % (
                fila['n_bytes'],
                costos[0],
                costos[1],
                costos[2],
                fila['mejor'] or 'ninguno',
            )
        )
    print('* SATURADO: el costo de CPU supera el tiempo de transferencia.')


def imprimir_barrido_velocidad(perfil, n_bytes):
    print('\n=== BARRIDO DE VELOCIDAD (N=%d bytes) ===' % n_bytes)
    print(
        '%14s%16s%16s%16s%16s'
        % ('us/byte', 'Votacion', 'Interrupciones', 'DMA', 'Mejor')
    )
    print('-' * 78)
    for fila in barrido_velocidad(perfil, n_bytes):
        costos = []
        for metodo in METODOS:
            resultado = fila['resultados'][metodo]
            texto = _fmt_numero(resultado['costo_us'])
            if resultado['saturado']:
                texto += '*'
            costos.append(texto)
        print(
            '%14s%16s%16s%16s%16s'
            % (
                _fmt_numero(fila['us_por_byte']),
                costos[0],
                costos[1],
                costos[2],
                fila['mejor'] or 'ninguno',
            )
        )
    print('* SATURADO: el costo de CPU supera el tiempo de transferencia.')


def verificar():
    """Devuelve [(descripcion, cumple)] para comparacion_es.py."""
    resultados = []

    def anotar(nombre, cumple):
        resultados.append((nombre, bool(cumple)))

    ppt = obtener_perfil('ppt_control')
    deli = obtener_perfil('delifiis')

    controles = [
        ('ppt 4096 votacion', evaluar('votacion', 4096, 10, ppt)['costo_us'], 40960),
        ('ppt 4096 interrupciones', evaluar('interrupciones', 4096, 10, ppt)['costo_us'], 22528),
        ('ppt 4096 dma', evaluar('dma', 4096, 10, ppt)['costo_us'], 25),
        ('ppt 65536 votacion', evaluar('votacion', 65536, 10, ppt)['costo_us'], 655360),
        ('ppt 65536 interrupciones', evaluar('interrupciones', 65536, 10, ppt)['costo_us'], 360448),
        ('ppt 65536 dma', evaluar('dma', 65536, 10, ppt)['costo_us'], 25),
        ('delifiis disco votacion', evaluar('votacion', 4096, 4, deli)['costo_us'], 16384),
        ('delifiis disco interrupciones', evaluar('interrupciones', 4096, 4, deli)['costo_us'], 34406.4),
        ('delifiis disco dma', evaluar('dma', 4096, 4, deli)['costo_us'], 38),
        ('delifiis red votacion', evaluar('votacion', 1500, 1, deli)['costo_us'], 1500),
        ('delifiis red interrupciones', evaluar('interrupciones', 1500, 1, deli)['costo_us'], 12600),
        ('delifiis red dma', evaluar('dma', 1500, 1, deli)['costo_us'], 38),
        ('delifiis teclado votacion', evaluar('votacion', 1, 100000, deli)['costo_us'], 100000),
        ('delifiis teclado interrupciones', evaluar('interrupciones', 1, 100000, deli)['costo_us'], 8.4),
        ('delifiis teclado dma', evaluar('dma', 1, 100000, deli)['costo_us'], 38),
    ]
    for nombre, obtenido, esperado in controles:
        anotar(
            nombre + ' = %s us' % esperado,
            abs(obtenido - esperado) < 1e-6,
        )

    anotar(
        'delifiis: interrupciones de disco quedan SATURADAS',
        evaluar('interrupciones', 4096, 4, deli)['saturado'],
    )
    anotar(
        'delifiis: interrupciones de red quedan SATURADAS',
        evaluar('interrupciones', 1500, 1, deli)['saturado'],
    )
    anotar(
        'umbral ppt_control = 5.5 us/byte',
        abs(umbral_votacion_vs_interrupciones_us(ppt) - 5.5) < 1e-9,
    )
    anotar(
        'umbral delifiis = 8.4 us/byte',
        abs(umbral_votacion_vs_interrupciones_us(deli) - 8.4) < 1e-9,
    )
    anotar(
        'DMA gana a interrupciones desde N=5 en ambos perfiles',
        n_minimo_dma(ppt) == 5 and n_minimo_dma(deli) == 5,
    )

    anotar('ppt: N=4, 1 us/byte -> votacion', mejor_metodo(4, 1, ppt) == 'votacion')
    anotar('ppt: N=4, 10 us/byte -> interrupciones', mejor_metodo(4, 10, ppt) == 'interrupciones')
    anotar('ppt: N=5, 10 us/byte -> dma', mejor_metodo(5, 10, ppt) == 'dma')
    anotar(
        'ppt: N=1, 100000 us/byte -> interrupciones',
        mejor_metodo(1, 100000, ppt) == 'interrupciones',
    )
    anotar('delifiis: disco -> dma', mejor_metodo(4096, 4, deli) == 'dma')
    anotar('delifiis: red -> dma', mejor_metodo(1500, 1, deli) == 'dma')
    anotar(
        'delifiis: teclado -> interrupciones',
        mejor_metodo(1, 100000, deli) == 'interrupciones',
    )
    return resultados


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Metodos de E/S del modulo 4 de DeliFIIS'
    )
    parser.add_argument(
        '--perfil',
        choices=tuple(PERFILES),
        default=None,
        help='perfil a mostrar; por defecto muestra ambos',
    )
    parser.add_argument(
        '--barridos',
        action='store_true',
        help='muestra barridos de tamanos y velocidades',
    )
    args = parser.parse_args(argv)

    nombres = (args.perfil,) if args.perfil else tuple(PERFILES)
    for nombre in nombres:
        perfil = obtener_perfil(nombre)
        imprimir_tabla_dispositivos(nombre, perfil)
        if args.barridos and 'disco' in perfil['dispositivos']:
            disco = perfil['dispositivos']['disco']
            imprimir_barrido_tamanos(perfil, disco['us_por_byte'])
            imprimir_barrido_velocidad(perfil, disco['bytes'])

    print('\n=== VERIFICACION DE es_metodos.py ===')
    resultados = verificar()
    for nombre, cumple in resultados:
        print('[%s] %s' % ('OK' if cumple else 'FALLO', nombre))
    ok = sum(1 for _, cumple in resultados if cumple)
    print('Verificaciones correctas: %d/%d' % (ok, len(resultados)))
    print('RESULTADO: %s' % ('OK' if ok == len(resultados) else 'FALLO'))
    return 0 if ok == len(resultados) else 1


if __name__ == '__main__':
    raise SystemExit(main())

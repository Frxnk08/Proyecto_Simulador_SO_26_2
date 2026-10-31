'''Modulo 4 (semana 9) - Constantes y formulas comunes de E/S. Caso: DeliFIIS.

Perfiles de valores (ppt_control y delifiis) y formula de costo de CPU de los
tres metodos de E/S. Los tiempos son unidades didacticas, no hardware real.
Salida por consola sin tildes (Windows).
'''

from __future__ import annotations

import math

TAM_BLOQUE = 4096  # bytes; igual que TAM_PAGINA del modulo 3
METODOS = ('votacion', 'interrupciones', 'dma')

PERFILES = {
    # Valores de control de la PPT de la semana 9 (NO cambiar).
    'ppt_control': {
        'copia_us': 0.5,      # copiar 1 byte
        'isr_us': 5,          # atender 1 interrupcion
        'dma_prep_us': 20,    # preparar el DMA
        'dispositivos': {
            'disco': {'bytes': 4096, 'us_por_byte': 10},
        },
    },
    # Valores propios del equipo (se pueden ajustar; avisar al grupo).
    'delifiis': {
        'copia_us': 0.4,
        'isr_us': 8,
        'dma_prep_us': 30,
        'dispositivos': {
            'disco': {'bytes': 4096, 'us_por_byte': 4},
            'red': {'bytes': 1500, 'us_por_byte': 1},
            'teclado': {'bytes': 1, 'us_por_byte': 100000},
        },
    },
}


def obtener_perfil(nombre):
    if nombre not in PERFILES:
        raise ValueError('Perfil desconocido: %r. Disponibles: %s' % (nombre, list(PERFILES)))
    return PERFILES[nombre]


def costo_cpu_us(metodo, n_bytes, us_por_byte, perfil):
    '''CPU consumida (us) al transferir n_bytes con el metodo indicado.'''
    if n_bytes <= 0:
        raise ValueError('n_bytes debe ser mayor que cero')
    if us_por_byte <= 0:
        raise ValueError('us_por_byte debe ser mayor que cero')
    if metodo == 'votacion':
        return n_bytes * us_por_byte  # la CPU espera toda la transferencia
    if metodo == 'interrupciones':
        return n_bytes * (perfil['copia_us'] + perfil['isr_us'])  # una ISR y una copia por byte
    if metodo == 'dma':
        return perfil['dma_prep_us'] + perfil['isr_us']  # preparar DMA + una interrupcion final
    raise ValueError('Metodo desconocido: %r. Validos: %s' % (metodo, METODOS))


def evaluar(metodo, n_bytes, us_por_byte, perfil):
    '''Costo, porcentaje del tiempo de transferencia y marca de saturacion.

    saturado = True cuando el costo de CPU supera el tiempo total de la
    transferencia: el porcentaje pasaria de 100 % y no es fisicamente valido.
    '''
    total = n_bytes * us_por_byte
    costo = costo_cpu_us(metodo, n_bytes, us_por_byte, perfil)
    return {
        'metodo': metodo,
        'costo_us': costo,
        'total_us': total,
        'porcentaje': 100.0 * costo / total,
        'saturado': costo > total + 1e-9,
    }


def umbral_votacion_vs_interrupciones_us(perfil):
    '''us por byte del dispositivo por encima del cual interrupciones < votacion.'''
    return perfil['copia_us'] + perfil['isr_us']


def n_minimo_dma(perfil):
    '''Menor N (bytes) para el que DMA cuesta menos CPU que interrupciones por byte.'''
    x = (perfil['dma_prep_us'] + perfil['isr_us']) / (perfil['copia_us'] + perfil['isr_us'])
    return math.floor(x) + 1


if __name__ == '__main__':
    for nombre, perfil in PERFILES.items():
        print('=== PERFIL %s ===' % nombre)
        print('Umbral votacion/interrupciones: %s us/byte' % umbral_votacion_vs_interrupciones_us(perfil))
        print('N minimo en que DMA gana a interrupciones: %d bytes' % n_minimo_dma(perfil))
        for disp, d in perfil['dispositivos'].items():
            for m in METODOS:
                r = evaluar(m, d['bytes'], d['us_por_byte'], perfil)
                marca = ' SATURADO' if r['saturado'] else ''
                print('%-8s%-16s%12.1f us %9.4f %%%s' % (disp, m, r['costo_us'], r['porcentaje'], marca))
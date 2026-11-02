'''Modulo 4 (semana 9) - Catalogo de dispositivos de DeliFIIS.

Rol R1. Clasifica los dispositivos del caso en bloque, caracter y red y
asigna el metodo de E/S recomendado segun la PPT de la semana 9:
transferencias grandes (disco, red) -> DMA; dispositivos lentos con pocos
datos (teclado) -> interrupciones; la impresora es de uso exclusivo y se
atiende con spooling (ver es_buffer_spooling.py).

Salida por consola sin tildes (Windows).
'''

from __future__ import annotations

TIPOS = ('bloque', 'caracter', 'red')

CATALOGO = [
    {
        'nombre': 'disco',
        'tipo': 'bloque',
        'ruta_linux': '/dev/sda (o /dev/vda)',
        'equivalente': 'almacen de recetas (archivo de fichas)',
        'metodo_recomendado': 'dma',
        'uso': 'compartido',
    },
    {
        'nombre': 'red',
        'tipo': 'red',
        'ruta_linux': 'enp0s3 (o eth0), interfaz sin archivo en /dev',
        'equivalente': 'ventanilla de pedidos de las sucursales',
        'metodo_recomendado': 'dma',
        'uso': 'compartido',
    },
    {
        'nombre': 'teclado',
        'tipo': 'caracter',
        'ruta_linux': '/dev/tty',
        'equivalente': 'timbre de la torre de control',
        'metodo_recomendado': 'interrupciones',
        'uso': 'compartido',
    },
    {
        'nombre': 'impresora',
        'tipo': 'caracter',
        'ruta_linux': 'cola de spool (sin ruta fija)',
        'equivalente': 'impresora de comandas',
        'metodo_recomendado': None,  # se atiende con spooling
        'uso': 'exclusivo',
    },
]


def obtener(nombre):
    for d in CATALOGO:
        if d['nombre'] == nombre:
            return d
    raise ValueError('Dispositivo desconocido: %r. Disponibles: %s'
                     % (nombre, [d['nombre'] for d in CATALOGO]))


def metodo_recomendado(nombre):
    '''Metodo de E/S recomendado ('dma', 'interrupciones') o None si usa spool.'''
    return obtener(nombre)['metodo_recomendado']


def listar_por_tipo(tipo):
    if tipo not in TIPOS:
        raise ValueError('Tipo desconocido: %r. Validos: %s' % (tipo, TIPOS))
    return [d for d in CATALOGO if d['tipo'] == tipo]


def imprimir_catalogo():
    print('%-11s%-10s%-16s%-12s%s' % ('Disp.', 'Tipo', 'Metodo', 'Uso', 'En DeliFIIS'))
    print('-' * 80)
    for d in CATALOGO:
        metodo = d['metodo_recomendado'] or 'spool'
        print('%-11s%-10s%-16s%-12s%s' % (d['nombre'], d['tipo'], metodo, d['uso'], d['equivalente']))


def verificar():
    '''Devuelve [(descripcion, cumple)] para comparacion_es.py.'''
    r = []

    def anotar(nombre, cumple):
        r.append((nombre, bool(cumple)))

    anotar('el catalogo tiene 4 dispositivos', len(CATALOGO) == 4)
    esperados = {'disco': 'bloque', 'red': 'red', 'teclado': 'caracter', 'impresora': 'caracter'}
    anotar('tipos: disco bloque, red red, teclado y impresora caracter',
           {d['nombre']: d['tipo'] for d in CATALOGO} == esperados)
    anotar('metodos: disco dma, red dma, teclado interrupciones, impresora None',
           (metodo_recomendado('disco'), metodo_recomendado('red'),
            metodo_recomendado('teclado'), metodo_recomendado('impresora'))
           == ('dma', 'dma', 'interrupciones', None))
    anotar('la impresora es de uso exclusivo', obtener('impresora')['uso'] == 'exclusivo')
    anotar('listar_por_tipo(caracter) = teclado e impresora',
           sorted(d['nombre'] for d in listar_por_tipo('caracter')) == ['impresora', 'teclado'])
    try:
        obtener('monitor')
        anotar('un dispositivo desconocido lanza ValueError', False)
    except ValueError:
        anotar('un dispositivo desconocido lanza ValueError', True)
    try:
        listar_por_tipo('otro')
        anotar('un tipo desconocido lanza ValueError', False)
    except ValueError:
        anotar('un tipo desconocido lanza ValueError', True)
    return r


def main():
    print('=== CATALOGO DE DISPOSITIVOS DE DeliFIIS ===')
    imprimir_catalogo()
    print('\n=== VERIFICACION DE es_dispositivos.py ===')
    resultados = verificar()
    for nombre, cumple in resultados:
        print('[%s] %s' % ('OK' if cumple else 'FALLO', nombre))
    ok = sum(1 for _, c in resultados if c)
    print('Verificaciones correctas: %d/%d' % (ok, len(resultados)))
    print('RESULTADO: %s' % ('OK' if ok == len(resultados) else 'FALLO'))
    return 0 if ok == len(resultados) else 1


if __name__ == '__main__':
    raise SystemExit(main())
'''Modulo 4 (semana 9) - Exploracion de dispositivos e interrupciones en Linux.

Rol R1. Lee /proc/devices, /proc/interrupts, /sys/block y /sys/class/net para
reconocer dispositivos (bloque, caracter, red) y observar que filas de
/proc/interrupts crecen al generar actividad. SOLO LINUX (WSL, VM o LabEx):
en Windows avisa y solo ejecuta las verificaciones de los parsers.

Uso:
    python3 es_explorar_linux.py              tabla de reconocimiento + verificacion
    python3 es_explorar_linux.py --medir 20   captura antes, espera 20 s, captura
                                              despues y muestra las filas que crecieron

Los numeros de /proc/interrupts cambian en cada equipo: no hay valor de control.
Salida por consola sin tildes (Windows).
'''

from __future__ import annotations

import argparse
import os
import stat
import sys
import time

PROC_DEVICES = '/proc/devices'
PROC_INTERRUPTS = '/proc/interrupts'


def es_linux():
    return os.path.exists(PROC_DEVICES) and os.path.exists(PROC_INTERRUPTS)


# ---- parsers (funcionan sobre texto; se verifican en cualquier sistema) ----
def _parsear_devices(texto):
    '''Separa /proc/devices en {'caracter': [(mayor, nombre)], 'bloque': [...]}.'''
    resultado = {'caracter': [], 'bloque': []}
    seccion = None
    for linea in texto.splitlines():
        linea = linea.strip()
        if linea == 'Character devices:':
            seccion = 'caracter'
        elif linea == 'Block devices:':
            seccion = 'bloque'
        elif linea and seccion:
            partes = linea.split(None, 1)
            if len(partes) == 2 and partes[0].isdigit():
                resultado[seccion].append((int(partes[0]), partes[1]))
    return resultado


def _parsear_interrupts(texto):
    '''Devuelve {irq: {'por_cpu': [...], 'total': int, 'descripcion': str}}.'''
    lineas = texto.splitlines()
    if not lineas:
        return {}
    ncpu = len(lineas[0].split())
    filas = {}
    for linea in lineas[1:]:
        if ':' not in linea:
            continue
        irq, resto = linea.split(':', 1)
        tokens = resto.split()
        cuentas = []
        i = 0
        while i < len(tokens) and tokens[i].isdigit() and len(cuentas) < ncpu:
            cuentas.append(int(tokens[i]))
            i += 1
        filas[irq.strip()] = {
            'por_cpu': cuentas,
            'total': sum(cuentas),
            'descripcion': ' '.join(tokens[i:]),
        }
    return filas


def leer_dispositivos_proc(ruta=PROC_DEVICES):
    with open(ruta, 'r', encoding='utf-8', errors='replace') as f:
        return _parsear_devices(f.read())


def leer_interrupciones(ruta=PROC_INTERRUPTS):
    with open(ruta, 'r', encoding='utf-8', errors='replace') as f:
        return _parsear_interrupts(f.read())


def diferencia(antes, despues):
    '''Filas cuyo contador total aumento: [(irq, aumento, descripcion)], de mayor a menor.'''
    cambios = []
    for irq, fila in despues.items():
        previo = antes.get(irq, {'total': 0})['total']
        delta = fila['total'] - previo
        if delta > 0:
            cambios.append((irq, delta, fila['descripcion']))
    return sorted(cambios, key=lambda c: c[1], reverse=True)


# ---- reconocimiento de dispositivos ------------------------------------------
def tipo_de_ruta_dev(ruta):
    '''Devuelve 'bloque', 'caracter' o None segun stat() de la ruta.'''
    try:
        modo = os.stat(ruta).st_mode
    except OSError:
        return None
    if stat.S_ISBLK(modo):
        return 'bloque'
    if stat.S_ISCHR(modo):
        return 'caracter'
    return None


def _listar(ruta):
    try:
        return sorted(os.listdir(ruta))
    except OSError:
        return []


def tabla_reconocimiento():
    '''Filas {dispositivo, tipo, evidencia, equivalente} con lo que haya en el equipo.'''
    filas = []
    for ruta in ('/dev/null', '/dev/zero', '/dev/tty'):
        tipo = tipo_de_ruta_dev(ruta)
        if tipo:
            filas.append({'dispositivo': ruta, 'tipo': tipo,
                          'evidencia': 'stat(%s) -> %s' % (ruta, tipo),
                          'equivalente': 'timbre / comanda que va llegando'})
    for nombre in _listar('/sys/block'):
        if nombre.startswith(('loop', 'ram')):
            continue
        ruta = '/dev/' + nombre
        tipo = tipo_de_ruta_dev(ruta)
        if tipo == 'bloque':
            filas.append({'dispositivo': ruta, 'tipo': 'bloque',
                          'evidencia': '/sys/block/%s + stat(%s) -> bloque' % (nombre, ruta),
                          'equivalente': 'almacen de recetas (archivo de fichas)'})
            break
    for nombre in _listar('/sys/class/net'):
        if nombre != 'lo':
            filas.append({'dispositivo': nombre, 'tipo': 'red',
                          'evidencia': '/sys/class/net/%s existe (interfaz, no archivo en /dev)' % nombre,
                          'equivalente': 'ventanilla de pedidos (telefono)'})
            break
    return filas


def imprimir_tabla(filas):
    print('%-16s%-10s%-66s%s' % ('Dispositivo', 'Tipo', 'Evidencia', 'En la cocina'))
    print('-' * 125)
    for f in filas:
        print('%-16s%-10s%-66s%s' % (f['dispositivo'], f['tipo'], f['evidencia'], f['equivalente']))


def medir(segundos):
    '''Captura /proc/interrupts, espera y muestra las filas que crecieron.'''
    antes = leer_interrupciones()
    print('Captura inicial lista. Durante %s s teclea en la terminal, usa la red '
          '(ej. ping -c 10 8.8.8.8) y escribe un archivo grande en disco...' % segundos)
    time.sleep(segundos)
    despues = leer_interrupciones()
    cambios = diferencia(antes, despues)
    print('\nFilas de /proc/interrupts que aumentaron (%d):' % len(cambios))
    print('%-8s%12s  %s' % ('IRQ', 'Aumento', 'Descripcion (dispositivo asociado)'))
    print('-' * 70)
    for irq, delta, desc in cambios:
        print('%-8s%12d  %s' % (irq, delta, desc))
    if not cambios:
        print('(ninguna: genera mas actividad de teclado, red o disco)')
    return cambios


# ---- verificacion --------------------------------------------------------------
_MUESTRA_DEVICES = '''Character devices:
  1 mem
  4 tty
  5 /dev/tty

Block devices:
259 blkext
  8 sd
254 virtblk
'''

_MUESTRA_INT_ANTES = '''           CPU0       CPU1
  0:         10          0   IO-APIC   2-edge      timer
  1:        500        120   IO-APIC   1-edge      i8042
NMI:          0          0   Non-maskable interrupts
'''

_MUESTRA_INT_DESPUES = '''           CPU0       CPU1
  0:         10          0   IO-APIC   2-edge      timer
  1:        700        140   IO-APIC   1-edge      i8042
NMI:          0          0   Non-maskable interrupts
'''


def verificar():
    '''Devuelve [(descripcion, cumple)] para comparacion_es.py.'''
    r = []

    def anotar(nombre, cumple):
        r.append((nombre, bool(cumple)))

    dev = _parsear_devices(_MUESTRA_DEVICES)
    anotar('parser /proc/devices: 3 de caracter y 3 de bloque',
           len(dev['caracter']) == 3 and len(dev['bloque']) == 3)
    anotar('parser /proc/devices: (4, tty) esta en caracter y (8, sd) en bloque',
           (4, 'tty') in dev['caracter'] and (8, 'sd') in dev['bloque'])

    antes = _parsear_interrupts(_MUESTRA_INT_ANTES)
    despues = _parsear_interrupts(_MUESTRA_INT_DESPUES)
    anotar('parser /proc/interrupts: IRQ 1 suma 620 en 2 CPU',
           antes['1']['total'] == 620 and antes['1']['por_cpu'] == [500, 120])
    anotar('parser /proc/interrupts: descripcion de IRQ 1 es IO-APIC 1-edge i8042',
           antes['1']['descripcion'] == 'IO-APIC 1-edge i8042')
    anotar('parser /proc/interrupts: la fila NMI se lee',
           'NMI' in antes and antes['NMI']['total'] == 0)
    anotar('diferencia: solo crece la IRQ 1, en 220',
           diferencia(antes, despues) == [('1', 220, 'IO-APIC 1-edge i8042')])

    if es_linux():
        proc = leer_dispositivos_proc()
        anotar('Linux: /proc/devices trae dispositivos de caracter y de bloque',
               len(proc['caracter']) > 0 and len(proc['bloque']) > 0)
        anotar('Linux: /proc/interrupts trae al menos una fila', len(leer_interrupciones()) > 0)
        anotar('Linux: la tabla de reconocimiento tiene al menos 4 dispositivos',
               len(tabla_reconocimiento()) >= 4)
    return r


def main(argv=None):
    parser = argparse.ArgumentParser(description='Exploracion de E/S en Linux (modulo 4, semana 9)')
    parser.add_argument('--medir', type=float, default=None, metavar='SEGUNDOS',
                        help='captura /proc/interrupts, espera y muestra las filas que crecieron')
    args = parser.parse_args(argv)
    if args.medir is not None and args.medir <= 0:
        parser.error('--medir debe ser mayor que cero')

    if not es_linux():
        print('AVISO: /proc no esta disponible. Ejecuta este script en Linux (WSL, VM o LabEx).')
        print('Solo se verifican los parsers con texto de muestra.')
    else:
        if args.medir is not None:
            medir(args.medir)
            return 0
        print('=== /proc/devices (resumen) ===')
        proc = leer_dispositivos_proc()
        for tipo in ('caracter', 'bloque'):
            nombres = ', '.join('%d:%s' % par for par in proc[tipo][:8])
            print('%-9s %d registrados. Primeros: %s' % (tipo, len(proc[tipo]), nombres))
        print('\n=== TABLA DE RECONOCIMIENTO (tipo segun stat y /sys) ===')
        imprimir_tabla(tabla_reconocimiento())

    print('\n=== VERIFICACION DE es_explorar_linux.py ===')
    resultados = verificar()
    for nombre, cumple in resultados:
        print('[%s] %s' % ('OK' if cumple else 'FALLO', nombre))
    ok = sum(1 for _, c in resultados if c)
    print('Verificaciones correctas: %d/%d' % (ok, len(resultados)))
    print('RESULTADO: %s' % ('OK' if ok == len(resultados) else 'FALLO'))
    return 0 if ok == len(resultados) else 1


if __name__ == '__main__':
    raise SystemExit(main())
'''Modulo 4 (semana 9) - Disco virtual de bloques. Caso: DeliFIIS.

Rol R1. Es el UNICO gancho entre la semana 9 (E/S) y la semana 10 (sistemas de
archivos): el sistema de archivos usara (o envolvera) esta clase desde archivos
fs_*.py, sin editar este archivo. La interfaz publica NO debe cambiar:

    DiscoVirtual(num_bloques=64, tam_bloque=TAM_BLOQUE, perfil='delifiis')
    leer(n) -> bytes (largo tam_bloque)
    escribir(n, datos)
    accesos_lectura, accesos_escritura, reiniciar_contadores()
    costo_cpu_us(metodo)
    ErrorDisco

Los costos son del modelo didactico de es_comun.py, no de hardware real.
Salida por consola sin tildes (Windows).
'''

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from es_comun import METODOS, TAM_BLOQUE, evaluar, obtener_perfil


class ErrorDisco(Exception):
    '''Acceso invalido al disco virtual (bloque fuera de rango o tipo incorrecto).'''


class DiscoVirtual:
    '''Disco de bloques de tamano fijo que cuenta sus accesos y su costo de CPU.'''

    def __init__(self, num_bloques=64, tam_bloque=TAM_BLOQUE, perfil='delifiis'):
        if not isinstance(num_bloques, int) or num_bloques <= 0:
            raise ValueError('num_bloques debe ser un entero mayor que cero')
        if not isinstance(tam_bloque, int) or tam_bloque <= 0:
            raise ValueError('tam_bloque debe ser un entero mayor que cero')
        self.num_bloques = num_bloques
        self.tam_bloque = tam_bloque
        self.perfil_nombre = perfil
        self._perfil = obtener_perfil(perfil)
        if 'disco' not in self._perfil['dispositivos']:
            raise ValueError("El perfil %r no define el dispositivo 'disco'" % perfil)
        self._bloques = [bytes(tam_bloque) for _ in range(num_bloques)]
        self.accesos_lectura = 0
        self.accesos_escritura = 0

    # ---- validaciones internas -------------------------------------------
    def _validar_bloque(self, n):
        if not isinstance(n, int) or isinstance(n, bool):
            raise ErrorDisco('el numero de bloque debe ser entero, se recibio %r' % (n,))
        if n < 0 or n >= self.num_bloques:
            raise ErrorDisco('bloque %d fuera de rango (0 a %d)' % (n, self.num_bloques - 1))

    # ---- interfaz publica ---------------------------------------------------
    def leer(self, n):
        '''Devuelve los tam_bloque bytes del bloque n y cuenta 1 lectura.'''
        self._validar_bloque(n)
        self.accesos_lectura += 1
        return self._bloques[n]

    def escribir(self, n, datos):
        '''Escribe datos en el bloque n (rellena con ceros) y cuenta 1 escritura.'''
        self._validar_bloque(n)
        if not isinstance(datos, (bytes, bytearray)):
            raise TypeError('datos debe ser bytes o bytearray')
        if len(datos) > self.tam_bloque:
            raise ValueError('los datos (%d bytes) no caben en un bloque de %d bytes'
                             % (len(datos), self.tam_bloque))
        self._bloques[n] = bytes(datos) + bytes(self.tam_bloque - len(datos))
        self.accesos_escritura += 1

    @property
    def accesos_totales(self):
        return self.accesos_lectura + self.accesos_escritura

    def reiniciar_contadores(self):
        self.accesos_lectura = 0
        self.accesos_escritura = 0

    def costo_cpu_us(self, metodo):
        '''CPU total (us) de todos los accesos hechos, tratando cada uno como
        una transferencia de 1 bloque con el metodo indicado.'''
        if metodo not in METODOS:
            raise ValueError('Metodo desconocido: %r. Validos: %s' % (metodo, METODOS))
        disco = self._perfil['dispositivos']['disco']
        por_bloque = evaluar(metodo, self.tam_bloque, disco['us_por_byte'], self._perfil)['costo_us']
        return self.accesos_totales * por_bloque


def verificar():
    '''Devuelve [(descripcion, cumple)] para comparacion_es.py.'''
    r = []

    def anotar(nombre, cumple):
        r.append((nombre, bool(cumple)))

    d = DiscoVirtual(16, perfil='ppt_control')
    anotar('bloque nuevo vale ceros y mide 4096', d.leer(0) == bytes(4096))
    d.reiniciar_contadores()
    d.escribir(3, b'hola')
    dato = d.leer(3)
    anotar('escribir b\'hola\' en bloque 3 y leerlo: b\'hola\' + ceros', dato == b'hola' + bytes(4092))
    anotar('el bloque leido mide 4096 bytes', len(dato) == 4096)
    anotar('contadores: 1 lectura y 1 escritura', (d.accesos_lectura, d.accesos_escritura) == (1, 1))
    anotar('ppt_control: 2 accesos con DMA = 50 us', d.costo_cpu_us('dma') == 50)
    anotar('ppt_control: 2 accesos con votacion = 81920 us', d.costo_cpu_us('votacion') == 81920)
    anotar('ppt_control: 2 accesos con interrupciones = 45056 us',
           abs(d.costo_cpu_us('interrupciones') - 45056) < 1e-6)

    try:
        d.leer(16)
        anotar('bloque 16 de un disco de 16 bloques lanza ErrorDisco', False)
    except ErrorDisco:
        anotar('bloque 16 de un disco de 16 bloques lanza ErrorDisco', True)
    try:
        d.leer(-1)
        anotar('bloque -1 lanza ErrorDisco', False)
    except ErrorDisco:
        anotar('bloque -1 lanza ErrorDisco', True)
    anotar('los accesos invalidos no se cuentan', d.accesos_totales == 2)

    try:
        d.escribir(0, bytes(4097))
        anotar('datos de 4097 bytes lanzan ValueError', False)
    except ValueError:
        anotar('datos de 4097 bytes lanzan ValueError', True)

    d.reiniciar_contadores()
    anotar('reiniciar_contadores deja ambos en 0', d.accesos_totales == 0)

    p = DiscoVirtual(8, perfil='delifiis')
    p.escribir(0, b'x')
    p.leer(0)
    anotar('delifiis: 2 accesos con DMA = 76 us', p.costo_cpu_us('dma') == 76)
    return r


def main():
    print('=== VERIFICACION DE es_disco.py (DiscoVirtual) ===')
    resultados = verificar()
    for nombre, cumple in resultados:
        print('[%s] %s' % ('OK' if cumple else 'FALLO', nombre))
    ok = sum(1 for _, c in resultados if c)
    print('Verificaciones correctas: %d/%d' % (ok, len(resultados)))
    print('RESULTADO: %s' % ('OK' if ok == len(resultados) else 'FALLO'))
    return 0 if ok == len(resultados) else 1


if __name__ == '__main__':
    raise SystemExit(main())
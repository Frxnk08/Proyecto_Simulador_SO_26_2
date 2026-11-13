'''Modulo 5 (semana 11) - sec_comun.py
Caso: DeliFIIS. Ruta a M1/M3/M4, valores de CONTROL y utilidades compartidas por los archivos sec_*.py.
Sin logica de algoritmos. Salida por consola sin tildes (Windows).
'''

from __future__ import annotations

import os
import platform
import shutil
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
for _carpeta in ('modulo4', 'modulo3', os.path.join('modulo1', 'codigo_py')):
    _ruta = os.path.abspath(os.path.join(_AQUI, '..', _carpeta))
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

# Reutiliza lo de la semana 10 (no se redefine)
from fs_comun import USUARIOS, imprimir_verificaciones  # noqa: E402,F401

ROLES = list(USUARIOS)  # ['chef', 'ayudante', 'visitante']


def herramienta_disponible(nombre: str) -> bool:
    '''True si el programa (gpg, gcc, iptables...) esta en el PATH.'''
    return shutil.which(nombre) is not None


def es_linux() -> bool:
    return platform.system() == 'Linux'


# ---- Valores de CONTROL (PPT semana 11 y practica dirigida; NO cambiar) ----
SAL_1 = bytes.fromhex('00112233445566778899aabbccddeeff')
SAL_2 = bytes.fromhex('ffeeddccbbaa99887766554433221100')

CONTROL = {
    'clave': 'ceviche123',
    'sha256_16': '55e006c75c2f282a',
    'pbkdf2_16': {'sal1': 'd1dc65b61a3b43f6', 'sal2': '708b03c6f415e847'},  # 100 000 iteraciones
    'velocidad': 10 ** 9,  # intentos por segundo (supuesto didactico)
    # nombre: (simbolos, largo, combinaciones)
    'fuerza_bruta': {
        '8 minusculas': (26, 8, 208_827_064_576),
        '8 letras y digitos': (62, 8, 218_340_105_584_896),
        '8 imprimibles': (94, 8, 6_095_689_385_410_816),
        '12 minusculas': (26, 12, 95_428_956_661_682_176),
        '12 letras y digitos': (62, 12, 3_226_266_762_397_899_821_056),
    },
    # (minutos, dias, anios) aproximados del peor caso, 2 decimales
    'tiempos': {
        '8 minusculas': (3.5, 0.00, 0.00),
        '8 letras y digitos': (3639.0, 2.53, 0.01),
        '8 imprimibles': (101594.8, 70.55, 0.19),
        '12 minusculas': (1590482.6, 1104.50, 3.02),
        '12 letras y digitos': (53771112706.6, 37341050.49, 102234.22),
    },
    # matriz de acceso del chef: archivo -> {usuario: (lee, escribe)}
    'matriz': {
        'receta.txt': {'chef': (True, True), 'ayudante': (True, False), 'visitante': (False, False)},
        'stock.csv': {'chef': (True, True), 'ayudante': (True, True), 'visitante': (False, False)},
        'caja.log': {'chef': (True, False), 'ayudante': (False, False), 'visitante': (False, False)},
    },
    'modos': {'receta.txt': 0o640, 'stock.csv': 0o660, 'caja.log': 0o400},
    'acl_receta': {'chef': ('leer', 'escribir'), 'ayudante': ('leer',)},
    'capacidades_ayudante': {'receta.txt': ('leer',), 'stock.csv': ('leer', 'escribir')},
    # firewall: reglas (proto, puerto, accion), politica por defecto y resultados
    'reglas': [('tcp', 22, 'ACCEPT'), ('tcp', 80, 'ACCEPT'), ('tcp', 443, 'ACCEPT'), ('tcp', 3306, 'DROP')],
    'politica': 'DROP',
    'paquetes': {('tcp', 22): 'ACCEPT', ('tcp', 443): 'ACCEPT', ('tcp', 3306): 'DROP',
                 ('tcp', 23): 'DROP', ('udp', 53): 'DROP', ('tcp', 80): 'ACCEPT'},
    # mensajes de gpg (con LC_ALL=C)
    'gpg': {'clave_mala': 'Bad session key', 'sin_secreta': 'No secret key',
            'firma_ok': 'Good signature', 'firma_mala': 'BAD signature'},
}
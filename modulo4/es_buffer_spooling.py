'''Modulo 4 (semana 9) - Bufering y Spooling de E/S. Caso: DeliFIIS.

Rol R3 (Leonel). Implementa:
1. tiempo_total(n_bloques, lectura_ms, proceso_ms, buffers):
   Simulacion por eventos temporizados con buffers >= 1 (1 = sin bufer,
   2 = doble bufer, 3 o mas para experimentacion). No es solo la formula.
2. cuello_botella(lectura_ms, proceso_ms): 'dispositivo', 'cpu' o 'equilibrado'.
3. diagrama_texto(n_bloques, lectura_ms, proceso_ms, buffers): carriles en texto.
4. simular_spool(conjunto, capacidad, t_impresion_s, escala_s):
   Reutiliza el patron de modulo2/productor_consumidor.py (mutex, vacios, llenos
   y None) coordinando pedidos de M1 hacia la impresora de comandas de DeliFIIS.

Salida por consola sin tildes (Windows).
'''

from __future__ import annotations

import os
import sys
import threading
import time
from typing import Sequence

# Asegurar importacion de modulo4 y modulo1
DIR_MODULO4 = os.path.dirname(os.path.abspath(__file__))
DIR_PROYECTO = os.path.abspath(os.path.join(DIR_MODULO4, '..'))
DIR_MODULO1 = os.path.join(DIR_PROYECTO, 'modulo1', 'codigo_py')

if DIR_MODULO4 not in sys.path:
    sys.path.insert(0, DIR_MODULO4)
if DIR_MODULO1 not in sys.path:
    sys.path.insert(0, DIR_MODULO1)

# Importar M1 de forma tolerante
try:
    from simulador_planificacion import CONJUNTO_EQUIPO, CONJUNTO_OFICIAL, Proceso, fcfs
except ImportError:
    # Definicion de respaldo en caso de ejecucion aislada
    class Proceso:  # type: ignore
        def __init__(self, id, llegada, duracion, prioridad=1, **kwargs):
            self.id = id
            self.llegada = llegada
            self.duracion = duracion
            self.prioridad = prioridad

    CONJUNTO_OFICIAL = (
        Proceso('P1', 0, 5), Proceso('P2', 1, 3),
        Proceso('P3', 2, 8), Proceso('P4', 3, 6)
    )
    CONJUNTO_EQUIPO = (
        Proceso('Q1', 0, 4), Proceso('Q2', 1, 7),
        Proceso('Q3', 2, 2), Proceso('Q4', 4, 5),
        Proceso('Q5', 6, 3)
    )

    def fcfs(procesos):
        t, gantt, metricas = 0, [], {}
        for p in sorted(procesos, key=lambda x: (x.llegada, x.id)):
            if t < p.llegada:
                t = p.llegada
            ini = t
            t += p.duracion
            gantt.append((p.id, ini, t))
            metricas[p.id] = type('Metrica', (), {'fin': t})()
        return gantt, metricas


# ==============================================================================
# PARTE A: MODELADO Y SIMULACION DE BUFERES (BUFFERING)
# ==============================================================================

def simular_buffering(n_bloques: int, lectura_ms: float, proceso_ms: float, buffers: int = 1):
    '''Simula evento a evento el flujo de n bloques a traves de K buferes.

    Retorna:
        (trazas, tiempo_total)
        Donde trazas es una lista de diccionarios con los tiempos de inicio y fin
        de lectura en dispositivo y procesamiento en CPU para cada bloque.
    '''
    if not isinstance(n_bloques, int) or n_bloques <= 0:
        raise ValueError('n_bloques debe ser un entero mayor que cero')
    if lectura_ms < 0 or proceso_ms < 0:
        raise ValueError('Los tiempos de lectura y proceso no pueden ser negativos')
    if not isinstance(buffers, int) or buffers < 1:
        raise ValueError('buffers debe ser un entero mayor o igual a 1')

    trazas = []
    fin_lecturas = []
    fin_procesos = []

    for i in range(n_bloques):
        # 1. El dispositivo no puede iniciar antes de terminar el bloque anterior
        disp_libre_en = fin_lecturas[-1] if fin_lecturas else 0.0

        # 2. El bufer i % buffers debe estar desocupado por la CPU
        if i < buffers:
            bufer_libre_en = 0.0
        else:
            # El bufer fue ocupado por el bloque (i - buffers); queda libre cuando la CPU lo termina
            bufer_libre_en = fin_procesos[i - buffers]

        inicio_l = max(disp_libre_en, bufer_libre_en)
        fin_l = inicio_l + lectura_ms

        # 3. La CPU no puede iniciar antes de terminar el bloque anterior
        cpu_libre_en = fin_procesos[-1] if fin_procesos else 0.0

        # 4. La CPU requiere que este bloque haya terminado de leerse en el bufer
        inicio_p = max(cpu_libre_en, fin_l)
        fin_p = inicio_p + proceso_ms

        fin_lecturas.append(fin_l)
        fin_procesos.append(fin_p)

        trazas.append({
            'bloque': i + 1,
            'bufer': (i % buffers) + 1,
            'inicio_lectura': inicio_l,
            'fin_lectura': fin_l,
            'inicio_proceso': inicio_p,
            'fin_proceso': fin_p,
        })

    tiempo_final = fin_procesos[-1] if fin_procesos else 0.0
    return trazas, tiempo_final


def tiempo_total(n_bloques: int, lectura_ms: float, proceso_ms: float, buffers: int = 1) -> float:
    '''Calcula el tiempo total (ms) mediante simulacion por eventos con buffers >= 1.'''
    _, t_total = simular_buffering(n_bloques, lectura_ms, proceso_ms, buffers)
    return t_total


def cuello_botella(lectura_ms: float, proceso_ms: float) -> str:
    '''Determina si el factor limitante es el dispositivo, la CPU o si esta equilibrado.'''
    if lectura_ms > proceso_ms:
        return 'dispositivo'
    elif proceso_ms > lectura_ms:
        return 'cpu'
    return 'equilibrado'


def diagrama_texto(n_bloques: int, lectura_ms: float, proceso_ms: float, buffers: int = 1) -> str:
    '''Genera un diagrama de Gantt en texto mostrando los carriles de Dispositivo y CPU.'''
    trazas, t_total = simular_buffering(n_bloques, lectura_ms, proceso_ms, buffers)
    cuello = cuello_botella(lectura_ms, proceso_ms)

    tipo_str = 'Sin bufer (1 bufer)' if buffers == 1 else f'Doble bufer ({buffers} buferes)'
    lineas = [
        f'=== DIAGRAMA DE BUFERING [{tipo_str}] ===',
        f'Parametros: {n_bloques} bloques, Lectura={lectura_ms} ms, Proceso={proceso_ms} ms',
        f'Tiempo total: {t_total:.1f} ms | Cuello de botella: {cuello}',
        '-' * 65,
        'Carril DISPOSITIVO (E/S):'
    ]

    for t in trazas:
        b_info = f' [B{t["bufer"]}]' if buffers > 1 else ''
        lineas.append(f'  L{t["bloque"]}{b_info:<5} : de {t["inicio_lectura"]:6.1f} ms a {t["fin_lectura"]:6.1f} ms (dur={lectura_ms} ms)')

    lineas.append('Carril CPU (Procesamiento):')
    for t in trazas:
        b_info = f' [B{t["bufer"]}]' if buffers > 1 else ''
        lineas.append(f'  P{t["bloque"]}{b_info:<5} : de {t["inicio_proceso"]:6.1f} ms a {t["fin_proceso"]:6.1f} ms (dur={proceso_ms} ms)')

    lineas.append('-' * 65)
    return '\n'.join(lineas)


# ==============================================================================
# PARTE B: SIMULACION DE SPOOLING (IMPRESORA DE COMANDAS)
# ==============================================================================

def simular_spool(conjunto, capacidad: int = 5, t_impresion_s: float = 0.05, escala_s: float = 0.05):
    '''Simula la cola de impresion de comandas (spooling) con hilos y semaforos.

    Reutiliza el patron de modulo2/productor_consumidor.py:
    - Cada pedido de M1 es un hilo productor que espera fin * escala_s y deposita su comanda.
    - Un hilo impresora consume las comandas e imprime a ritmo t_impresion_s.
    - Se senaliza el fin con None.

    Retorna:
        (insertadas, impresas, bloqueos_productores)
    '''
    # Determinar tiempos de fin segun FCFS de M1
    if isinstance(conjunto, str):
        if conjunto.lower() in ('oficial', 'p'):
            conjunto_procesos = CONJUNTO_OFICIAL
        elif conjunto.lower() in ('equipo', 'q'):
            conjunto_procesos = CONJUNTO_EQUIPO
        else:
            raise ValueError(f'Conjunto no reconocido: {conjunto}')
    else:
        conjunto_procesos = list(conjunto)

    _, metricas = fcfs(conjunto_procesos)

    # Primitivas de sincronizacion (patron Productor-Consumidor de M2)
    mutex = threading.Semaphore(1)
    vacios = threading.Semaphore(capacidad)
    llenos = threading.Semaphore(0)
    cola_spool = []

    insertadas = []
    impresas = []
    bloqueos_productores = 0
    lock_stats = threading.Lock()

    def hilo_productor(pedido_id: str, t_fin_m1: float):
        nonlocal bloqueos_productores
        # Esperar a que la cocina termine el plato
        time.sleep(t_fin_m1 * escala_s)

        # Intento no bloqueante previo para registrar si el spool esta saturado
        adquirido_inmediato = vacios.acquire(blocking=False)
        if not adquirido_inmediato:
            with lock_stats:
                bloqueos_productores += 1
            vacios.acquire()

        # Seccion critica protegida por mutex
        mutex.acquire()
        comanda = f'Comanda-{pedido_id}'
        cola_spool.append(comanda)
        with lock_stats:
            insertadas.append(comanda)
        mutex.release()
        llenos.release()

    def hilo_consumidor_impresora():
        while True:
            llenos.acquire()
            mutex.acquire()
            item = cola_spool.pop(0)
            mutex.release()
            vacios.release()

            if item is None:
                # Senal de cierre
                break

            # Simular impresion del ticket
            time.sleep(t_impresion_s)
            with lock_stats:
                impresas.append(item)

    # Lanzar hilo consumidor (impresora de comandas)
    t_impr = threading.Thread(target=hilo_consumidor_impresora, name='Impresora-Comandas')
    t_impr.start()

    # Lanzar hilos productores (uno por pedido)
    hilos_prod = []
    for p in conjunto_procesos:
        pid = p.id
        t_fin = metricas[pid].fin
        t_p = threading.Thread(
            target=hilo_productor,
            args=(pid, t_fin),
            name=f'Productor-{pid}'
        )
        hilos_prod.append(t_p)
        t_p.start()

    # Esperar a que todos los pedidos sean enviados al spool
    for t_p in hilos_prod:
        t_p.join()

    # Enviar senal centinela None para cerrar la impresora
    vacios.acquire()
    mutex.acquire()
    cola_spool.append(None)
    mutex.release()
    llenos.release()

    t_impr.join()

    return insertadas, impresas, bloqueos_productores


# ==============================================================================
# VERIFICACION Y PRUEBAS AUTOMATIZADAS (TABLA C Y CONTROL)
# ==============================================================================

def verificar():
    '''Bateria de pruebas requeridas por el plan del equipo (Tabla C y Spooling).'''
    resultados = []

    def anotar(nombre, cumple):
        resultados.append((nombre, bool(cumple)))

    # --- 1. Tabla C: Tiempos de Bufering y Cuello de Botella ---
    # Caso 1: Control PPT (n=5, L=10, P=6) -> Sin bufer=80, Doble=56, cuello=dispositivo
    t_c1_sin = tiempo_total(5, 10, 6, buffers=1)
    t_c1_dob = tiempo_total(5, 10, 6, buffers=2)
    q_c1 = cuello_botella(10, 6)
    anotar('Control PPT: 5 bloques, L=10, P=6 -> 80 ms sin bufer', t_c1_sin == 80)
    anotar('Control PPT: 5 bloques, L=10, P=6 -> 56 ms doble bufer', t_c1_dob == 56)
    anotar('Control PPT: cuello de botella es dispositivo', q_c1 == 'dispositivo')

    # Caso 2: Practica dirigida 1 (n=8, L=12, P=5) -> Sin bufer=136, Doble=101, cuello=dispositivo
    t_c2_sin = tiempo_total(8, 12, 5, buffers=1)
    t_c2_dob = tiempo_total(8, 12, 5, buffers=2)
    q_c2 = cuello_botella(12, 5)
    anotar('Practica dirigida 1: 8 bloques, L=12, P=5 -> 136 ms sin bufer', t_c2_sin == 136)
    anotar('Practica dirigida 1: 8 bloques, L=12, P=5 -> 101 ms doble bufer', t_c2_dob == 101)
    anotar('Practica dirigida 1: cuello de botella es dispositivo', q_c2 == 'dispositivo')

    # Caso 3: Practica dirigida 2 (n=8, L=5, P=12) -> Sin bufer=136, Doble=101, cuello=cpu
    t_c3_sin = tiempo_total(8, 5, 12, buffers=1)
    t_c3_dob = tiempo_total(8, 5, 12, buffers=2)
    q_c3 = cuello_botella(5, 12)
    anotar('Practica dirigida 2: 8 bloques, L=5, P=12 -> 136 ms sin bufer', t_c3_sin == 136)
    anotar('Practica dirigida 2: 8 bloques, L=5, P=12 -> 101 ms doble bufer', t_c3_dob == 101)
    anotar('Practica dirigida 2: cuello de botella es cpu', q_c3 == 'cpu')

    # Caso 4: Propio 1 (n=8, L=8, P=14) -> Sin bufer=176, Doble=120, cuello=cpu
    anotar('Propio 1: 8 bloques, L=8, P=14 -> 176 ms sin bufer', tiempo_total(8, 8, 14, buffers=1) == 176)
    anotar('Propio 1: 8 bloques, L=8, P=14 -> 120 ms doble bufer', tiempo_total(8, 8, 14, buffers=2) == 120)
    anotar('Propio 1: cuello de botella es cpu', cuello_botella(8, 14) == 'cpu')

    # Caso 5: Propio 2 (n=8, L=14, P=8) -> Sin bufer=176, Doble=120, cuello=dispositivo
    anotar('Propio 2: 8 bloques, L=14, P=8 -> 176 ms sin bufer', tiempo_total(8, 14, 8, buffers=1) == 176)
    anotar('Propio 2: 8 bloques, L=14, P=8 -> 120 ms doble bufer', tiempo_total(8, 14, 8, buffers=2) == 120)
    anotar('Propio 2: cuello de botella es dispositivo', cuello_botella(14, 8) == 'dispositivo')

    # Caso 6: Propio 3 (n=6, L=9, P=9) -> Sin bufer=108, Doble=63, cuello=equilibrado
    anotar('Propio 3: 6 bloques, L=9, P=9 -> 108 ms sin bufer', tiempo_total(6, 9, 9, buffers=1) == 108)
    anotar('Propio 3: 6 bloques, L=9, P=9 -> 63 ms doble bufer', tiempo_total(6, 9, 9, buffers=2) == 63)
    anotar('Propio 3: cuello de botella es equilibrado', cuello_botella(9, 9) == 'equilibrado')

    # --- 2. Invarianza con 3 y 4 buferes ---
    anotar('Invarianza: 3 buferes en Control PPT da 56 ms igual que con 2', tiempo_total(5, 10, 6, buffers=3) == 56)
    anotar('Invarianza: 4 buferes en Control PPT da 56 ms igual que con 2', tiempo_total(5, 10, 6, buffers=4) == 56)
    anotar('Invarianza: 3 buferes en Practica 1 da 101 ms igual que con 2', tiempo_total(8, 12, 5, buffers=3) == 101)
    anotar('Invarianza: 4 buferes en Practica 2 da 101 ms igual que con 2', tiempo_total(8, 5, 12, buffers=4) == 101)

    # --- 3. Spooling de Comandas ---
    # Conjunto Oficial (P1-P4) con capacidad amplia (5): sin bloqueos
    ins_p, imp_p, bloq_p = simular_spool(CONJUNTO_OFICIAL, capacidad=5, t_impresion_s=0.01, escala_s=0.01)
    anotar('Spool Oficial (P1-P4): 4 comandas impresas', len(imp_p) == 4)
    anotar('Spool Oficial: orden impresion coincide con insercion', ins_p == imp_p)
    anotar('Spool Oficial (cap=5): 0 bloqueos de productores', bloq_p == 0)

    # Conjunto Equipo (Q1-Q5) con capacidad amplia (5): sin bloqueos
    ins_q, imp_q, bloq_q = simular_spool(CONJUNTO_EQUIPO, capacidad=5, t_impresion_s=0.01, escala_s=0.01)
    anotar('Spool Equipo (Q1-Q5): 5 comandas impresas', len(imp_q) == 5)
    anotar('Spool Equipo: orden impresion coincide con insercion', ins_q == imp_q)
    anotar('Spool Equipo (cap=5): 0 bloqueos de productores', bloq_q == 0)

    # Bloqueos con capacidad saturada (capacidad=1, impresion lenta)
    _, _, bloq_sat_p = simular_spool(CONJUNTO_OFICIAL, capacidad=1, t_impresion_s=0.06, escala_s=0.005)
    anotar('Spool saturado (P1-P4, cap=1): detecta al menos 1 bloqueo', bloq_sat_p >= 1)

    _, _, bloq_sat_q = simular_spool(CONJUNTO_EQUIPO, capacidad=1, t_impresion_s=0.06, escala_s=0.005)
    anotar('Spool saturado (Q1-Q5, cap=1): detecta al menos 1 bloqueo', bloq_sat_q >= 1)

    return resultados


def main():
    print('=== VERIFICACION DE es_buffer_spooling.py (Rol R3: Leonel) ===')
    resultados = verificar()
    for nombre, cumple in resultados:
        print('[%s] %s' % ('OK' if cumple else 'FALLO', nombre))
    ok = sum(1 for _, c in resultados if c)
    total = len(resultados)
    print('Verificaciones correctas: %d/%d' % (ok, total))
    print('RESULTADO: %s' % ('OK' if ok == total else 'FALLO'))

    # Mostrar ejemplo del diagrama de texto de la practica dirigida
    print('\n' + diagrama_texto(5, 10, 6, buffers=2))
    return 0 if ok == total else 1


if __name__ == '__main__':
    raise SystemExit(main())

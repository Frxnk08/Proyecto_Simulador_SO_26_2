"""Modulo 3 - Comparacion Final de Estrategias de Gestion de Memoria.
Caso: CocinaPeru Express

Responsable: Persona 4 (Leonel)
Une y compara cuantitativa y conceptualmente las tres tecnicas de memoria:
1. Asignacion Contigua (Primer Ajuste / First-Fit) -> Fragmentacion Externa
2. Paginacion (Marcos no contiguos de 4 096 bytes)  -> Sin Fragmentacion Externa
3. Segmentacion (Base y Limite)                    -> Proteccion y SegmentFault

Este archivo genera una tabla comparativa en la terminal al ejecutar.
"""

from __future__ import annotations

import os
import sys

# Asegurar path para importar modulos hermanos
sys.path.insert(0, os.path.dirname(__file__))

from comun import (
    CONJUNTO_EQUIPO,
    CONJUNTO_OFICIAL,
    MEMORIA_TOTAL,
    TAM_PAGINA,
    eventos,
    intervalos,
)
import contigua
import segmentacion


def simular_paginacion(datos_conjunto):
    """Simula la asignacion de paginas a marcos libres para la comparacion."""
    marcos = ['.'] * MEMORIA_TOTAL
    lista_intervalos = intervalos(datos_conjunto)
    lista_eventos = eventos(lista_intervalos)
    asignaciones = {}
    rechazos = []

    for instante, tipo_evento, pid, tamano in lista_eventos:
        simbolo = pid[-1]
        if tipo_evento == 0:  # Salida
            if pid in asignaciones:
                for m in asignaciones[pid]:
                    marcos[m] = '.'
        else:  # Llegada
            # En paginacion no se requiere contiguidad, solo contar marcos libres
            libres = [idx for idx, val in enumerate(marcos) if val == '.']
            if len(libres) >= tamano:
                marcos_asignados = libres[:tamano]
                for m in marcos_asignados:
                    marcos[m] = simbolo
                asignaciones[pid] = marcos_asignados
            else:
                rechazos.append(pid)

    return asignaciones, rechazos


def ejecutar_comparacion():
    print("=" * 80)
    print("MODULO 3 - COMPARACION GENERAL DE ESTRATEGIAS DE MEMORIA")
    print("CocinaPeru Express - Torre de Control")
    print("=" * 80)

    # 1. Asignacion Contigua
    print("\n>>> 1. ASIGNACION CONTIGUA (Primer Ajuste / First-Fit)")
    rechazados_contigua_q = contigua.simular_asignacion_contigua("Conjunto Alternativo Q1-Q5", CONJUNTO_EQUIPO)
    rechazados_contigua_p = contigua.simular_asignacion_contigua("Conjunto de Control P1-P4", CONJUNTO_OFICIAL)

    # 2. Paginacion
    print("\n>>> 2. PAGINACION (Marcos no contiguos)")
    asig_q, rech_pag_q = simular_paginacion(CONJUNTO_EQUIPO)
    print("Simulacion con Q1-Q5:")
    for pid, marcos_asig in asig_q.items():
        print(f"  - {pid} asignado a marcos: {marcos_asig}")
    print(f"  - Pedidos rechazados: {rech_pag_q if rech_pag_q else 'Ninguno (Todos aceptados)'}")

    # 3. Segmentacion
    print("\n>>> 3. SEGMENTACION (Base y Limite con deteccion de Fallo de Proteccion)")
    segmentacion.imprimir_tabla(segmentacion.TABLA_SEGMENTOS)
    ejemplos_seg = [
        ((0, 100), "Acceso valido a codigo"),
        ((1, 300), "Acceso valido a datos"),
        ((1, 900), "Desbordamiento de datos (900 >= 800) -> Segmentation Fault"),
        ((2, 300), "Fuera de limite de pila (300 >= 300) -> Segmentation Fault"),
    ]
    print("\nTraducciones representativas:")
    for (seg, des), descripcion in ejemplos_seg:
        try:
            fis = segmentacion.traducir(segmentacion.TABLA_SEGMENTOS, seg, des)
            print(f"  - ({seg}, {des:3d}) -> Dir. Fisica: {fis:4d} | {descripcion}")
        except segmentacion.ErrorProteccion as e:
            print(f"  - ({seg}, {des:3d}) -> TRAP ERROR : {e}")

    # 4. Tabla Comparativa Final (Seccion 7 del informe)
    print("\n" + "=" * 80)
    print("TABLA COMPARATIVA FINAL DE ESTRATEGIAS (SECCION 7)")
    print("=" * 80)
    print(f"{'Criterio / Caracteristica':<30}{'Asignacion Contigua':<22}{'Paginacion':<20}{'Segmentacion':<18}")
    print("-" * 90)
    print(f"{'Unidad de memoria':<30}{'Bloque continuo':<22}{'Paginas fijas (4 KB)':<20}{'Segmentos variables':<18}")
    print(f"{'Fragmentacion externa':<30}{'SI (Q5 rechazado)':<22}{'NO (Totalmente nula)':<20}{'SI (Entre huecos)':<18}")
    print(f"{'Fragmentacion interna':<30}{'NO (Exacto)':<22}{'SI (Ultima pagina)':<20}{'NO':<18}")
    print(f"{'Soporta no contiguidad':<30}{'NO':<22}{'SI (Cualquier marco)':<20}{'SI (Por segmento)':<18}")
    print(f"{'Comportamiento con Q1-Q5':<30}{'Rechaza Q5 en t=6':<22}{'Acepta todos (Q1-Q5)':<20}{'No simula tiempo':<18}")
    print(f"{'Comportamiento con P1-P4':<30}{'Acepta todos':<22}{'Acepta todos':<20}{'No simula tiempo':<18}")
    print(f"{'Proteccion / Aislamiento':<30}{'Por registro limite':<22}{'Bit Validez (PageFault)':<20}{'Limite (SegFault)':<18}")
    print("-" * 90)

    # 5. Justificacion conceptual para la sustentacion oral
    print("\n" + "=" * 80)
    print("PREGUNTAS CLAVE PARA LA SUSTENTACION ORAL (PERSONA 4)")
    print("=" * 80)
    print("1. De donde salen llegada y fin?")
    print("   -> Llegada: Instante en que el mostrador crea el pedido.")
    print("   -> Fin: Calculado por FCFS (llegada + espera + duracion).\n")
    print("2. Por que se usa FCFS para la memoria?")
    print("   -> Modela el orden natural de cocina: primer pedido en llegar se prepara")
    print("      sin interrupcion y ocupa estantes hasta finalizar su coccion.\n")
    print("3. Por que P1-P4 no muestra fragmentacion externa?")
    print("   -> Todos (P1 a P4) llegan antes de t=3 y el primero sale en t=5.")
    print("      Los estantes se llenan secuencialmente sin huecos intermedios.")
    print("      En cambio, en Q1-Q5, Q1 sale en t=4 liberando los estantes 0-1,")
    print("      y cuando Q5 llega en t=6 pidiendo 3 estantes, los 3 estantes libres")
    print("      estan dispersos (0, 1 y 9), haciendo imposible ubicar 3 contiguos.")
    print("=" * 80)


if __name__ == "__main__":
    ejecutar_comparacion()


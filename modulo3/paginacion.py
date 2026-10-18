"""Modulo 3 - Paginacion.
Caso: CocinaPeru Express

Simula la asignacion de paginas a marcos y traduce direcciones virtuales.
"""

from __future__ import annotations

from comun import (
    CONJUNTO_EQUIPO,
    CONJUNTO_OFICIAL,
    MEMORIA_TOTAL,
    TAM_PAGINA,
    eventos,
    intervalos,
)


def simular(procesos):
    """Devuelve tablas historicas, rechazados y traza de eventos del conjunto."""
    ocupados = [None] * MEMORIA_TOTAL
    activos = {}
    tablas = {}
    rechazados = []
    traza = []

    for instante, tipo, pedido, tamano in eventos(intervalos(procesos)):
        if tipo == 0:
            if pedido in activos:
                for marco in activos.pop(pedido).values():
                    ocupados[marco] = None
                traza.append(f"t={instante}: sale {pedido}; libera sus marcos")
            continue

        libres = [marco for marco, ocupante in enumerate(ocupados) if ocupante is None]
        if len(libres) < tamano:
            rechazados.append(pedido)
            traza.append(f"t={instante}: {pedido} RECHAZADO ({tamano} paginas, {len(libres)} marcos libres)")
            continue

        tabla = dict(enumerate(libres[:tamano]))
        for marco in tabla.values():
            ocupados[marco] = pedido
        activos[pedido] = tabla
        tablas[pedido] = tabla.copy()
        traza.append(f"t={instante}: entra {pedido}; " + ", ".join(
            f"pagina {pagina} -> marco {marco}" for pagina, marco in tabla.items()
        ))

    return tablas, rechazados, traza


def traducir(tabla, direccion_virtual):
    """Devuelve (pagina, desplazamiento, marco, direccion_fisica)."""
    if direccion_virtual < 0:
        raise ValueError("La direccion virtual no puede ser negativa")
    pagina = direccion_virtual // TAM_PAGINA
    desplazamiento = direccion_virtual % TAM_PAGINA
    if pagina not in tabla:
        raise ValueError(f"La pagina {pagina} no existe en la tabla")
    marco = tabla[pagina]
    return pagina, desplazamiento, marco, marco * TAM_PAGINA + desplazamiento


def fragmentacion_interna(tamano_bytes):
    """Devuelve (paginas, espacio_reservado, bytes_desperdiciados)."""
    if tamano_bytes < 0:
        raise ValueError("El tamano en bytes no puede ser negativo")
    paginas = (tamano_bytes + TAM_PAGINA - 1) // TAM_PAGINA
    reservado = paginas * TAM_PAGINA
    return paginas, reservado, reservado - tamano_bytes


def mostrar_conjunto(nombre, procesos):
    print(f"\n=== PAGINACION: {nombre} ===")
    tablas, rechazados, traza = simular(procesos)
    for linea in traza:
        print(linea)
    print(f"Rechazados: {rechazados if rechazados else 'ninguno'}")
    return tablas, rechazados


def main():
    correctas = []

    def verificar(nombre, cumple):
        print(f"[{'OK' if cumple else 'FALLO'}] {nombre}")
        correctas.append(cumple)

    tablas_q, rechazados_q = mostrar_conjunto("Q1-Q5", CONJUNTO_EQUIPO)
    verificar("Q1-Q5: Q5 aceptado y ningun rechazo", not rechazados_q and "Q5" in tablas_q)
    verificar("Q1-Q4: marcos esperados", all(
        list(tablas_q[pedido].values()) == marcos for pedido, marcos in {
            "Q1": [0, 1], "Q2": [2, 3], "Q3": [4, 5], "Q4": [0, 1, 6]
        }.items()
    ))
    verificar("Q5: paginas 0,1,2 -> marcos 7,8,9", tablas_q.get("Q5") == {0: 7, 1: 8, 2: 9})

    tablas_p, rechazados_p = mostrar_conjunto("P1-P4", CONJUNTO_OFICIAL)
    verificar("P1-P4: todos aceptados", not rechazados_p and len(tablas_p) == 4)

    print("\n=== TRADUCCION DE DIRECCION ===")
    tabla_ejemplo = {0: 5, 1: 2, 2: 7, 3: 0}
    pagina, desplazamiento, marco, fisica = traducir(tabla_ejemplo, 10000)
    print(f"Virtual 10000: pagina={pagina}, desplazamiento={desplazamiento}, "
          f"marco={marco}, fisica={fisica}")
    verificar("10000 -> pagina 2, offset 1808, marco 7, fisica 30480",
             (pagina, desplazamiento, marco, fisica) == (2, 1808, 7, 30480))
    for direccion, tabla, nombre in ((-1, tabla_ejemplo, "direccion negativa"),
                                     (4 * TAM_PAGINA, tabla_ejemplo, "pagina inexistente")):
        try:
            traducir(tabla, direccion)
        except ValueError as error:
            print(f"Error esperado: {error}")
            verificar(nombre, True)
        else:
            verificar(nombre, False)

    paginas, reservado, desperdicio = fragmentacion_interna(10000)
    print(f"\n10000 bytes: {paginas} paginas, {reservado} bytes reservados, "
          f"{desperdicio} bytes de fragmentacion interna")
    verificar("fragmentacion interna: 2288 bytes", (paginas, reservado, desperdicio) == (3, 12288, 2288))
    return 0 if all(correctas) else 1


if __name__ == "__main__":
    raise SystemExit(main())

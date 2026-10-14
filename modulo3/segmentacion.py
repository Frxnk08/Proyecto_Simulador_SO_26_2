"""Modulo 3 - Segmentacion (base y limite) - Rincon del Sabor.

Cada pedido se divide en segmentos (codigo, datos, pila). La direccion logica
es (segmento, desplazamiento). Es valida solo si el desplazamiento es menor que
el limite del segmento; la direccion fisica es base + desplazamiento. Si no se
cumple, se produce un error de proteccion.
"""

# Tabla de segmentos: numero -> nombre, base (donde empieza en memoria) y limite (tamano)
TABLA_SEGMENTOS = {
    0: {"nombre": "codigo", "base": 1000, "limite": 400},
    1: {"nombre": "datos", "base": 5200, "limite": 800},
    2: {"nombre": "pila", "base": 9000, "limite": 300},
}


class ErrorProteccion(Exception):
    """Direccion fuera del limite del segmento, o segmento que no existe."""


def traducir(tabla, segmento, desplazamiento):
    """Devuelve la direccion fisica de (segmento, desplazamiento) o lanza ErrorProteccion."""
    if segmento not in tabla:
        raise ErrorProteccion(f"el segmento {segmento} no existe")
    seg = tabla[segmento]
    if desplazamiento < 0 or desplazamiento >= seg["limite"]:
        raise ErrorProteccion(
            f"desplazamiento {desplazamiento} fuera del limite {seg['limite']} "
            f"del segmento {segmento} ({seg['nombre']})"
        )
    return seg["base"] + desplazamiento


def imprimir_tabla(tabla):
    print("=== TABLA DE SEGMENTOS ===")
    print(f"{'Seg':<5}{'Nombre':<10}{'Base':>7}{'Limite':>9}")
    print("-" * 31)
    for numero, seg in tabla.items():
        print(f"{numero:<5}{seg['nombre']:<10}{seg['base']:>7}{seg['limite']:>9}")


def main():
    imprimir_tabla(TABLA_SEGMENTOS)

    # ((segmento, desplazamiento), direccion fisica esperada; None = debe dar error)
    pruebas = [
        ((0, 100), 1100),
        ((1, 300), 5500),
        ((1, 900), None),   # supera el limite de 800
        ((2, 300), None),   # igual al limite de 300: tambien es invalido
        ((2, 299), 9299),   # ultimo desplazamiento valido de la pila
        ((5, 0), None),     # segmento inexistente
    ]

    print("\n=== TRADUCCIONES ===")
    correctas = 0
    for (seg, des), esperado in pruebas:
        try:
            fisica = traducir(TABLA_SEGMENTOS, seg, des)
            detalle = f"direccion fisica = {fisica}"
        except ErrorProteccion as error:
            fisica = None
            detalle = f"ERROR DE PROTECCION: {error}"
        estado = "OK" if fisica == esperado else "FALLO"
        if estado == "OK":
            correctas += 1
        print(f"({seg}, {des:>3}) -> {detalle}  [{estado}]")

    print(f"\nPruebas correctas: {correctas}/{len(pruebas)}")
    if correctas == len(pruebas):
        print("RESULTADO: OK - todas las traducciones coinciden con lo esperado")
    else:
        print("RESULTADO: FALLO - revisar las traducciones marcadas")


if __name__ == "__main__":
    main()
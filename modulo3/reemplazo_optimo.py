"""Modulo 3 - Algoritmo de Reemplazo de Paginas: Optimo (Belady / MIN).
Caso: CocinaPeru Express

Responsable: Persona 3 (Leonel)
Implementa el algoritmo de reemplazo Optimo:
- Ante un fallo de pagina cuando los marcos estan llenos, busca la pagina
  en memoria cuyo proximo uso este mas lejos en el futuro o que nunca mas
  vuelva a usarse.
- En caso de empate, la victima es la pagina que lleva mas tiempo en memoria (criterio FIFO).
"""

from __future__ import annotations

# Cadenas de referencia estandar acordadas en la Seccion 5.1
CLASE = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
TALLER = [2, 3, 2, 1, 5, 2, 4, 5, 3, 2, 5, 2, 6, 1, 3, 6]
BELADY = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]


def simular(refs: list[int | str], marcos: int) -> tuple[int, list[tuple[int | str, list[int | str], bool]]]:
    """Simula el reemplazo de paginas con politica Optima.

    Devuelve: (fallos, traza)
    traza = lista de (pagina, marcos_tras_el_paso, fue_fallo)
    marcos_tras_el_paso = lista COPIADA de las paginas en memoria.
    """
    if marcos <= 0:
        raise ValueError("La cantidad de marcos debe ser mayor a 0.")

    memoria: list[int | str] = []
    traza: list[tuple[int | str, list[int | str], bool]] = []
    fallos = 0

    for i, p in enumerate(refs):
        if p in memoria:
            # Acierto: la pagina ya esta cargada en RAM
            traza.append((p, list(memoria), False))
        else:
            # Fallo de pagina
            fallos += 1
            if len(memoria) < marcos:
                memoria.append(p)
            else:
                # Seleccionar victima mirando hacia el futuro (refs[i+1:])
                futuro = refs[i + 1:]
                peor_indice_futuro = -1
                victima = memoria[0]

                for pag in memoria:
                    if pag not in futuro:
                        # Nunca mas se vuelve a usar: es la victima ideal
                        victima = pag
                        break
                    else:
                        proximo_uso = futuro.index(pag)
                        if proximo_uso > peor_indice_futuro:
                            peor_indice_futuro = proximo_uso
                            victima = pag

                idx_victima = memoria.index(victima)
                memoria[idx_victima] = p

            traza.append((p, list(memoria), True))

    return fallos, traza


def imprimir_traza(refs: list[int | str], marcos: int, traza: list[tuple[int | str, list[int | str], bool]], titulo: str = "") -> None:
    """Formato de impresion de traza acordado en la Seccion 5.2."""
    print(f"=== {titulo} (marcos={marcos}) ===")
    print(f"{'Ref':<5}| {'Marcos':<17} | Resultado")
    print("-" * 40)
    for pagina, en_marcos, fallo in traza:
        resultado_str = "FALLO" if fallo else "acierto"
        print(f"{str(pagina):<5}| {str(en_marcos):<17} | {resultado_str}")
    fallos = sum(1 for _, _, f in traza if f)
    total = len(refs)
    tasa_aciertos = 100 * (total - fallos) / total if total > 0 else 0
    print(f"Fallos: {fallos} | Aciertos: {total - fallos} | Tasa de aciertos: {tasa_aciertos:.1f}%\n")


if __name__ == "__main__":
    print("=========================================================")
    print("VERIFICACION OFICIAL: ALGORITMO OPTIMO (PERSONA 3)")
    print("=========================================================\n")

    # Pruebas obligatorias contra la Seccion 4 del documento
    VERIFICACIONES = [
        ("Clase", CLASE, 3, 9),
        ("Taller", TALLER, 3, 8),
        ("Taller", TALLER, 4, 7),
        ("Belady", BELADY, 3, 7),
        ("Belady", BELADY, 4, 6),
    ]

    todos_ok = True
    for nombre, cadena, m, esperado in VERIFICACIONES:
        fallos, traza = simular(cadena, m)
        cumple = (fallos == esperado)
        estado = "OK" if cumple else "FALLO"
        print(f"[{estado}] Cadena {nombre:<6} ({len(cadena)} refs, {m} marcos): Fallos={fallos} (esperado {esperado})")
        if not cumple:
            todos_ok = False

    print("\n---------------------------------------------------------")
    if todos_ok:
        print("=> RESULTADO: Todos los valores de referencia coinciden al 100%.")
    else:
        print("=> ADVERTENCIA: Hubo discrepancias en los valores esperados.")
    print("---------------------------------------------------------\n")

    # Mostrar la traza detallada de la Cadena de Clase con 3 marcos
    _, traza_demo = simular(CLASE, 3)
    imprimir_traza(CLASE, 3, traza_demo, titulo="TRAZA DETALLADA: Cadena de Clase")

"""Modulo 3 - Reemplazo de paginas LRU.
Caso: CocinaPeru Express
"""

from __future__ import annotations

CLASE = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
TALLER = [2, 3, 2, 1, 5, 2, 4, 5, 3, 2, 5, 2, 6, 1, 3, 6]
BELADY = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]


def simular(refs: list[int | str], marcos: int) -> tuple[int, list[tuple[int | str, list[int | str], bool]]]:
    """Simula LRU; memoria va de menos reciente a mas reciente."""
    if marcos <= 0:
        raise ValueError("La cantidad de marcos debe ser mayor a 0.")

    memoria: list[int | str] = []
    traza: list[tuple[int | str, list[int | str], bool]] = []
    fallos = 0
    for pagina in refs:
        fue_fallo = pagina not in memoria
        if fue_fallo:
            fallos += 1
            if len(memoria) == marcos:
                memoria.pop(0)
        else:
            memoria.remove(pagina)
        memoria.append(pagina)
        traza.append((pagina, memoria.copy(), fue_fallo))
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


def main():
    verificaciones = [
        ("Clase", CLASE, 3, 12),
        ("Taller", TALLER, 3, 10),
        ("Taller", TALLER, 4, 9),
        ("Belady", BELADY, 3, 10),
        ("Belady", BELADY, 4, 8),
    ]
    correctas = []
    for nombre, refs, marcos, esperado in verificaciones:
        fallos, _ = simular(refs, marcos)
        cumple = fallos == esperado
        correctas.append(cumple)
        print(f"[{'OK' if cumple else 'FALLO'}] {nombre}, {marcos} marcos: "
              f"{fallos} fallos (esperado {esperado})")

    sin_anomalia = simular(BELADY, 4)[0] <= simular(BELADY, 3)[0]
    correctas.append(sin_anomalia)
    print(f"[{'OK' if sin_anomalia else 'FALLO'}] LRU sin anomalia de Belady")
    _, traza = simular(TALLER, 3)
    print()
    imprimir_traza(TALLER, 3, traza, "TRAZA DETALLADA: Cadena del Taller")
    return 0 if all(correctas) else 1


if __name__ == "__main__":
    raise SystemExit(main())

CLASE = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
TALLER = [2, 3, 2, 1, 5, 2, 4, 5, 3, 2, 5, 2, 6, 1, 3, 6]
BELADY = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]


def simular(refs, marcos):
    """Devuelve (fallos, traza).

    traza = lista de (pagina, marcos_tras_el_paso, fue_fallo)
    marcos_tras_el_paso = lista COPIADA de las paginas en memoria.
    """
    memoria = []
    traza = []
    fallos = 0

    for pag in refs:
        if pag in memoria:
            fue_fallo = False
        else:
            fue_fallo = True
            fallos += 1
            if len(memoria) < marcos:
                memoria.append(pag)
            else:
                memoria.pop(0)
                memoria.append(pag)

        traza.append((pag, list(memoria), fue_fallo))

    return fallos, traza


def imprimir_traza(refs, marcos, traza, titulo):
    print(f"=== {titulo} (marcos={marcos}) ===")
    print("Ref  | Marcos           | Resultado")
    print("-" * 40)
    for pagina, en_marcos, fallo in traza:
        print(
            f"{str(pagina):<5}| {str(en_marcos):<17}| {'FALLO' if fallo else 'acierto'}"
        )
    fallos = sum(1 for _, _, f in traza if f)
    total = len(refs)
    print(
        f"Fallos: {fallos} | Aciertos: {total - fallos} | Tasa de aciertos:"
        f" {100 * (total - fallos) / total:.1f}%"
    )


if __name__ == "__main__":
    _, traza_taller_3 = simular(TALLER, 3)
    imprimir_traza(TALLER, 3, traza_taller_3, "FIFO - Taller")
    print()

    VERIFICACIONES = [
        ("clase", CLASE, 3, 15),
        ("taller", TALLER, 3, 12),
        ("taller", TALLER, 4, 9),
    ]

    print("=== VERIFICACIONES FIFO ===")
    for nombre, cadena, marcos, esperado in VERIFICACIONES:
        fallos, _ = simular(cadena, marcos)
        estado = "OK" if fallos == esperado else "FALLO"
        print(
            f"{nombre} con {marcos} marcos: {fallos} fallos (esperado"
            f" {esperado}) -> {estado}"
        )
    print()

    print("=== DEMOSTRACION ANOMALIA DE BELADY ===")
    fallos_b3, _ = simular(BELADY, 3)
    fallos_b4, _ = simular(BELADY, 4)
    print(f"Belady con 3 marcos: {fallos_b3} fallos (esperado 9)")
    print(f"Belady con 4 marcos: {fallos_b4} fallos (esperado 10)")

    if fallos_b4 > fallos_b3:
        print("ANOMALIA: mas marcos, mas fallos")
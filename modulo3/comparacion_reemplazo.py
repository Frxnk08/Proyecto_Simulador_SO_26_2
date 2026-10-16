"""Modulo 3 - Comparacion de algoritmos de reemplazo de paginas (FIFO, LRU, Optimo).

Carga los algoritmos que esten en la carpeta (reemplazo_fifo.py, reemplazo_lru.py,
reemplazo_optimo.py) y la cadena de la cocina (reemplazo_cocina.py). Lo que falte
se avisa como "aun no disponible" y el script sigue; nunca se cae por un archivo
ausente. Al final verifica contra los valores de referencia del Word (seccion 4).

Los textos impresos van sin tildes para que la consola de Windows no los rompa.
"""

import importlib

CLASE = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
TALLER = [2, 3, 2, 1, 5, 2, 4, 5, 3, 2, 5, 2, 6, 1, 3, 6]
BELADY = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]

ALGORITMOS = [("FIFO", "reemplazo_fifo"), ("LRU", "reemplazo_lru"), ("Optimo", "reemplazo_optimo")]

# Valores de referencia (fallos de pagina) de la seccion 4 del Word
REFERENCIA_PPT = [
    ("Clase", CLASE, 3, {"FIFO": 15, "LRU": 12, "Optimo": 9}),
    ("Taller", TALLER, 3, {"FIFO": 12, "LRU": 10, "Optimo": 8}),
    ("Taller", TALLER, 4, {"FIFO": 9, "LRU": 9, "Optimo": 7}),
    ("Belady", BELADY, 3, {"FIFO": 9, "LRU": 10, "Optimo": 7}),
    ("Belady", BELADY, 4, {"FIFO": 10, "LRU": 8, "Optimo": 6}),
]
MARCOS_COCINA = (3, 4, 5, 6)
REFERENCIA_COCINA = {
    "oficial": {"FIFO": [16, 16, 16, 16], "LRU": [16, 16, 16, 14], "Optimo": [14, 13, 12, 11]},
    "equipo": {"FIFO": [14, 14, 14, 14], "LRU": [14, 14, 14, 13], "Optimo": [13, 12, 11, 11]},
}


def cargar_algoritmos():
    """Devuelve {nombre: simular} con los algoritmos que se puedan importar."""
    disponibles = {}
    for nombre, modulo in ALGORITMOS:
        try:
            disponibles[nombre] = importlib.import_module(modulo).simular
        except Exception as error:
            print(f"[aviso] {nombre}: aun no disponible ({modulo}.py: {error})")
    return disponibles


def calcular(algoritmos, refs, marcos):
    """Devuelve {nombre: fallos}; None si ese algoritmo fallo al ejecutarse."""
    resultado = {}
    for nombre, simular in algoritmos.items():
        try:
            resultado[nombre] = simular(refs, marcos)[0]
        except Exception as error:
            print(f"[aviso] {nombre} fallo con {marcos} marcos: {error}")
            resultado[nombre] = None
    return resultado


def brecha(fallos, optimo):
    if fallos is None or optimo is None or optimo <= 0:
        return "n/d"
    return f"+{100 * (fallos - optimo) / optimo:.1f}%"


def tabla_comparativa(titulo, refs, marcos, algoritmos):
    """Fallos, tasa de aciertos y brecha frente al Optimo para una cadena y un numero de marcos."""
    resultado = calcular(algoritmos, refs, marcos)
    total = len(refs)
    optimo = resultado.get("Optimo")
    print(f"\n{titulo} ({total} referencias, {marcos} marcos)")
    print(f"{'Algoritmo':<10}{'Fallos':>8}{'Aciertos':>11}{'Brecha vs Optimo':>20}")
    print("-" * 49)
    for nombre, _ in ALGORITMOS:
        fallos = resultado.get(nombre)
        if fallos is None:
            print(f"{nombre:<10}{'aun no disponible':>38}")
            continue
        aciertos = 100 * (total - fallos) / total
        columna = "-" if nombre == "Optimo" else brecha(fallos, optimo)
        print(f"{nombre:<10}{fallos:>8}{aciertos:>10.1f}%{columna:>20}")
    return resultado


def tabla_belady(algoritmos):
    """Cadena de Belady con 3 y 4 marcos; marca la anomalia (mas marcos, mas fallos)."""
    con3 = calcular(algoritmos, BELADY, 3)
    con4 = calcular(algoritmos, BELADY, 4)
    print(f"\n(c) Anomalia de Belady ({len(BELADY)} referencias)")
    print(f"{'Algoritmo':<10}{'3 marcos':>10}{'4 marcos':>10}   Resultado")
    print("-" * 52)
    for nombre, _ in ALGORITMOS:
        f3, f4 = con3.get(nombre), con4.get(nombre)
        if f3 is None or f4 is None:
            print(f"{nombre:<10}{'aun no disponible':>20}")
            continue
        if f4 > f3:
            veredicto = "ANOMALIA: mas marcos, mas fallos"
        else:
            veredicto = "sin anomalia"
        print(f"{nombre:<10}{f3:>10}{f4:>10}   {veredicto}")
    return con3, con4


def tabla_cocina(algoritmos):
    """Cadena de la cocina (Round Robin q=4) con 3, 4, 5 y 6 marcos. Devuelve {conjunto: {alg: [fallos]}}."""
    try:
        cadena_cocina = importlib.import_module("reemplazo_cocina").cadena_cocina
    except Exception as error:
        print(f"\n[aviso] (d) cadena de la cocina: aun no disponible (reemplazo_cocina.py: {error})")
        return {}

    obtenido = {}
    for conjunto in ("oficial", "equipo"):
        refs = cadena_cocina(conjunto)
        obtenido[conjunto] = {}
        print(f"\n(d) Cadena de la cocina, conjunto {conjunto} ({len(refs)} referencias, "
              f"{len(set(refs))} paginas distintas)")
        print(f"{'Algoritmo':<10}" + "".join(f"{str(m) + ' marcos':>11}" for m in MARCOS_COCINA))
        print("-" * (10 + 11 * len(MARCOS_COCINA)))
        por_marcos = [calcular(algoritmos, refs, m) for m in MARCOS_COCINA]
        for nombre, _ in ALGORITMOS:
            if nombre not in algoritmos:
                print(f"{nombre:<10}{'aun no disponible':>28}")
                continue
            valores = [resultado.get(nombre) for resultado in por_marcos]
            obtenido[conjunto][nombre] = valores
            print(f"{nombre:<10}" + "".join(f"{('-' if v is None else v):>11}" for v in valores))
    return obtenido


def verificar(obtenido_ppt, obtenido_cocina, algoritmos):
    """Compara contra los valores de referencia y cierra con una linea RESULTADO."""
    print("\n=== VERIFICACION CONTRA LOS VALORES DE REFERENCIA ===")
    correctas = total = 0
    for nombre_cadena, _, marcos, esperado in REFERENCIA_PPT:
        obtenido = obtenido_ppt.get((nombre_cadena, marcos), {})
        for nombre, valor_esperado in esperado.items():
            if obtenido.get(nombre) is None:
                continue
            total += 1
            if obtenido[nombre] == valor_esperado:
                correctas += 1
            else:
                print(f"[FALLO] {nombre_cadena}, {marcos} marcos, {nombre}: "
                      f"obtenido {obtenido[nombre]} | esperado {valor_esperado}")
    for conjunto, por_algoritmo in obtenido_cocina.items():
        for nombre, valores in por_algoritmo.items():
            if not valores or None in valores:
                continue
            total += 1
            esperado = REFERENCIA_COCINA[conjunto][nombre]
            if valores == esperado:
                correctas += 1
            else:
                print(f"[FALLO] Cocina {conjunto}, {nombre}: obtenido {valores} | esperado {esperado}")

    faltan = [nombre for nombre, _ in ALGORITMOS if nombre not in algoritmos]
    print(f"Verificaciones correctas: {correctas}/{total}")
    if correctas != total:
        print("RESULTADO: FALLO - hay valores que no coinciden con la referencia")
    elif faltan or not obtenido_cocina:
        pendientes = faltan + ([] if obtenido_cocina else ["cadena de la cocina"])
        print(f"RESULTADO: PARCIAL - todo lo disponible coincide; falta: {', '.join(pendientes)}")
    else:
        print("RESULTADO: OK - todos los valores coinciden con la referencia")


def main():
    print("=== COMPARACION DE ALGORITMOS DE REEMPLAZO DE PAGINAS ===")
    algoritmos = cargar_algoritmos()
    print(f"Algoritmos disponibles: {', '.join(algoritmos) if algoritmos else 'ninguno'}")

    obtenido_ppt = {}
    obtenido_ppt[("Clase", 3)] = tabla_comparativa("(a) Cadena de clase", CLASE, 3, algoritmos)
    for marcos in (3, 4):
        obtenido_ppt[("Taller", marcos)] = tabla_comparativa("(b) Cadena del taller", TALLER, marcos, algoritmos)
    obtenido_ppt[("Belady", 3)], obtenido_ppt[("Belady", 4)] = tabla_belady(algoritmos)
    obtenido_cocina = tabla_cocina(algoritmos)

    verificar(obtenido_ppt, obtenido_cocina, algoritmos)


if __name__ == "__main__":
    main()
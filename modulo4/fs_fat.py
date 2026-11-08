"""Modulo 4 (semana 10) - Tabla FAT mediante un diccionario.
Caso: DeliFIIS. Rol 3: recorrido, asignacion, liberacion y dimensionamiento.
"""

from __future__ import annotations

from fs_comun import CONTROL, FAT_CONTROL, imprimir_verificaciones

FIN = "FIN"


def _validar_bloque(numero):
    if not isinstance(numero, int) or isinstance(numero, bool) or numero < 0:
        raise ValueError("El numero de cluster debe ser un entero no negativo")


def cadena(fat, inicio):
    """Devuelve la cadena desde inicio hasta FIN y detecta inconsistencias."""
    _validar_bloque(inicio)
    recorrido = []
    visitados = set()
    actual = inicio
    while True:
        if actual in visitados:
            raise ValueError("Ciclo detectado en la FAT")
        if actual not in fat:
            raise ValueError("Cluster sin entrada FAT: %d" % actual)
        visitados.add(actual)
        recorrido.append(actual)
        siguiente = fat[actual]
        if siguiente == FIN:
            return recorrido
        _validar_bloque(siguiente)
        actual = siguiente


def asignar_cadena(fat, bloques):
    """Reserva los bloques indicados y devuelve el primero de la cadena."""
    bloques = list(bloques)
    if not bloques:
        raise ValueError("Se necesita al menos un cluster")
    for numero in bloques:
        _validar_bloque(numero)
    if len(set(bloques)) != len(bloques):
        raise ValueError("La cadena no puede repetir clusters")
    ocupados = [numero for numero in bloques if numero in fat]
    if ocupados:
        raise ValueError("Clusters ya ocupados: %s" % ocupados)
    for posicion, numero in enumerate(bloques):
        fat[numero] = bloques[posicion + 1] if posicion + 1 < len(bloques) else FIN
    return bloques[0]


def liberar_cadena(fat, inicio):
    """Valida y libera una cadena completa; devuelve los clusters liberados."""
    recorrido = cadena(fat, inicio)
    for numero in recorrido:
        del fat[numero]
    return recorrido


def calcular_fat(disco_bytes, cluster_bytes, bytes_por_entrada):
    """Calcula cantidad de clusters y bytes de FAT a partir de sus tamanos."""
    valores = (disco_bytes, cluster_bytes, bytes_por_entrada)
    if any(not isinstance(v, int) or isinstance(v, bool) or v <= 0 for v in valores):
        raise ValueError("Los tamanos deben ser enteros positivos")
    entradas = (disco_bytes + cluster_bytes - 1) // cluster_bytes
    return entradas, entradas * bytes_por_entrada


def ejemplo_cinco_clusters():
    """Construye y libera la cadena propia 1 -> 4 -> 6 -> 3 -> 8 -> FIN."""
    fat = {}
    bloques = [1, 4, 6, 3, 8]
    inicio = asignar_cadena(fat, bloques)
    recorrido = cadena(fat, inicio)
    liberados = liberar_cadena(fat, inicio)
    return bloques, recorrido, liberados, fat


def verificar():
    disco_8gb = 8 * 1024 ** 3
    cluster_4kb = 4 * 1024
    entradas, tamano = calcular_fat(disco_8gb, cluster_4kb, 4)
    bloques, recorrido, liberados, fat_final = ejemplo_cinco_clusters()

    try:
        cadena({1: 2, 2: 1}, 1)
        ciclo_rechazado = False
    except ValueError:
        ciclo_rechazado = True
    try:
        cadena({1: 2}, 1)
        faltante_rechazado = False
    except ValueError:
        faltante_rechazado = True
    try:
        asignar_cadena({4: FIN}, [3, 4])
        ocupado_rechazado = False
    except ValueError:
        ocupado_rechazado = True

    return [
        ("FAT_CONTROL desde 4 produce [4, 7, 2]",
         cadena(FAT_CONTROL, 4) == [4, 7, 2]),
        ("FAT_CONTROL desde 9 produce [9]", cadena(FAT_CONTROL, 9) == [9]),
        ("8 GB / 4 KB produce 2097152 entradas", entradas == 2097152),
        ("FAT de 4 bytes por entrada ocupa 8388608 bytes", tamano == 8388608),
        ("tamano calculado de FAT coincide con el control",
         (entradas, tamano) == CONTROL["fat_8gb"]),
        ("8388608 bytes equivalen a 8 MB", tamano // (1024 ** 2) == 8),
        ("ejemplo propio asigna cinco clusters", bloques == [1, 4, 6, 3, 8]),
        ("ejemplo propio se recorre en el orden asignado", recorrido == bloques),
        ("liberacion devuelve los cinco clusters", liberados == bloques),
        ("tras liberar, todas las entradas quedan disponibles", fat_final == {}),
        ("una cadena ciclica es rechazada", ciclo_rechazado),
        ("una referencia FAT faltante es rechazada", faltante_rechazado),
        ("la asignacion rechaza clusters ocupados sin sobrescribirlos",
         ocupado_rechazado),
    ]


def main():
    print("=== TABLA FAT - DeliFIIS ===")
    print("FAT_CONTROL desde 4: %s" % cadena(FAT_CONTROL, 4))
    print("FAT_CONTROL desde 9: %s" % cadena(FAT_CONTROL, 9))

    entradas, tamano = calcular_fat(8 * 1024 ** 3, 4 * 1024, 4)
    print("\nDisco: 8 GB | Cluster: 4 KB | Entrada FAT: 4 bytes")
    print("Entradas: %d" % entradas)
    print("Tamano FAT: %d bytes (%d MB)" % (tamano, tamano // (1024 ** 2)))

    bloques, recorrido, liberados, fat_final = ejemplo_cinco_clusters()
    print("\nEjemplo propio: %s -> FIN" % " -> ".join(map(str, bloques)))
    print("Recorrido: %s" % recorrido)
    print("Liberados: %s | FAT final: %s" % (liberados, fat_final))

    print("\n=== VERIFICACION ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())

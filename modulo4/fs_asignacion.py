"""Modulo 4 (semana 10) - Metodos de asignacion de archivos.
Caso: DeliFIIS. Rol 3: asignacion contigua, enlazada e indexada.
"""

from __future__ import annotations

from es_disco import DiscoVirtual
from fs_comun import (
    DISCO_CONTROL,
    TAM_BLOQUE,
    TAM_PUNTERO,
    fichas_delifiis,
    imprimir_verificaciones,
)


def _ocupacion_inicial(disco, ocupacion=None):
    """Copia y valida el mapa bloque -> archivo usado por la simulacion."""
    if ocupacion is None:
        return [None] * disco.num_bloques
    if len(ocupacion) != disco.num_bloques:
        raise ValueError("La ocupacion debe tener un elemento por bloque")
    return list(ocupacion)


def _validar_solicitud(nombre, cantidad, archivos):
    if not isinstance(nombre, str) or not nombre:
        raise ValueError("El nombre del archivo no puede estar vacio")
    if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
        raise ValueError("La cantidad de bloques debe ser un entero positivo")
    if nombre in archivos:
        raise ValueError("El archivo ya esta asignado: %s" % nombre)


def _validar_bloque_logico(k, cantidad):
    if not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= cantidad:
        raise IndexError("Bloque logico fuera de rango: %r" % (k,))


class AsignacionContigua:
    """Asigna bloques consecutivos mediante primer ajuste (first-fit)."""

    def __init__(self, disco, ocupacion=None):
        self.disco = disco
        self.ocupacion = _ocupacion_inicial(disco, ocupacion)
        self.archivos = {}

    def bloques_libres(self):
        return sum(1 for valor in self.ocupacion if valor is None)

    def mayor_hueco(self):
        mayor = actual = 0
        for valor in self.ocupacion:
            if valor is None:
                actual += 1
                mayor = max(mayor, actual)
            else:
                actual = 0
        return mayor

    def buscar_hueco(self, cantidad):
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser positiva")
        limite = self.disco.num_bloques - cantidad + 1
        for inicio in range(max(0, limite)):
            if all(self.ocupacion[i] is None for i in range(inicio, inicio + cantidad)):
                return inicio
        return None

    def asignar(self, nombre, cantidad):
        _validar_solicitud(nombre, cantidad, self.archivos)
        inicio = self.buscar_hueco(cantidad)
        if inicio is None:
            return None
        bloques = list(range(inicio, inicio + cantidad))
        for numero in bloques:
            self.ocupacion[numero] = nombre
            self.disco.escribir(numero, ("%s:%d" % (nombre, numero)).encode("ascii"))
        self.archivos[nombre] = (inicio, cantidad)
        return bloques

    def leer_bloque(self, nombre, k):
        if nombre not in self.archivos:
            raise KeyError("Archivo no asignado: %s" % nombre)
        inicio, cantidad = self.archivos[nombre]
        _validar_bloque_logico(k, cantidad)
        return self.disco.leer(inicio + k - 1)


class AsignacionEnlazada:
    """Cada bloque guarda en sus ultimos 4 bytes el siguiente bloque."""

    FIN = (1 << (8 * TAM_PUNTERO)) - 1

    def __init__(self, disco, ocupacion=None):
        self.disco = disco
        self.ocupacion = _ocupacion_inicial(disco, ocupacion)
        self.archivos = {}

    @property
    def capacidad_datos(self):
        return self.disco.tam_bloque - TAM_PUNTERO

    def bloques_libres(self):
        return sum(1 for valor in self.ocupacion if valor is None)

    def _escribir_bloque(self, numero, nombre, siguiente):
        etiqueta = ("%s:%d" % (nombre, numero)).encode("ascii")[:self.capacidad_datos]
        datos = etiqueta + bytes(self.capacidad_datos - len(etiqueta))
        puntero = siguiente.to_bytes(TAM_PUNTERO, "little")
        self.disco.escribir(numero, datos + puntero)

    def _siguiente(self, contenido):
        valor = int.from_bytes(contenido[-TAM_PUNTERO:], "little")
        return None if valor == self.FIN else valor

    def asignar(self, nombre, cantidad):
        _validar_solicitud(nombre, cantidad, self.archivos)
        libres = [i for i, valor in enumerate(self.ocupacion) if valor is None]
        if len(libres) < cantidad:
            return None
        bloques = libres[:cantidad]
        for posicion, numero in enumerate(bloques):
            siguiente = bloques[posicion + 1] if posicion + 1 < cantidad else self.FIN
            self.ocupacion[numero] = nombre
            self._escribir_bloque(numero, nombre, siguiente)
        self.archivos[nombre] = (bloques[0], cantidad)
        return bloques

    def leer_bloque(self, nombre, k):
        if nombre not in self.archivos:
            raise KeyError("Archivo no asignado: %s" % nombre)
        actual, cantidad = self.archivos[nombre]
        _validar_bloque_logico(k, cantidad)
        for posicion in range(1, k + 1):
            contenido = self.disco.leer(actual)
            if posicion == k:
                return contenido[:self.capacidad_datos]
            actual = self._siguiente(contenido)
            if actual is None:
                raise RuntimeError("La cadena termino antes del bloque solicitado")
        raise RuntimeError("Cadena enlazada inconsistente")


class AsignacionIndexada:
    """Usa un bloque indice con punteros a todos los bloques de datos."""

    def __init__(self, disco, ocupacion=None):
        self.disco = disco
        self.ocupacion = _ocupacion_inicial(disco, ocupacion)
        self.archivos = {}

    def bloques_libres(self):
        return sum(1 for valor in self.ocupacion if valor is None)

    def asignar(self, nombre, cantidad):
        _validar_solicitud(nombre, cantidad, self.archivos)
        maximo = self.disco.tam_bloque // TAM_PUNTERO
        if cantidad > maximo:
            raise ValueError("El archivo excede la capacidad del bloque indice")
        libres = [i for i, valor in enumerate(self.ocupacion) if valor is None]
        if len(libres) < cantidad + 1:
            return None
        indice = libres[0]
        datos = libres[1:cantidad + 1]
        tabla = bytearray(self.disco.tam_bloque)
        for posicion, numero in enumerate(datos):
            inicio = posicion * TAM_PUNTERO
            tabla[inicio:inicio + TAM_PUNTERO] = numero.to_bytes(TAM_PUNTERO, "little")
            self.ocupacion[numero] = nombre
            self.disco.escribir(numero, ("%s:%d" % (nombre, posicion + 1)).encode("ascii"))
        self.ocupacion[indice] = nombre + "#indice"
        self.disco.escribir(indice, tabla)
        self.archivos[nombre] = (indice, cantidad)
        return [indice] + datos

    def leer_bloque(self, nombre, k):
        if nombre not in self.archivos:
            raise KeyError("Archivo no asignado: %s" % nombre)
        indice, cantidad = self.archivos[nombre]
        _validar_bloque_logico(k, cantidad)
        tabla = self.disco.leer(indice)
        inicio = (k - 1) * TAM_PUNTERO
        numero = int.from_bytes(tabla[inicio:inicio + TAM_PUNTERO], "little")
        return self.disco.leer(numero)


def medir_lecturas(asignador, nombre, bloques_logicos):
    """Mide lecturas reales reiniciando los contadores antes de cada acceso."""
    lecturas = []
    for k in bloques_logicos:
        asignador.disco.reiniciar_contadores()
        asignador.leer_bloque(nombre, k)
        lecturas.append(asignador.disco.accesos_lectura)
    return lecturas


def _lecturas_control():
    resultados = {}
    for nombre, clase in (
        ("contigua", AsignacionContigua),
        ("enlazada", AsignacionEnlazada),
        ("indexada", AsignacionIndexada),
    ):
        simulador = clase(DiscoVirtual(num_bloques=16))
        simulador.asignar("X", 5)
        resultados[nombre] = medir_lecturas(simulador, "X", (1, 3, 5))
    return resultados


def _fragmentacion_control():
    contigua = AsignacionContigua(DiscoVirtual(num_bloques=16), DISCO_CONTROL)
    enlazada = AsignacionEnlazada(DiscoVirtual(num_bloques=16), DISCO_CONTROL)
    indexada = AsignacionIndexada(DiscoVirtual(num_bloques=16), DISCO_CONTROL)
    return {
        "libres": contigua.bloques_libres(),
        "mayor_hueco": contigua.mayor_hueco(),
        "contigua": contigua.asignar("D", 6),
        "enlazada": enlazada.asignar("D", 6),
        "indexada": indexada.asignar("D", 6),
    }


def _perfil_delifiis(clase):
    simulador = clase(DiscoVirtual(num_bloques=16))
    fichas = fichas_delifiis()
    reservas = [simulador.asignar(pid, bloques) for pid, _descripcion, bloques in fichas]
    return fichas, reservas, simulador


def verificar():
    lecturas = _lecturas_control()
    fragmentacion = _fragmentacion_control()
    fichas = fichas_delifiis()
    tamanos = [bloques for _pid, _descripcion, bloques in fichas]

    contigua_ff = AsignacionContigua(DiscoVirtual(num_bloques=16), DISCO_CONTROL)
    primer_hueco = contigua_ff.asignar("X", 3)

    perfiles = {}
    for nombre, clase in (
        ("contigua", AsignacionContigua),
        ("enlazada", AsignacionEnlazada),
        ("indexada", AsignacionIndexada),
    ):
        perfiles[nombre] = _perfil_delifiis(clase)

    return [
        ("contigua: lecturas para k=1,3,5 son [1, 1, 1]",
         lecturas["contigua"] == [1, 1, 1]),
        ("enlazada: lecturas para k=1,3,5 son [1, 3, 5]",
         lecturas["enlazada"] == [1, 3, 5]),
        ("indexada: lecturas para k=1,3,5 son [2, 2, 2]",
         lecturas["indexada"] == [2, 2, 2]),
        ("DISCO_CONTROL tiene 8 bloques libres", fragmentacion["libres"] == 8),
        ("DISCO_CONTROL tiene un mayor hueco de 5 bloques",
         fragmentacion["mayor_hueco"] == 5),
        ("contigua: D de 6 bloques no cabe aunque hay 8 libres",
         fragmentacion["contigua"] is None),
        ("enlazada: D ocupa 6 de los 8 bloques libres",
         fragmentacion["enlazada"] is not None
         and len(fragmentacion["enlazada"]) == 6),
        ("indexada: D ocupa 6 datos + 1 indice de los 8 libres",
         fragmentacion["indexada"] is not None
         and len(fragmentacion["indexada"]) == 7),
        ("first-fit elige el hueco 5,6,7 para una solicitud de 3",
         primer_hueco == [5, 6, 7]),
        ("enlazada deja 4092 bytes de datos por bloque",
         TAM_BLOQUE - TAM_PUNTERO == 4092),
        ("perfil DeliFIIS conserva P1..P4 con tamanos 2,2,3,3",
         [pid for pid, _d, _b in fichas] == ["P1", "P2", "P3", "P4"]
         and tamanos == [2, 2, 3, 3]),
        ("perfil DeliFIIS suma 10 bloques", sum(tamanos) == 10),
        ("perfil DeliFIIS cabe con asignacion contigua",
         all(reserva is not None for reserva in perfiles["contigua"][1])),
        ("perfil DeliFIIS cabe con asignacion enlazada",
         all(reserva is not None for reserva in perfiles["enlazada"][1])),
        ("perfil DeliFIIS cabe con asignacion indexada",
         all(reserva is not None for reserva in perfiles["indexada"][1])),
    ]


def main():
    lecturas = _lecturas_control()
    print("=== METODOS DE ASIGNACION - DeliFIIS ===")
    print("\nLecturas reales para un archivo de 5 bloques (k=1,3,5):")
    for metodo in ("contigua", "enlazada", "indexada"):
        print("%-10s %s" % (metodo, lecturas[metodo]))

    fragmentacion = _fragmentacion_control()
    print("\nFragmentacion externa con DISCO_CONTROL:")
    print("Bloques libres: %d" % fragmentacion["libres"])
    print("Mayor hueco libre: %d" % fragmentacion["mayor_hueco"])
    print("D (6 bloques) en contigua: %s" %
          ("NO CABE" if fragmentacion["contigua"] is None else "CABE"))
    print("D (6 bloques) en enlazada: %s" %
          ("CABE" if fragmentacion["enlazada"] is not None else "NO CABE"))
    print("D (6 datos + 1 indice) en indexada: %s" %
          ("CABE" if fragmentacion["indexada"] is not None else "NO CABE"))
    print("La contigua falla por fragmentacion externa: hay espacio total, "
          "pero no 6 bloques consecutivos.")

    fichas = fichas_delifiis()
    print("\nPerfil DeliFIIS en disco vacio de 16 bloques:")
    print(", ".join("%s=%d" % (pid, bloques) for pid, _d, bloques in fichas))
    print("Total de datos: %d bloques" % sum(b for _p, _d, b in fichas))

    print("\n=== VERIFICACION ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())

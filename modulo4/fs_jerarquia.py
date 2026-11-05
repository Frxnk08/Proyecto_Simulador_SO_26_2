"""Modulo 4 (semana 10) - Jerarquia de directorios y rutas.
Caso: DeliFIIS

Cada directorio es un diccionario nombre -> numero de inodo. El nombre NO vive
en el inodo (Inodo no tiene campo nombre): vive en el directorio que lo contiene.
Solo depende de fs_comun.py (y, por fichas_delifiis, de M1 en lectura).
"""

from __future__ import annotations

import posixpath

from fs_comun import TAM_BLOQUE, Inodo, fichas_delifiis, imprimir_verificaciones


class Jerarquia:
    """Arbol de directorios en memoria con tabla de inodos."""

    def __init__(self):
        self.inodos: dict[int, Inodo] = {}
        self.directorios: dict[int, dict[str, int]] = {}
        self._siguiente = 1
        self.raiz = self._nuevo_inodo("directorio", permisos=0o755)
        self.directorios[self.raiz] = {}

    def _nuevo_inodo(self, tipo, tamano=0, permisos=0o640):
        numero = self._siguiente
        self._siguiente += 1
        self.inodos[numero] = Inodo(numero=numero, tipo=tipo, tamano=tamano, permisos=permisos)
        return numero

    @staticmethod
    def _partes(ruta):
        if not ruta.startswith("/"):
            raise ValueError(f"La ruta debe ser absoluta (empezar con /): {ruta}")
        return [p for p in ruta.split("/") if p]

    def resolver(self, ruta):
        """Devuelve (numero_inodo, pasos). Un paso por cada directorio recorrido."""
        actual = self.raiz
        pasos = []
        for nombre in self._partes(ruta):
            entradas = self.directorios.get(actual)
            if entradas is None:
                raise NotADirectoryError(f"No es un directorio (inodo {actual}): {ruta}")
            if nombre not in entradas:
                raise FileNotFoundError(f"No such file or directory: {ruta}")
            pasos.append(f"leer directorio (inodo {actual}): '{nombre}' -> inodo {entradas[nombre]}")
            actual = entradas[nombre]
        return actual, pasos

    def crear_directorio(self, ruta):
        """Como mkdir -p: crea los directorios que falten."""
        actual = self.raiz
        for nombre in self._partes(ruta):
            entradas = self.directorios[actual]
            if nombre not in entradas:
                numero = self._nuevo_inodo("directorio", permisos=0o755)
                self.directorios[numero] = {}
                entradas[nombre] = numero
            actual = entradas[nombre]
        return actual

    def crear_archivo(self, ruta, tamano=0, permisos=0o640):
        carpeta, nombre = posixpath.split(ruta)
        if not nombre:
            raise ValueError("Falta el nombre del archivo")
        padre, _ = self.resolver(carpeta or "/")
        entradas = self.directorios.get(padre)
        if entradas is None:
            raise NotADirectoryError(f"No es un directorio: {carpeta}")
        if nombre in entradas:
            raise FileExistsError(f"File exists: {ruta}")
        numero = self._nuevo_inodo("archivo", tamano=tamano, permisos=permisos)
        entradas[nombre] = numero
        return numero

    def listar(self, ruta="/"):
        """Recorrido tipo 'find': lista rutas absolutas en orden alfabetico."""
        inicio, _ = self.resolver(ruta)
        salida = []

        def recorrer(numero, prefijo):
            for nombre in sorted(self.directorios.get(numero, {})):
                hijo = self.directorios[numero][nombre]
                destino = posixpath.join(prefijo, nombre)
                salida.append(destino)
                if hijo in self.directorios:
                    recorrer(hijo, destino)

        recorrer(inicio, "/" if ruta == "/" else ruta.rstrip("/"))
        return salida


def ruta_relativa(desde, hasta):
    """Ruta relativa de 'hasta' tomando 'desde' como directorio actual."""
    return posixpath.relpath(hasta, desde)


def ruta_absoluta(desde, relativa):
    """Ruta absoluta de una ruta relativa evaluada desde el directorio 'desde'."""
    return posixpath.normpath(posixpath.join(desde, relativa))


def construir_cocina(perfil="control"):
    """perfil 'control': jerarquia de la practica. 'delifiis': agrega fichas P1-P4."""
    j = Jerarquia()
    for ruta in ("/cocina/recetas/entradas", "/cocina/recetas/fondos",
                 "/cocina/inventario", "/cocina/personal"):
        j.crear_directorio(ruta)
    j.crear_archivo("/cocina/recetas/entradas/ceviche.txt", tamano=7, permisos=0o640)
    j.crear_archivo("/cocina/inventario/stock.csv", tamano=7, permisos=0o660)
    if perfil == "delifiis":
        j.crear_directorio("/cocina/recetas/fichas")
        for pid, _descripcion, bloques in fichas_delifiis():
            j.crear_archivo(f"/cocina/recetas/fichas/ficha_{pid}.txt", tamano=bloques * TAM_BLOQUE)
    return j


def verificar():
    j = construir_cocina("control")
    cev = "/cocina/recetas/entradas/ceviche.txt"
    stk = "/cocina/inventario/stock.csv"
    desde = "/cocina/recetas"
    _, pasos = j.resolver(cev)
    try:
        j.resolver("/cocina/recetas/entradas/no_existe.txt")
        inexistente = False
    except FileNotFoundError:
        inexistente = True
    try:
        j.resolver("cocina/recetas")
        relativa_rechazada = False
    except ValueError:
        relativa_rechazada = True
    listado = j.listar("/cocina")
    jd = construir_cocina("delifiis")
    try:
        fichas = [(pid, jd.inodos[jd.resolver(f"/cocina/recetas/fichas/ficha_{pid}.txt")[0]].tamano // TAM_BLOQUE)
                  for pid, _d, _b in fichas_delifiis()]
        fichas_ok = fichas == [("P1", 2), ("P2", 2), ("P3", 3), ("P4", 3)]
    except Exception:
        fichas_ok = False
    return [
        ("ceviche.txt: ruta absoluta /cocina/recetas/entradas/ceviche.txt", j.listar("/cocina").count(cev) == 1),
        ("ceviche.txt: relativa desde /cocina/recetas = entradas/ceviche.txt",
         ruta_relativa(desde, cev) == "entradas/ceviche.txt"),
        ("stock.csv: relativa desde /cocina/recetas = ../inventario/stock.csv",
         ruta_relativa(desde, stk) == "../inventario/stock.csv"),
        ("ruta_absoluta es la inversa de ruta_relativa (ceviche y stock)",
         ruta_absoluta(desde, "entradas/ceviche.txt") == cev
         and ruta_absoluta(desde, "../inventario/stock.csv") == stk),
        ("resolver(ceviche.txt) recorre 4 directorios", len(pasos) == 4),
        ("ruta inexistente -> FileNotFoundError", inexistente),
        ("ruta relativa en resolver() -> ValueError", relativa_rechazada),
        ("jerarquia completa bajo /cocina: 5 directorios + 2 archivos", len(listado) == 7),
        ("el nombre NO esta en el inodo (Inodo sin campo nombre)", not hasattr(j.inodos[1], "nombre")),
        ("perfil delifiis: fichas P1-P4 con 2, 2, 3, 3 bloques", fichas_ok),
    ]


def main():
    print("=== JERARQUIA DE DIRECTORIOS - DeliFIIS ===")
    for perfil in ("control", "delifiis"):
        j = construir_cocina(perfil)
        print(f"\n--- find /cocina (perfil {perfil}) ---")
        for ruta in j.listar("/cocina"):
            print(ruta)
    j = construir_cocina("control")
    print("\n--- Tabla de rutas (desde /cocina/recetas) ---")
    print(f"{'Archivo':<14}{'Ruta absoluta':<40}{'Ruta relativa'}")
    for nombre, ruta in (("ceviche.txt", "/cocina/recetas/entradas/ceviche.txt"),
                         ("stock.csv", "/cocina/inventario/stock.csv")):
        print(f"{nombre:<14}{ruta:<40}{ruta_relativa('/cocina/recetas', ruta)}")
    print("\n--- Del nombre al inodo: resolver ceviche.txt ---")
    numero, pasos = j.resolver("/cocina/recetas/entradas/ceviche.txt")
    for paso in pasos:
        print(paso)
    ino = j.inodos[numero]
    print(f"inodo {ino.numero}: tipo={ino.tipo}, tamano={ino.tamano}, permisos={ino.permisos:o}")
    print("\n=== VERIFICACION ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())
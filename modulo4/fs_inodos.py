
from __future__ import annotations

from fs_comun import Inodo, bloques_necesarios, imprimir_verificaciones


class SistemaInodos:
    """Gestiona una tabla de inodos y un directorio plano nombre -> numero_inodo."""

    def __init__(self) -> None:
        self.tabla_inodos: dict[int, Inodo] = {}
        self.directorio: dict[str, int] = {}
        self.datos_inodos: dict[int, str] = {}
        self._siguiente_inodo: int = 1

    def _nuevo_numero(self) -> int:
        num = self._siguiente_inodo
        self._siguiente_inodo += 1
        return num

    def crear(
        self,
        nombre: str,
        contenido: str = "",
        propietario: str = "chef",
        grupo: str = "cocineros",
        permisos: int = 0o640,
    ) -> Inodo:
        """Crea un archivo regular y registra su entrada en el directorio."""
        if nombre in self.directorio:
            raise FileExistsError(f"El archivo '{nombre}' ya existe")

        num = self._nuevo_numero()
        tamano = len(contenido.encode("utf-8"))
        n_bloques = bloques_necesarios(tamano)
        inodo = Inodo(
            numero=num,
            tipo="archivo",
            tamano=tamano,
            propietario=propietario,
            grupo=grupo,
            permisos=permisos,
            enlaces=1,
            bloques=list(range(n_bloques)),
        )
        self.tabla_inodos[num] = inodo
        self.datos_inodos[num] = contenido
        self.directorio[nombre] = num
        return inodo

    def enlace_duro(self, origen: str, destino: str) -> Inodo:
        """Crea un enlace duro: destino apunta al mismo numero de inodo que origen."""
        if origen not in self.directorio:
            raise FileNotFoundError(f"No such file or directory: '{origen}'")
        if destino in self.directorio:
            raise FileExistsError(f"El destino '{destino}' ya existe")

        num_inodo = self.directorio[origen]
        inodo = self.tabla_inodos[num_inodo]
        if inodo.tipo == "simbolico":
            raise ValueError("No se permite enlace duro directo a un enlace simbolico en esta simulacion")

        inodo.enlaces += 1
        self.directorio[destino] = num_inodo
        return inodo

    def enlace_simbolico(self, origen: str, destino: str) -> Inodo:
        """Crea un enlace simbolico: nuevo inodo que guarda la ruta/nombre de origen."""
        if destino in self.directorio:
            raise FileExistsError(f"El destino '{destino}' ya existe")

        num = self._nuevo_numero()
        inodo = Inodo(
            numero=num,
            tipo="simbolico",
            tamano=len(origen.encode("utf-8")),
            enlaces=1,
            destino=origen,
        )
        self.tabla_inodos[num] = inodo
        self.directorio[destino] = num
        return inodo

    def leer(self, nombre: str, _profundidad: int = 0) -> str:
        """Lee el contenido de un archivo o sigue un enlace simbolico."""
        if _profundidad > 8:
            raise OSError("Demasiados niveles de enlaces simbolicos")
        if nombre not in self.directorio:
            raise FileNotFoundError(f"No such file or directory: '{nombre}'")

        num = self.directorio[nombre]
        inodo = self.tabla_inodos[num]

        if inodo.tipo == "simbolico":
            if not inodo.destino or inodo.destino not in self.directorio:
                raise FileNotFoundError(f"No such file or directory: '{nombre}' -> '{inodo.destino}'")
            return self.leer(inodo.destino, _profundidad + 1)

        return self.datos_inodos.get(num, "")

    def borrar(self, nombre: str) -> None:
        """Elimina la entrada del directorio y decrementa el contador de enlaces del inodo."""
        if nombre not in self.directorio:
            raise FileNotFoundError(f"No such file or directory: '{nombre}'")

        num = self.directorio.pop(nombre)
        inodo = self.tabla_inodos[num]
        inodo.enlaces -= 1

        if inodo.enlaces <= 0:
            del self.tabla_inodos[num]
            self.datos_inodos.pop(num, None)

    def obtener_inodo(self, nombre: str) -> Inodo:
        """Devuelve el Inodo asociado directamente a la entrada del directorio."""
        if nombre not in self.directorio:
            raise FileNotFoundError(f"No such file or directory: '{nombre}'")
        return self.tabla_inodos[self.directorio[nombre]]


def crear(fs: SistemaInodos, nombre: str, contenido: str = "") -> Inodo:
    return fs.crear(nombre, contenido)


def enlace_duro(fs: SistemaInodos, origen: str, destino: str) -> Inodo:
    return fs.enlace_duro(origen, destino)


def enlace_simbolico(fs: SistemaInodos, origen: str, destino: str) -> Inodo:
    return fs.enlace_simbolico(origen, destino)


def leer(fs: SistemaInodos, nombre: str) -> str:
    return fs.leer(nombre)


def borrar(fs: SistemaInodos, nombre: str) -> None:
    fs.borrar(nombre)


def verificar() -> list[tuple[str, bool]]:
    """Verifica el comportamiento esperado de inodos, enlaces duros y simbolicos."""
    pruebas: list[tuple[str, bool]] = []
    fs = SistemaInodos()

    texto_receta = "Receta oficial de Ceviche Clasico DeliFIIS"
    inodo_orig = crear(fs, "ceviche.txt", texto_receta)
    inodo_dur = enlace_duro(fs, "ceviche.txt", "dur.txt")
    inodo_sim = enlace_simbolico(fs, "ceviche.txt", "sim.txt")

    pruebas.append((
        "dur.txt comparte inodo con ceviche.txt y enlaces == 2",
        inodo_dur.numero == inodo_orig.numero and inodo_dur.enlaces == 2,
    ))

    pruebas.append((
        "sim.txt tiene inodo distinto y tipo simbolico",
        inodo_sim.numero != inodo_orig.numero and inodo_sim.tipo == "simbolico",
    ))
    pruebas.append((
        "Lectura correcta antes de borrar original",
        leer(fs, "dur.txt") == texto_receta and leer(fs, "sim.txt") == texto_receta,
    ))

    borrar(fs, "ceviche.txt")

    contenido_dur = leer(fs, "dur.txt")
    pruebas.append((
        "Tras borrar ceviche.txt, dur.txt sigue leyendo y enlaces == 1",
        contenido_dur == texto_receta and fs.obtener_inodo("dur.txt").enlaces == 1,
    ))

    sim_roto = False
    try:
        leer(fs, "sim.txt")
    except FileNotFoundError as exc:
        sim_roto = "No such file or directory" in str(exc)

    pruebas.append((
        "Tras borrar ceviche.txt, sim.txt queda roto (No such file or directory)",
        sim_roto,
    ))

    return pruebas


def main() -> int:
    print("=== MODULO 4 (SEMANA 10) - INODOS Y ENLACES (SIMULADO) ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())
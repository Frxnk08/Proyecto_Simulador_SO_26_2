"""Modulo 4 (semana 10) - Integracion de acceso a archivos.
Caso: DeliFIIS. Rol 4: integracion, verificador y recomendacion.

Implementa 'abrir una ficha' en 5 pasos secuenciales:
  Paso 1: ruta -> validacion y normalizacion de la ruta absoluta.
  Paso 2: directorios -> resolucion de nombres mediante mini-directorio en memoria.
  Paso 3: inodo -> obtencion de metadatos (propietario, grupo, permisos, bloques).
  Paso 4: permisos -> evaluacion de bits rwx segun clase (propietario/grupo/otros).
          Si es denegado, el SO rechaza ANTES de acceder al disco (accesos_lectura == 0).
  Paso 5: bloques -> acceso y lectura/escritura de bloques en DiscoVirtual.

Es autocontenido: no importa fs_jerarquia ni fs_permisos.
Salida por consola sin tildes (Windows).
"""

from __future__ import annotations

import os
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)

from es_disco import DiscoVirtual
from fs_comun import Inodo, TAM_BLOQUE, USUARIOS, fichas_delifiis, imprimir_verificaciones

_LETRAS = {"r": 4, "w": 2, "x": 1}


def puede(usuario: str, inodo: Inodo, operacion: str) -> bool:
    """Evalua si 'usuario' puede realizar 'operacion' ('r', 'w' o 'x') sobre el inodo.
    Aplica una sola clase en orden de precedencia: propietario, si no grupo, si no otros.
    """
    if operacion not in _LETRAS:
        raise ValueError(f"Operacion invalida: {operacion!r}. Debe ser 'r', 'w' o 'x'")
    if usuario == inodo.propietario:
        desp = 6
    elif inodo.grupo in USUARIOS.get(usuario, []):
        desp = 3
    else:
        desp = 0
    return bool((inodo.permisos >> desp) & _LETRAS[operacion])


class SistemaArchivosIntegrado:
    """Mini-directorio autocontenido conectado a un DiscoVirtual de bloques."""

    def __init__(self, disco: DiscoVirtual | None = None):
        self.disco = disco if disco is not None else DiscoVirtual(num_bloques=16, perfil="delifiis")
        self.inodos: dict[int, Inodo] = {}
        self.directorios: dict[int, dict[str, int]] = {}
        self._siguiente_inodo = 1

        # Inodo raiz (directorio /)
        self.raiz = self._crear_inodo(tipo="directorio", propietario="chef", grupo="cocineros", permisos=0o755)
        self.directorios[self.raiz] = {}

        self._inicializar_fichas()

    def _crear_inodo(
        self,
        tipo: str = "archivo",
        tamano: int = 0,
        propietario: str = "chef",
        grupo: str = "cocineros",
        permisos: int = 0o640,
        bloques: list[int] | None = None,
    ) -> int:
        num = self._siguiente_inodo
        self._siguiente_inodo += 1
        bloques_lista = list(bloques) if bloques is not None else []
        self.inodos[num] = Inodo(
            numero=num,
            tipo=tipo,
            tamano=tamano,
            propietario=propietario,
            grupo=grupo,
            permisos=permisos,
            bloques=bloques_lista,
        )
        return num

    def _partes(self, ruta: str) -> list[str]:
        if not ruta.startswith("/"):
            raise ValueError(f"La ruta debe ser absoluta (iniciar con '/'): {ruta}")
        partes = [p for p in ruta.split("/") if p]
        if not partes:
            raise ValueError("Ruta invalida: apunta a la raiz vacia")
        return partes

    def _crear_directorio(self, ruta: str, propietario: str = "chef", grupo: str = "cocineros", permisos: int = 0o755) -> int:
        """Crea directorios recursivamente en el mini-directorio."""
        actual = self.raiz
        for nombre in self._partes(ruta):
            entradas = self.directorios[actual]
            if nombre not in entradas:
                nuevo_inodo = self._crear_inodo("directorio", propietario=propietario, grupo=grupo, permisos=permisos)
                self.directorios[nuevo_inodo] = {}
                entradas[nombre] = nuevo_inodo
            actual = entradas[nombre]
        return actual

    def agregar_archivo(
        self,
        ruta: str,
        contenido: bytes,
        bloques_fisicos: list[int],
        propietario: str = "chef",
        grupo: str = "cocineros",
        permisos: int = 0o640,
    ) -> int:
        """Registra un archivo en el mini-directorio y escribe su contenido en DiscoVirtual."""
        partes = self._partes(ruta)
        dir_partes, nombre_archivo = partes[:-1], partes[-1]

        # Crear ruta de directorios padres
        inodo_dir = self.raiz
        if dir_partes:
            ruta_dir = "/" + "/".join(dir_partes)
            inodo_dir = self._crear_directorio(ruta_dir)

        # Crear inodo de archivo
        tamano = len(contenido)
        inodo_archivo = self._crear_inodo(
            tipo="archivo",
            tamano=tamano,
            propietario=propietario,
            grupo=grupo,
            permisos=permisos,
            bloques=bloques_fisicos,
        )
        self.directorios[inodo_dir][nombre_archivo] = inodo_archivo

        # Escribir en los bloques asignados del disco virtual
        desplazamiento = 0
        for b in bloques_fisicos:
            pedazo = contenido[desplazamiento : desplazamiento + TAM_BLOQUE]
            desplazamiento += TAM_BLOQUE
            if len(pedazo) < TAM_BLOQUE:
                pedazo = pedazo + bytes(TAM_BLOQUE - len(pedazo))
            self.disco.escribir(b, pedazo)

        return inodo_archivo

    def _inicializar_fichas(self):
        """Inicializa las recetas de control de la practica y del caso DeliFIIS."""
        # 1. ceviche.txt (control: 640, chef=rw, ayudante=r, visitante=nada)
        cont_ceviche = b"Receta oficial de Ceviche Clasico DeliFIIS: pescado, limon, aji limo, cebolla roja."
        self.agregar_archivo(
            "/cocina/recetas/entradas/ceviche.txt",
            contenido=cont_ceviche,
            bloques_fisicos=[3],
            propietario="chef",
            grupo="cocineros",
            permisos=0o640,
        )

        # 2. stock.csv (control: 660, chef=rw, ayudante=rw, visitante=nada)
        cont_stock = b"insumo,stock_kg,alerta_minima\npescado,45,10\nlimon,120,25\ncebolla,80,15\n"
        self.agregar_archivo(
            "/cocina/inventario/stock.csv",
            contenido=cont_stock,
            bloques_fisicos=[4],
            propietario="chef",
            grupo="cocineros",
            permisos=0o660,
        )

        # 3. Fichas de recetas DeliFIIS (P1 a P4 de CONJUNTO_OFICIAL)
        try:
            fichas = fichas_delifiis()
        except Exception:
            fichas = [
                ("P1", "Lomo Saltado", 2),
                ("P2", "Causa Limena", 2),
                ("P3", "Aji de Gallina", 3),
                ("P4", "Anticuchos", 3),
            ]

        # Bloques de 6 a 15 para las 4 fichas DeliFIIS
        bloque_actual = 6
        for pid, desc, n_bloques in fichas:
            bloques_ficha = list(range(bloque_actual, min(self.disco.num_bloques, bloque_actual + n_bloques)))
            bloque_actual += n_bloques
            cont_ficha = f"Ficha Tecnica Receta DeliFIIS [{pid}] {desc} - Preparacion estandarizada".encode("utf-8")
            self.agregar_archivo(
                f"/cocina/recetas/fichas/ficha_{pid}.txt",
                contenido=cont_ficha,
                bloques_fisicos=bloques_ficha,
                propietario="chef",
                grupo="cocineros",
                permisos=0o640,
            )

        # Reiniciar contadores de acceso al disco tras poblar el estado inicial
        self.disco.reiniciar_contadores()

    def abrir_ficha(self, ruta: str, usuario: str = "ayudante", operacion: str = "r") -> dict:
        """Ejecuta los 5 pasos del SO para abrir un archivo:
        1. Ruta -> normalizacion y validacion.
        2. Directorios -> recorrido de mini-directorios.
        3. Inodo -> obtencion del inodo con metadatos y bloques.
        4. Permisos -> chequeo rwx segun rol (chef/ayudante/visitante).
           Si es denegado, lanza PermissionError sin tocar el DiscoVirtual.
        5. Bloques -> lectura o escritura en DiscoVirtual.
        """
        pasos = []

        # Paso 1: Ruta
        partes = self._partes(ruta)
        ruta_normalizada = "/" + "/".join(partes)
        pasos.append(f"Paso 1 (Ruta): Normalizada '{ruta_normalizada}' ({len(partes)} componentes)")

        # Paso 2: Directorios
        actual = self.raiz
        for nombre in partes[:-1]:
            entradas = self.directorios.get(actual)
            if entradas is None or nombre not in entradas:
                raise FileNotFoundError(f"Directorio no encontrado: '{nombre}' en inodo {actual} (ruta {ruta})")
            inodo_hijo = entradas[nombre]
            if self.inodos[inodo_hijo].tipo != "directorio":
                raise NotADirectoryError(f"El componente '{nombre}' no es un directorio (inodo {inodo_hijo})")
            pasos.append(f"Paso 2 (Directorios): Inodo {actual} -> '{nombre}' -> Inodo {inodo_hijo}")
            actual = inodo_hijo

        nombre_archivo = partes[-1]
        entradas_finales = self.directorios.get(actual, {})
        if nombre_archivo not in entradas_finales:
            raise FileNotFoundError(f"Archivo no encontrado: '{nombre_archivo}' en directorio inodo {actual}")

        num_inodo = entradas_finales[nombre_archivo]
        inodo = self.inodos[num_inodo]

        # Paso 3: Inodo
        pasos.append(
            f"Paso 3 (Inodo): Inodo {inodo.numero} [tipo={inodo.tipo}, tamano={inodo.tamano}B, "
            f"propietario={inodo.propietario}, grupo={inodo.grupo}, permisos={oct(inodo.permisos)}, "
            f"bloques={inodo.bloques}]"
        )

        # Paso 4: Permisos
        autorizado = puede(usuario, inodo, operacion)
        if not autorizado:
            pasos.append(
                f"Paso 4 (Permisos): Usuario '{usuario}' solicita '{operacion}' -> DENEGADO "
                f"(bloques NO consultados en DiscoVirtual)"
            )
            raise PermissionError(
                f"Permiso denegado: usuario {usuario!r} no tiene permiso '{operacion}' "
                f"para inodo {inodo.numero} ({oct(inodo.permisos)})"
            )

        pasos.append(
            f"Paso 4 (Permisos): Usuario '{usuario}' solicita '{operacion}' -> AUTORIZADO "
            f"(permisos={oct(inodo.permisos)})"
        )

        # Paso 5: Bloques de DiscoVirtual
        datos_leidos = b""
        if operacion == "r":
            for b in inodo.bloques:
                datos_leidos += self.disco.leer(b)
            # Acotar al tamano util si aplica
            if inodo.tamano > 0 and len(datos_leidos) >= inodo.tamano:
                datos_utiles = datos_leidos[: inodo.tamano]
            else:
                datos_utiles = datos_leidos
            pasos.append(
                f"Paso 5 (Bloques): Leidos {len(inodo.bloques)} bloques {inodo.bloques} "
                f"({len(datos_utiles)} bytes) desde DiscoVirtual"
            )
        else:
            pasos.append(
                f"Paso 5 (Bloques): Preparado para escritura en bloques {inodo.bloques} de DiscoVirtual"
            )
            datos_utiles = b""

        return {
            "ruta": ruta_normalizada,
            "usuario": usuario,
            "operacion": operacion,
            "inodo": inodo,
            "pasos": pasos,
            "contenido": datos_utiles,
            "bloques": inodo.bloques,
            "accesos_lectura": self.disco.accesos_lectura,
            "accesos_escritura": self.disco.accesos_escritura,
        }

    def escribir_ficha(self, ruta: str, datos: bytes, usuario: str = "chef") -> dict:
        """Escribe datos sobre una ficha verificando permisos antes de escribir en disco."""
        res = self.abrir_ficha(ruta, usuario=usuario, operacion="w")
        inodo = res["inodo"]
        desplazamiento = 0
        for b in inodo.bloques:
            pedazo = datos[desplazamiento : desplazamiento + TAM_BLOQUE]
            desplazamiento += TAM_BLOQUE
            if len(pedazo) < TAM_BLOQUE:
                pedazo = pedazo + bytes(TAM_BLOQUE - len(pedazo))
            self.disco.escribir(b, pedazo)
        inodo.tamano = len(datos)
        res["accesos_escritura"] = self.disco.accesos_escritura
        return res


def verificar():
    """Verificaciones oficiales del Rol 4 (fs_integracion.py)."""
    resultados = []
    fs = SistemaArchivosIntegrado()

    # 1. ayudante lee ceviche.txt (640): OK
    fs.disco.reiniciar_contadores()
    try:
        res = fs.abrir_ficha("/cocina/recetas/entradas/ceviche.txt", usuario="ayudante", operacion="r")
        cumple1 = b"Ceviche" in res["contenido"] and res["accesos_lectura"] == 1
    except Exception:
        cumple1 = False
    resultados.append(("ayudante lee ceviche.txt (640): OK", cumple1))

    # 2. ayudante escribir ceviche.txt (640): denegado
    fs.disco.reiniciar_contadores()
    try:
        fs.escribir_ficha("/cocina/recetas/entradas/ceviche.txt", b"nuevo ceviche", usuario="ayudante")
        cumple2 = False
    except PermissionError:
        cumple2 = fs.disco.accesos_escritura == 0
    resultados.append(("ayudante escribir ceviche.txt (640): denegado y 0 escrituras a disco", cumple2))

    # 3. visitante lee: denegado
    fs.disco.reiniciar_contadores()
    try:
        fs.abrir_ficha("/cocina/recetas/entradas/ceviche.txt", usuario="visitante", operacion="r")
        cumple3 = False
    except PermissionError:
        cumple3 = True
    resultados.append(("visitante lee ceviche.txt (640): denegado", cumple3))

    # 4. visitante lee: accesos_lectura == 0 (el SO rechaza antes de leer un solo bloque)
    cumple4 = fs.disco.accesos_lectura == 0
    resultados.append(("visitante denegado: accesos_lectura == 0 (rechaza antes de leer disco)", cumple4))

    # 5. chef lee y escribe ceviche.txt (640): OK
    fs.disco.reiniciar_contadores()
    try:
        r_chef = fs.abrir_ficha("/cocina/recetas/entradas/ceviche.txt", usuario="chef", operacion="r")
        w_chef = fs.escribir_ficha("/cocina/recetas/entradas/ceviche.txt", b"Ceviche Gourmet", usuario="chef")
        cumple5 = b"Ceviche" in r_chef["contenido"] and w_chef["accesos_escritura"] == 1
    except Exception:
        cumple5 = False
    resultados.append(("chef lee y escribe ceviche.txt (640): OK", cumple5))

    # 6. ruta inexistente: error (FileNotFoundError)
    try:
        fs.abrir_ficha("/cocina/recetas/postres/torta.txt", usuario="chef", operacion="r")
        cumple6 = False
    except FileNotFoundError:
        cumple6 = True
    resultados.append(("ruta inexistente lanza FileNotFoundError", cumple6))

    # 7. componente no directorio lanza NotADirectoryError
    try:
        fs.abrir_ficha("/cocina/recetas/entradas/ceviche.txt/subarchivo.txt", usuario="chef", operacion="r")
        cumple7 = False
    except (NotADirectoryError, FileNotFoundError):
        cumple7 = True
    resultados.append(("componente que no es directorio lanza error esperado", cumple7))

    # 8. stock.csv (660): ayudante lee y escribe OK
    fs.disco.reiniciar_contadores()
    try:
        r_stock = fs.abrir_ficha("/cocina/inventario/stock.csv", usuario="ayudante", operacion="r")
        w_stock = fs.escribir_ficha("/cocina/inventario/stock.csv", b"insumo,stock\npescado,50\n", usuario="ayudante")
        cumple8 = b"pescado" in r_stock["contenido"] and w_stock["accesos_escritura"] == 1
    except Exception:
        cumple8 = False
    resultados.append(("stock.csv (660): ayudante lee y escribe OK", cumple8))

    # 9. stock.csv (660): visitante denegado con 0 accesos a disco
    fs.disco.reiniciar_contadores()
    try:
        fs.abrir_ficha("/cocina/inventario/stock.csv", usuario="visitante", operacion="r")
        cumple9 = False
    except PermissionError:
        cumple9 = fs.disco.accesos_lectura == 0
    resultados.append(("stock.csv (660): visitante denegado con accesos_lectura == 0", cumple9))

    # 10. fichas DeliFIIS P1-P4 legibles por ayudante
    fs.disco.reiniciar_contadores()
    try:
        f_p1 = fs.abrir_ficha("/cocina/recetas/fichas/ficha_P1.txt", usuario="ayudante", operacion="r")
        cumple10 = b"DeliFIIS" in f_p1["contenido"] and len(f_p1["bloques"]) >= 1
    except Exception:
        cumple10 = False
    resultados.append(("fichas DeliFIIS (P1-P4) legibles por ayudante", cumple10))

    # 11. los 5 pasos se ejecutan en orden secuencial
    try:
        res_pasos = fs.abrir_ficha("/cocina/recetas/entradas/ceviche.txt", usuario="chef", operacion="r")
        pasos = res_pasos["pasos"]
        tiene_p1 = any(p.startswith("Paso 1") for p in pasos)
        tiene_p2 = any(p.startswith("Paso 2") for p in pasos)
        tiene_p3 = any(p.startswith("Paso 3") for p in pasos)
        tiene_p4 = any(p.startswith("Paso 4") for p in pasos)
        tiene_p5 = any(p.startswith("Paso 5") for p in pasos)
        cumple11 = tiene_p1 and tiene_p2 and tiene_p3 and tiene_p4 and tiene_p5
    except Exception:
        cumple11 = False
    resultados.append(("5 pasos secuenciales de apertura (ruta->directorios->inodo->permisos->bloques)", cumple11))

    # 12. operacion invalida lanza ValueError
    try:
        puede("chef", fs.inodos[fs.raiz], "z")
        cumple12 = False
    except ValueError:
        cumple12 = True
    resultados.append(("operacion invalida lanza ValueError", cumple12))

    return resultados


def main():
    print("=========================================================")
    print("  MODULO 4 (SEMANA 10): INTEGRACION DE ACCESO A ARCHIVOS")
    print("  Caso: DeliFIIS - Apertura en 5 pasos (Rol 4 - Leonel)")
    print("=========================================================\n")

    fs = SistemaArchivosIntegrado()
    print(">>> Demostracion de apertura exitosa (ayudante -> ceviche.txt):")
    res_ok = fs.abrir_ficha("/cocina/recetas/entradas/ceviche.txt", usuario="ayudante", operacion="r")
    for p in res_ok["pasos"]:
        print(f"  {p}")
    print(f"  Contenido recuperado: {res_ok['contenido'].decode('utf-8', errors='ignore')[:60]}...")
    print(f"  Accesos lectura al DiscoVirtual: {res_ok['accesos_lectura']}\n")

    print(">>> Demostracion de rechazo por permisos (visitante -> ceviche.txt):")
    fs.disco.reiniciar_contadores()
    try:
        fs.abrir_ficha("/cocina/recetas/entradas/ceviche.txt", usuario="visitante", operacion="r")
    except PermissionError as err:
        print(f"  [RECHAZADO] {err}")
        print(f"  Accesos lectura al DiscoVirtual: {fs.disco.accesos_lectura} (0 bloques leidos)\n")

    print("=== VERIFICACION OFICIAL ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())


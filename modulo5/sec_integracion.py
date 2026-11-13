"""Modulo 5 (semana 11) - sec_integracion.py
Caso: DeliFIIS. Rol 4: Franco.

Cadena de custodia de una ficha: para abrir una ficha de DeliFIIS se pasa por
1) firewall, 2) autenticacion, 3) apertura real en el sistema de archivos de la
semana 10 (que lee el DiscoVirtual de la semana 9), 4) coherencia con la matriz
de acceso, 5) auditoria del intento denegado y 6) huella de la ficha leida.

Los pasos 1, 2, 4, 5 y 6 usan funciones de los archivos de los otros roles
(sec_firewall, sec_contrasenas, sec_acceso, sec_amenazas, sec_cifrado). Si un
archivo aun no esta subido, su paso se informa como PENDIENTE y no como FALLO.
Con el parametro hooks se pueden inyectar funciones de prueba.

Textos de consola sin tildes (Windows).
"""

from __future__ import annotations

import hashlib
import importlib
import os
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)

from sec_comun import imprimir_verificaciones  # noqa: E402  (tambien arma las rutas a M1/M3/M4)
from fs_integracion import SistemaArchivosIntegrado  # noqa: E402

# nombre del gancho -> (modulo, funcion) segun las interfaces acordadas
GANCHOS = {
    "evaluar": ("sec_firewall", "evaluar"),
    "crear_almacen": ("sec_contrasenas", "crear_almacen"),
    "autenticar": ("sec_contrasenas", "autenticar"),
    "matriz_esperada": ("sec_acceso", "matriz_esperada"),
    "huella": ("sec_cifrado", "huella"),
    "clasificar_evento": ("sec_amenazas", "clasificar_evento"),
}
_ERRORES: dict[str, str] = {}

# ---------------- Valores PROPIOS del equipo (datos de demostracion) ----------------
RUTA_P1 = "/cocina/recetas/fichas/ficha_P1.txt"
RUTA_CAJA = "/cocina/finanzas/caja.log"
RUTA_BUZON = "/cocina/pedidos/buzon_pedidos.txt"
RUTA_MENU = "/cocina/recetas/menu_publico.txt"
# (ruta, contenido, bloque libre del disco de 16, permisos): mismos archivos que el Rol 2
ARCHIVOS_NUEVOS = [
    (RUTA_CAJA, b"registro de caja", 0, 0o400),
    (RUTA_BUZON, b"buzon de pedidos", 1, 0o420),
    (RUTA_MENU, b"menu del dia", 2, 0o644),
]
# Claves de DEMOSTRACION (no reales). ayudante y visitante la repiten a proposito.
CLAVES_DEMO = {"chef": "Chef-Demo-2026", "ayudante": "ceviche123", "visitante": "ceviche123"}

# num, usuario, clave, ruta, operacion, puerto, autorizado, lecturas, propiedad del evento, paso que corta
ESCENARIOS = [
    ("1", "chef", "Chef-Demo-2026", RUTA_P1, "r", 443, True, 2, None, None),
    ("2", "ayudante", "ceviche123", RUTA_CAJA, "r", 443, False, 0, "Confidencialidad", "permisos"),
    ("3", "ayudante", "ceviche123", RUTA_P1, "w", 443, False, 0, "Integridad", "permisos"),
    ("4a", "ayudante", "ceviche123", RUTA_BUZON, "w", 443, True, 0, None, None),
    ("4b", "ayudante", "ceviche123", RUTA_BUZON, "r", 443, False, 0, "Confidencialidad", "permisos"),
    ("5", "visitante", "ceviche123", RUTA_MENU, "r", 443, True, 1, None, None),
    ("6", "visitante", "clave-equivocada", RUTA_MENU, "r", 443, False, 0, None, "autenticacion"),
    ("7", "chef", "Chef-Demo-2026", RUTA_P1, "r", 3306, False, 0, None, "firewall"),
]


def preparar_sistema() -> SistemaArchivosIntegrado:
    """Sistema de archivos de la semana 10 + 3 archivos nuevos, con contadores en cero."""
    sfa = SistemaArchivosIntegrado()
    for ruta, contenido, bloque, permisos in ARCHIVOS_NUEVOS:
        sfa.agregar_archivo(ruta, contenido, [bloque], permisos=permisos)
    sfa.disco.reiniciar_contadores()
    return sfa


def cargar_ganchos(hooks: dict | None = None) -> dict:
    """Devuelve {nombre: funcion o None}. hooks tiene prioridad (un None fuerza PENDIENTE)."""
    ganchos = {}
    for nombre, (modulo, funcion) in GANCHOS.items():
        if hooks is not None and nombre in hooks:
            ganchos[nombre] = hooks[nombre]
            continue
        try:
            ganchos[nombre] = getattr(importlib.import_module(modulo), funcion)
        except ModuleNotFoundError:
            ganchos[nombre] = None
        except Exception as error:  # modulo existe pero falla o no tiene la funcion
            _ERRORES[nombre] = f"{modulo}.{funcion}: {error}"
            ganchos[nombre] = None
    return ganchos


def faltantes(hooks: dict | None = None) -> list[str]:
    return [n for n, f in cargar_ganchos(hooks).items() if f is None]


def abrir_ficha_segura(sfa, almacen, usuario, clave, ruta, operacion="r",
                       proto="tcp", puerto=443, hooks=None) -> dict:
    """Ejecuta la cadena de custodia. Devuelve un dict con pasos y resultado.

    pasos = [(nombre, estado, detalle)], estado en OK, DENEGADO, PENDIENTE,
    OMITIDO, INCONSISTENTE o ERROR. Se corta en el primer DENEGADO de firewall,
    autenticacion o permisos (despues de permisos aun corren coherencia y auditoria).
    """
    g = cargar_ganchos(hooks)
    pasos: list[tuple[str, str, str]] = []
    res = {"usuario": usuario, "ruta": ruta, "operacion": operacion, "autorizado": False,
           "pasos": pasos, "lecturas": 0, "costo_dma_us": 0, "evento": None,
           "huella": None, "bytes": 0}

    # 1. Firewall
    if g["evaluar"] is None:
        pasos.append(("firewall", "PENDIENTE", "falta sec_firewall.py"))
    else:
        decision = g["evaluar"](proto, puerto)
        if decision != "ACCEPT":
            pasos.append(("firewall", "DENEGADO", f"{proto}/{puerto} -> {decision}"))
            return res
        pasos.append(("firewall", "OK", f"{proto}/{puerto} -> ACCEPT"))

    # 2. Autenticacion
    if g["autenticar"] is None or almacen is None:
        pasos.append(("autenticacion", "PENDIENTE", "falta sec_contrasenas.py o el almacen"))
    elif not g["autenticar"](almacen, usuario, clave):
        pasos.append(("autenticacion", "DENEGADO", f"clave incorrecta para {usuario}"))
        return res
    else:
        pasos.append(("autenticacion", "OK", usuario))

    # 3. Apertura real (S10 sobre S9)
    lect0 = sfa.disco.accesos_lectura
    dma0 = sfa.disco.costo_cpu_us("dma")
    contenido = None
    permitido = True
    try:
        r = sfa.abrir_ficha(ruta, usuario, operacion)
        contenido = r.get("contenido") if operacion == "r" else None
        pasos.append(("permisos", "OK", f"{usuario} puede '{operacion}' en {ruta}"))
    except PermissionError as error:
        permitido = False
        pasos.append(("permisos", "DENEGADO", str(error)))
    except (FileNotFoundError, NotADirectoryError) as error:
        pasos.append(("apertura", "ERROR", str(error)))
        return res
    res["lecturas"] = sfa.disco.accesos_lectura - lect0
    res["costo_dma_us"] = sfa.disco.costo_cpu_us("dma") - dma0
    res["autorizado"] = permitido
    if contenido is not None:
        res["bytes"] = len(contenido)

    # 4. Coherencia entre la matriz de acceso (Rol 2) y lo que permitio el inodo (S10)
    if g["matriz_esperada"] is None:
        pasos.append(("coherencia", "PENDIENTE", "falta sec_acceso.py"))
    else:
        fila = g["matriz_esperada"](ruta)
        if fila is None:
            pasos.append(("coherencia", "OMITIDO", "ruta fuera de la matriz"))
        else:
            esperado = fila.get(usuario, (False, False))[0 if operacion == "r" else 1]
            estado = "OK" if esperado == permitido else "INCONSISTENTE"
            pasos.append(("coherencia", estado, f"matriz={esperado} inodo={permitido}"))

    # 5. Auditoria del intento denegado
    if not permitido:
        if g["clasificar_evento"] is None:
            pasos.append(("auditoria", "PENDIENTE", "falta sec_amenazas.py"))
        else:
            evento = g["clasificar_evento"](usuario, operacion, False, ruta)
            res["evento"] = evento
            detalle = evento.get("propiedad", "") if evento else "sin evento"
            pasos.append(("auditoria", "OK", detalle))

    # 6. Huella de lo leido
    if permitido and contenido is not None:
        if g["huella"] is None:
            pasos.append(("proteccion", "PENDIENTE", "falta sec_cifrado.py"))
        else:
            res["huella"] = g["huella"](contenido)
            pasos.append(("proteccion", "OK", f"sha256 {res['huella'][:16]}"))
    elif permitido:
        pasos.append(("proteccion", "OMITIDO", "operacion de escritura"))
    return res


def correr_escenario(esc, hooks=None, claves=None) -> dict:
    """Corre un escenario en un sistema nuevo (contadores aislados)."""
    num, usuario, clave, ruta, op, puerto = esc[:6]
    g = cargar_ganchos(hooks)
    almacen = g["crear_almacen"](claves or CLAVES_DEMO) if g["crear_almacen"] else None
    sfa = preparar_sistema()
    return abrir_ficha_segura(sfa, almacen, usuario, clave, ruta, op, "tcp", puerto, hooks)


# ---------------- Funciones de prueba (se inyectan por hooks) ----------------
def _fila_desde_modo(modo: int) -> dict:
    digitos = ((modo >> 6) & 7, (modo >> 3) & 7, modo & 7)
    return {u: (bool(d & 4), bool(d & 2)) for u, d in zip(("chef", "ayudante", "visitante"), digitos)}


_MODOS_PRUEBA = {RUTA_P1: 0o640, RUTA_CAJA: 0o400, RUTA_BUZON: 0o420, RUTA_MENU: 0o644}


def ganchos_de_prueba() -> dict:
    def evaluar(proto, puerto):
        return "DROP" if (proto, puerto) == ("tcp", 3306) else "ACCEPT"

    def evento(usuario, operacion, permitido, ruta=""):
        if permitido:
            return None
        return {"usuario": usuario, "operacion": operacion, "ruta": ruta,
                "amenaza": "acceso no autorizado",
                "propiedad": "Confidencialidad" if operacion == "r" else "Integridad"}

    return {
        "evaluar": evaluar,
        "crear_almacen": lambda claves: dict(claves),
        "autenticar": lambda almacen, usuario, clave: almacen.get(usuario) == clave,
        "matriz_esperada": lambda ruta: _fila_desde_modo(_MODOS_PRUEBA[ruta]) if ruta in _MODOS_PRUEBA else None,
        "huella": lambda datos: hashlib.sha256(datos).hexdigest(),
        "clasificar_evento": evento,
    }


def _resumen_escenario(esc, res) -> tuple:
    corte = next((p[0] for p in res["pasos"] if p[1] == "DENEGADO"), None)
    prop = res["evento"]["propiedad"] if res["evento"] else None
    return (res["autorizado"], res["lecturas"], prop, corte)


def verificar():
    v = []
    fake = ganchos_de_prueba()

    # A) Orquestacion con ganchos de prueba (siempre corre; usa S9/S10 reales)
    for esc in ESCENARIOS:
        res = correr_escenario(esc, fake)
        esperado = (esc[6], esc[7], esc[8], esc[9])
        v.append((f"[prueba] escenario {esc[0]}: {esc[1]} '{esc[4]}' {esc[3].split('/')[-1]} -> {esperado}",
                  _resumen_escenario(esc, res) == esperado))
    r1 = correr_escenario(ESCENARIOS[0], fake)
    v.append(("[prueba] esc. 1: ficha P1 cuesta 2 lecturas y 76 us de CPU con DMA (perfil de S9)",
              r1["lecturas"] == 2 and r1["costo_dma_us"] == 76))
    v.append(("[prueba] esc. 1: huella SHA-256 de 64 caracteres hexadecimales",
              r1["huella"] is not None and len(r1["huella"]) == 64))
    r2 = correr_escenario(ESCENARIOS[1], fake)
    v.append(("[prueba] denegado por permisos: 0 lecturas y evento de auditoria registrado",
              r2["lecturas"] == 0 and r2["evento"] is not None))
    v.append(("[prueba] coherencia: la matriz de prueba coincide con los inodos reales en los 8 escenarios",
              all(p[1] == "OK" for esc in ESCENARIOS
                  for p in correr_escenario(esc, fake)["pasos"] if p[0] == "coherencia")))

    # B) Sin ningun gancho: todo PENDIENTE y la apertura de S10 sigue funcionando
    nada = {n: None for n in GANCHOS}
    rp = correr_escenario(ESCENARIOS[0], nada)
    estados = {p[0]: p[1] for p in rp["pasos"]}
    v.append(("sin ganchos: firewall, autenticacion, coherencia y proteccion quedan PENDIENTE",
              all(estados[k] == "PENDIENTE" for k in ("firewall", "autenticacion", "coherencia", "proteccion"))))
    v.append(("sin ganchos: la apertura de S10 igual autoriza al chef", rp["autorizado"] and rp["lecturas"] == 2))

    # C) Integridad de una ficha (huella antes y despues de escribir) con S10 real
    sfa = preparar_sistema()
    h1 = fake["huella"](sfa.abrir_ficha(RUTA_P1, "chef", "r")["contenido"])
    sfa.escribir_ficha(RUTA_P1, b"MODIFICADA", "chef")
    h2 = fake["huella"](sfa.abrir_ficha(RUTA_P1, "chef", "r")["contenido"])
    v.append(("escribir la ficha cambia su huella (se detecta la alteracion)", h1 != h2))
    try:
        sfa.escribir_ficha(RUTA_P1, b"X", "ayudante")
        bloqueado = False
    except PermissionError:
        bloqueado = True
    v.append(("el ayudante no puede escribir la ficha (640)", bloqueado))

    # D) Cadena real, solo si ya estan los 5 archivos de los otros roles
    falta = faltantes()
    if falta:
        print(f"[aviso] cadena real PENDIENTE: faltan ganchos {', '.join(falta)}")
        for nombre, motivo in _ERRORES.items():
            print(f"[aviso] {motivo}")
    else:
        for esc in ESCENARIOS:
            res = correr_escenario(esc)
            esperado = (esc[6], esc[7], esc[8], esc[9])
            v.append((f"[real] escenario {esc[0]} -> {esperado}", _resumen_escenario(esc, res) == esperado))
        v.append(("[real] ningun escenario con paso INCONSISTENTE",
                  all(p[1] != "INCONSISTENTE" for esc in ESCENARIOS for p in correr_escenario(esc)["pasos"])))
    return v


def main():
    print("=" * 72)
    print("MODULO 5 - CADENA DE CUSTODIA DE UNA FICHA (DeliFIIS)")
    print("=" * 72)
    falta = faltantes()
    print("Ganchos pendientes: " + (", ".join(falta) if falta else "ninguno (cadena real completa)"))
    for esc in ESCENARIOS:
        res = correr_escenario(esc)
        print(f"\nEscenario {esc[0]}: {esc[1]} '{esc[4]}' {esc[3]} (tcp/{esc[5]})"
              f" -> {'AUTORIZADO' if res['autorizado'] else 'NO AUTORIZADO'}"
              f" | lecturas de disco: {res['lecturas']} | CPU DMA: {res['costo_dma_us']} us")
        for nombre, estado, detalle in res["pasos"]:
            print(f"   {nombre:<14}{estado:<14}{detalle}")
    print("\n" + "=" * 72)
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())
"""Modulo 4 (semana 10) - Permisos y propietarios (rwx, octal, umask).
Caso: DeliFIIS

Simulacion pura en Python (corre en Windows). chown y sudo -u reales se prueban
aparte en la VM del curso. Solo depende de fs_comun.py.
"""

from __future__ import annotations

from fs_comun import CONTROL, USUARIOS, Inodo, imprimir_verificaciones

_LETRAS = {"r": 4, "w": 2, "x": 1}
_DESPLAZAMIENTO = {"u": 6, "g": 3, "o": 0}


def octal_a_simbolico(permisos):
    """0o640 -> 'rw-r-----'."""
    if not 0 <= permisos <= 0o777:
        raise ValueError(f"Permisos fuera de rango: {permisos:o}")
    texto = ""
    for desp in (6, 3, 0):
        grupo = (permisos >> desp) & 7
        for letra, bit in _LETRAS.items():
            texto += letra if grupo & bit else "-"
    return texto


def simbolico_a_octal(texto):
    """'rw-r-----' -> 0o640."""
    if len(texto) != 9:
        raise ValueError("Se esperan 9 caracteres, por ejemplo rw-r-----")
    valor = 0
    for i, caracter in enumerate(texto):
        if caracter == "rwx"[i % 3]:
            valor |= 1 << (8 - i)
        elif caracter != "-":
            raise ValueError(f"Caracter invalido en la posicion {i}: {caracter!r}")
    return valor


def aplicar_simbolico(actual, expresion):
    """Equivale a chmod con notacion simbolica: 'u=rw,g=r,o=' o 'o+r' o 'g-w'."""
    permisos = actual
    for clausula in expresion.split(","):
        clausula = clausula.strip()
        pos = next((i for i, c in enumerate(clausula) if c in "=+-"), -1)
        if pos <= 0:
            raise ValueError(f"Clausula invalida: {clausula!r}")
        clases, operador, letras = clausula[:pos], clausula[pos], clausula[pos + 1:]
        if any(c not in "ugoa" for c in clases) or any(c not in _LETRAS for c in letras):
            raise ValueError(f"Clausula invalida: {clausula!r}")
        if "a" in clases:
            clases = "ugo"
        bits = sum(_LETRAS[c] for c in set(letras))
        for clase in set(clases):
            desp = _DESPLAZAMIENTO[clase]
            if operador == "=":
                permisos = (permisos & ~(7 << desp)) | (bits << desp)
            elif operador == "+":
                permisos |= bits << desp
            else:
                permisos &= ~(bits << desp)
    return permisos


def puede(usuario, inodo, operacion):
    """True si 'usuario' puede hacer 'operacion' ('r', 'w' o 'x') sobre el inodo.
    Se aplica solo UNA clase: propietario, si no grupo, si no otros."""
    if operacion not in _LETRAS:
        raise ValueError("La operacion debe ser 'r', 'w' o 'x'")
    if usuario == inodo.propietario:
        desp = 6
    elif inodo.grupo in USUARIOS.get(usuario, []):
        desp = 3
    else:
        desp = 0
    return bool((inodo.permisos >> desp) & _LETRAS[operacion])


def umask_resultante(umask, es_directorio):
    """Permisos de un archivo (base 666) o directorio (base 777) nuevo con esa umask."""
    base = 0o777 if es_directorio else 0o666
    return base & ~int(umask, 8)


def matriz(permisos, propietario="chef", grupo="cocineros"):
    """{usuario: (lee, escribe)} para un archivo con esos permisos."""
    inodo = Inodo(numero=0, propietario=propietario, grupo=grupo, permisos=permisos)
    return {u: (puede(u, inodo, "r"), puede(u, inodo, "w")) for u in USUARIOS}


def imprimir_matriz(nombre, permisos):
    print(f"\n{nombre} ({permisos:o}, {octal_a_simbolico(permisos)})")
    print(f"{'Usuario':<12}{'Lee':>6}{'Escribe':>10}")
    for usuario, (lee, escribe) in matriz(permisos).items():
        print(f"{usuario:<12}{'SI' if lee else 'NO':>6}{'SI' if escribe else 'NO':>10}")


def verificar():
    resultados = []
    for nombre, (permisos, esperado) in CONTROL["matriz_permisos"].items():
        resultados.append((f"matriz de {nombre} ({permisos:o}) coincide con el control",
                           matriz(permisos) == esperado))
    resultados += [
        ("640 -> rw-r----- y 754 -> rwxr-xr--",
         octal_a_simbolico(0o640) == "rw-r-----" and octal_a_simbolico(0o754) == "rwxr-xr--"),
        ("octal <-> simbolico es reversible para 000..777",
         all(simbolico_a_octal(octal_a_simbolico(p)) == p for p in range(0o1000))),
        ("chmod u=rw,g=r,o= (desde 754) da 640", aplicar_simbolico(0o754, "u=rw,g=r,o=") == 0o640),
        ("chmod o+r sobre 640 da 644: visitante lee y no escribe",
         aplicar_simbolico(0o640, "o+r") == 0o644 and matriz(0o644)["visitante"] == (True, False)),
        ("umask 022 -> archivo 644, directorio 755",
         (umask_resultante("022", False), umask_resultante("022", True)) == CONTROL["umask"]["022"]),
        ("umask 077 -> archivo 600, directorio 700",
         (umask_resultante("077", False), umask_resultante("077", True)) == CONTROL["umask"]["077"]),
    ]
    try:
        puede("chef", Inodo(numero=0), "z")
        rechaza = False
    except ValueError:
        rechaza = True
    resultados.append(("operacion invalida -> ValueError", rechaza))
    return resultados


def main():
    print("=== PERMISOS POR ROL - DeliFIIS ===")
    for nombre, (permisos, _) in CONTROL["matriz_permisos"].items():
        imprimir_matriz(nombre, permisos)
    print("\n--- umask ---")
    for umask in ("022", "077"):
        print(f"umask {umask}: archivo {umask_resultante(umask, False):o}, "
              f"directorio {umask_resultante(umask, True):o}")
    print("\n=== VERIFICACION ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())
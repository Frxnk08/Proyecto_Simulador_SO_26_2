
from __future__ import annotations

from fs_comun import (
    CONTROL,
    TAM_BLOQUE,
    TAM_PUNTERO,
    imprimir_verificaciones,
)

try:
    from paginacion import fragmentacion_interna
except ImportError:
    def fragmentacion_interna(tamano_bytes: int) -> tuple[int, int, int]:
        if tamano_bytes < 0:
            raise ValueError("El tamano en bytes no puede ser negativo")
        paginas = (tamano_bytes + TAM_BLOQUE - 1) // TAM_BLOQUE
        reservado = paginas * TAM_BLOQUE
        return paginas, reservado, reservado - tamano_bytes


def calcular_fragmentacion_interna(tamano_bytes: int) -> tuple[int, int, int]:
    """Devuelve (bloques, bytes_reservados, bytes_desperdiciados)."""
    return fragmentacion_interna(tamano_bytes)


def capacidad_bloque_indice(
    tam_bloque: int = TAM_BLOQUE,
    tam_puntero: int = TAM_PUNTERO,
) -> tuple[int, int]:
    """Calcula (punteros_por_bloque, max_tamano_archivo_bytes) para indice simple."""
    if tam_bloque <= 0 or tam_puntero <= 0:
        raise ValueError("El tamano de bloque y puntero deben ser positivos")
    punteros = tam_bloque // tam_puntero
    max_bytes = punteros * tam_bloque
    return punteros, max_bytes


def verificar() -> list[tuple[str, bool]]:
    """Verifica fragmentacion interna y capacidad de indice contra CONTROL."""
    pruebas: list[tuple[str, bool]] = []

    res_10240 = calcular_fragmentacion_interna(10240)
    esp_10240 = CONTROL["interna"][10240]
    pruebas.append((
        f"Fragmentacion interna 10240 B -> {res_10240} (esperado {esp_10240})",
        res_10240 == esp_10240,
    ))

    res_4097 = calcular_fragmentacion_interna(4097)
    esp_4097 = CONTROL["interna"][4097]
    pruebas.append((
        f"Fragmentacion interna 4097 B -> {res_4097} (esperado {esp_4097})",
        res_4097 == esp_4097,
    ))

    punteros, max_bytes = capacidad_bloque_indice()
    esp_punteros = CONTROL["punteros_por_indice"]
    esp_max_bytes = CONTROL["max_archivo_un_indice"]

    pruebas.append((
        f"Punteros por bloque indice -> {punteros} (esperado {esp_punteros})",
        punteros == esp_punteros,
    ))
    pruebas.append((
        f"Tamano maximo con un indice -> {max_bytes} B / 4 MB (esperado {esp_max_bytes} B)",
        max_bytes == esp_max_bytes,
    ))

    return pruebas


def main() -> int:
    print("=== MODULO 4 (SEMANA 10) - FRAGMENTACION Y BLOQUES INDICE ===")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())
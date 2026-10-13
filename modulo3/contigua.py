import os
import sys

# Intentar importar la configuración común si ya fue creada por Persona 4
try:
    from comun import MEMORIA_TOTAL, eventos, intervalos, CONJUNTO_EQUIPO, CONJUNTO_OFICIAL
except ImportError:
    # Valores de respaldo acordados (Sección 2) mientras comun.py no esté disponible
    MEMORIA_TOTAL = 10

    CONJUNTO_EQUIPO = [
        ("Q1", 0, 4, 2),
        ("Q2", 1, 11, 2),
        ("Q3", 2, 13, 2),
        ("Q4", 4, 18, 3),
        ("Q5", 6, 21, 3),
    ]

    CONJUNTO_OFICIAL = [
        ("P1", 0, 5, 2),
        ("P2", 1, 8, 2),
        ("P3", 2, 16, 3),
        ("P4", 3, 22, 3),
    ]

    def intervalos(procesos):
        if isinstance(procesos[0], tuple):
            return procesos
        return [(p.id, p.llegada, getattr(p, 'fin', 0), p.tamano) for p in procesos]

    def eventos(intervs):
        ev = []
        for (i, a, f, s) in intervs:
            # Salida = 0, Llegada = 1 (en mismo instante, la salida se procesa primero)
            ev.append((a, 1, i, s))
            ev.append((f, 0, i, s))
        return sorted(ev)


def simular_asignacion_contigua(nombre_conjunto, datos_conjunto):
    print(f"\n==========================================")
    print(f" SIMULACIÓN ASIGNACIÓN CONTIGUA: {nombre_conjunto}")
    print(f"==========================================")

    memoria = ['.'] * MEMORIA_TOTAL
    rechazados = set()

    lista_intervalos = intervalos(datos_conjunto)
    lista_eventos = eventos(lista_intervalos)

    for instante, tipo_evento, pid, tamano in lista_eventos:
        # Usamos el último carácter del ID para representar el estante (ej: '1' para Q1/P1)
        simbolo = pid[-1]

        if tipo_evento == 0:  # Evento: Salida de pedido
            if pid in rechazados:
                continue  # La salida de un pedido rechazado se ignora

            # Liberar estantes
            memoria = ['.' if char == simbolo else char for char in memoria]
            estado_mem = "".join(memoria)
            print(f"t={instante:<2} | Sale {pid:<2} (libera {tamano})      | Estantes: {estado_mem}")

        elif tipo_evento == 1:  # Evento: Llegada de pedido
            # Búsqueda por Primer Ajuste (First-Fit)
            pos_encontrada = -1
            max_fila_libre = 0
            temp_len = 0
            temp_inicio = 0

            for idx, char in enumerate(memoria):
                if char == '.':
                    if temp_len == 0:
                        temp_inicio = idx
                    temp_len += 1
                    if temp_len > max_fila_libre:
                        max_fila_libre = temp_len
                    if temp_len == tamano and pos_encontrada == -1:
                        pos_encontrada = temp_inicio
                else:
                    temp_len = 0

            total_libres = memoria.count('.')

            if pos_encontrada != -1:
                # Asignar espacio contiguo
                for k in range(pos_encontrada, pos_encontrada + tamano):
                    memoria[k] = simbolo
                estado_mem = "".join(memoria)
                print(f"t={instante:<2} | Entra {pid:<2} ({tamano} estantes)  | Estantes: {estado_mem}")
            else:
                # Rechazar pedido por falta de un bloque contiguo
                rechazados.add(pid)
                estado_mem = "".join(memoria)
                print(
                    f"t={instante:<2} | {pid} pide {tamano}: RECHAZADO  | Estantes: {estado_mem} "
                    f"(Libres: {total_libres}, Fila libre máx: {max_fila_libre})"
                )


if __name__ == "__main__":
    simular_asignacion_contigua("Conjunto Equipo (Q1-Q5)", CONJUNTO_EQUIPO)
    simular_asignacion_contigua("Conjunto Oficial (P1-P4)", CONJUNTO_OFICIAL)
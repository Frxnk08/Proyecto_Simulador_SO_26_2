import threading
import time

CAPACIDAD = 5
NUM_PROVEEDORES = 2
NUM_COCINEROS = 2
INSUMOS_POR_PROVEEDOR = 10
MAX_ESPERA = 2000  # si espera mas de ~2 segundos, se da por vencido

stock = 0
total_insertados = 0
total_retirados = 0
medidor = threading.Lock()

def proveedor(id_proveedor, cantidad):
    global stock, total_insertados
    for _ in range(cantidad):
        intentos = 0
        while stock >= CAPACIDAD:
            time.sleep(0.001)
            intentos += 1
            if intentos >= MAX_ESPERA:
                print(f"[{threading.current_thread().name}] ATASCADO esperando espacio (stock={stock}) - abandono")
                return
        valor_leido = stock
        time.sleep(0.001)
        stock = valor_leido + 1
        with medidor:
            total_insertados += 1
        print(f"[{threading.current_thread().name}] inserto insumo (stock={stock})")

def cocinero(id_cocinero, cantidad):
    global stock, total_retirados
    retirados = 0
    while retirados < cantidad:
        intentos = 0
        while stock <= 0:
            time.sleep(0.001)
            intentos += 1
            if intentos >= MAX_ESPERA:
                print(f"[{threading.current_thread().name}] ATASCADO esperando insumo (stock={stock}) - abandono")
                return
        valor_leido = stock
        time.sleep(0.001)
        stock = valor_leido - 1
        with medidor:
            total_retirados += 1
        retirados += 1
        print(f"[{threading.current_thread().name}] retiro insumo (stock={stock})")

def main():
    total = NUM_PROVEEDORES * INSUMOS_POR_PROVEEDOR
    por_cocinero = total // NUM_COCINEROS

    hilos = []
    for i in range(NUM_PROVEEDORES):
        hilos.append(threading.Thread(target=proveedor, args=(i, INSUMOS_POR_PROVEEDOR), name=f"Proveedor-{i}"))
    for i in range(NUM_COCINEROS):
        hilos.append(threading.Thread(target=cocinero, args=(i, por_cocinero), name=f"Cocinero-{i}"))

    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    esperado = total_insertados - total_retirados

    print("\n=== VERIFICACION (SIN sincronizacion) ===")
    print(f"Insertados: {total_insertados} | Retirados: {total_retirados}")
    print(f"Stock final real    : {stock}")
    print(f"Stock final esperado: {esperado}")
    if stock != esperado:
        print("RESULTADO: FALLO - condicion de carrera detectada (stock mal calculado)")
    else:
        print("RESULTADO: coincidio esta vez")

if __name__ == "__main__":
    main()
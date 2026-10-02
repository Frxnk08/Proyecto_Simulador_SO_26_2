import threading
import time

CAPACIDAD = 5
NUM_PROVEEDORES = 2
NUM_COCINEROS = 2
INSUMOS_POR_PROVEEDOR = 10

stock = 0  # SIN ningun candado protegiendolo (a proposito)

total_insertados = 0
total_retirados = 0
medidor = threading.Lock()  # solo para contar bien, NO protege "stock"

def proveedor(id_proveedor, cantidad):
    global stock, total_insertados
    for _ in range(cantidad):
        while stock >= CAPACIDAD:
            time.sleep(0.001)

        valor_leido = stock          # LEE el stock
        time.sleep(0.001)            # fuerza que otro hilo se meta en el medio
        stock = valor_leido + 1      # ESCRIBE el nuevo stock

        with medidor:
            total_insertados += 1
        print(f"[{threading.current_thread().name}] inserto insumo (stock={stock})")

def cocinero(id_cocinero, cantidad):
    global stock, total_retirados
    retirados = 0
    while retirados < cantidad:
        if stock <= 0:
            time.sleep(0.001)
            continue

        valor_leido = stock          # LEE el stock
        time.sleep(0.001)            # fuerza que otro hilo se meta en el medio
        stock = valor_leido - 1      # ESCRIBE el nuevo stock

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

    print("\n=== VERIFICACION ===")
    print(f"Insertados: {total_insertados} | Retirados: {total_retirados}")
    print(f"Stock final real    : {stock}")
    print(f"Stock final esperado: {esperado}")
    if stock != esperado:
        print("RESULTADO: FALLO - condicion de carrera detectada (stock mal calculado)")
    else:
        print("RESULTADO: coincidio esta vez")

if __name__ == "__main__":
    main()
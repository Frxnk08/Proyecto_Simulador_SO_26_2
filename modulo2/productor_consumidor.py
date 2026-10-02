import threading
import time
import random
from datetime import datetime

CAPACIDAD = 5
NUM_PROVEEDORES = 2
NUM_COCINEROS = 2
INSUMOS_POR_PROVEEDOR = 10  # total esperado = NUM_PROVEEDORES * INSUMOS_POR_PROVEEDOR

mutex = threading.Semaphore(1)
vacios = threading.Semaphore(CAPACIDAD)
llenos = threading.Semaphore(0)
almacen = []

producidos = []
consumidos = []
lock_registro = threading.Lock()

def log(evento):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    hilo = threading.current_thread().name
    print(f"[{ts}] [{hilo}] {evento}")

def proveedor(id_proveedor, cantidad):
    for i in range(cantidad):
        insumo = f"P{id_proveedor}-{i:03d}"
        log(f"esperando espacio para insertar {insumo}")
        vacios.acquire()
        mutex.acquire()
        almacen.append(insumo)
        with lock_registro:
            producidos.append(insumo)
        log(f"insertado {insumo} (almacen={len(almacen)}/{CAPACIDAD})")
        mutex.release()
        llenos.release()
        time.sleep(random.uniform(0.01, 0.05))

def cocinero(id_cocinero):
    while True:
        log("esperando insumo")
        llenos.acquire()
        mutex.acquire()
        insumo = almacen.pop(0)
        mutex.release()
        vacios.release()
        if insumo is None:  # senal de cierre
            log("senal de cierre recibida, terminando")
            break
        with lock_registro:
            consumidos.append(insumo)
        log(f"retirado {insumo}, preparando plato")
        time.sleep(random.uniform(0.01, 0.05))

def main():
    hilos_cocineros = [
        threading.Thread(target=cocinero, args=(i,), name=f"Cocinero-{i}")
        for i in range(NUM_COCINEROS)
    ]
    hilos_proveedores = [
        threading.Thread(target=proveedor, args=(i, INSUMOS_POR_PROVEEDOR), name=f"Proveedor-{i}")
        for i in range(NUM_PROVEEDORES)
    ]

    for h in hilos_cocineros:
        h.start()
    for h in hilos_proveedores:
        h.start()
    for h in hilos_proveedores:
        h.join()

    for _ in hilos_cocineros:
        vacios.acquire()
        mutex.acquire()
        almacen.append(None)
        mutex.release()
        llenos.release()

    for h in hilos_cocineros:
        h.join()

    total_esperado = NUM_PROVEEDORES * INSUMOS_POR_PROVEEDOR
    perdidos = set(producidos) - set(consumidos)
    duplicados = len(consumidos) - len(set(consumidos))

    print("\n=== VERIFICACION ===")
    print(f"Producidos: {len(producidos)} | Consumidos: {len(consumidos)} | Esperados: {total_esperado}")
    print(f"Perdidos: {len(perdidos)} {sorted(perdidos) if perdidos else ''}")
    print(f"Duplicados: {duplicados}")
    if not perdidos and duplicados == 0 and len(consumidos) == total_esperado:
        print("RESULTADO: OK - sin perdidas ni duplicados")
    else:
        print("RESULTADO: FALLO")

if __name__ == "__main__":
    main()
import threading
import time
import random
import datetime

N_COCINEROS = 5 
utensilios = [threading.Lock() for _ in range(N_COCINEROS)]
fil_log = []

def cocinero_filosofo(id_coc, rondas):
    """
    Simula el ciclo de vida de cada cocinero en la estación central.
    Estrategia de Prevención de Deadlock: Ruptura de Simetría / Asignación Asimétrica.
    """
    izq = id_coc
    der = (id_coc + 1) % N_COCINEROS
    
    if id_coc == N_COCINEROS - 1:
        primero, segundo = der, izq
    else:
        primero, segundo = izq, der
        
    for r in range(rondas):
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_espera = f"[{now}] [Cocinero {id_coc}] Esperando utensilios (Ronda {r+1}/{rondas})"
        fil_log.append(log_espera)
        print(log_espera)
        time.sleep(random.uniform(0.005, 0.015))
        
        utensilios[primero].acquire()
        utensilios[segundo].acquire()
        
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_cocinando = f"[{now}] [Cocinero {id_coc}] Tomó utensilios {primero} y {segundo}. Preparando plato..."
        fil_log.append(log_cocinando)
        print(log_cocinando)
        
        time.sleep(random.uniform(0.01, 0.025))
        
        utensilios[segundo].release()
        utensilios[primero].release()
        
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_fin = f"[{now}] [Cocinero {id_coc}] Soltó utensilios {primero} y {segundo}. Plato terminado."
        fil_log.append(log_fin)
        print(log_fin)
        
        time.sleep(random.uniform(0.005, 0.015))

def ejecutar_estacion_central(rondas_por_cocinero=3):
    """
    Lanza la simulación multihilo para los 5 cocineros concurrentes.
    """
    global utensilios, fil_log
    utensilios = [threading.Lock() for _ in range(N_COCINEROS)]
    fil_log = []
    
    hilos = []
    for i in range(N_COCINEROS):
        t = threading.Thread(target=cocinero_filosofo, args=(i, rondas_por_cocinero))
        hilos.append(t)
        t.start()
        
    for t in hilos:
        t.join(timeout=10)
        
    print("\n--- SIMULACIÓN DE ESTACIÓN CENTRAL FINALIZADA CON ÉXITO ---")

if __name__ == "__main__":
    ejecutar_estacion_central()
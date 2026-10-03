import threading
import time

N_COCINEROS = 5 
utensilios = [threading.Lock() for _ in range(N_COCINEROS)]

def cocinero_incauto_deadlock(id_coc):
    izq = id_coc
    der = (id_coc + 1) % N_COCINEROS
    
    print(f"[Cocinero {id_coc}] Esperando utensilio izquierdo ({izq})...")
    
    utensilios[izq].acquire()
    print(f"--> [Cocinero {id_coc}] Tomó utensilio izquierdo {izq}. Esperando derecho {der}...")
    
    time.sleep(0.1)
    
    utensilios[der].acquire() 
    
    print(f"[Cocinero {id_coc}] ¡Logró preparar su plato!")
    utensilios[der].release()
    utensilios[izq].release()

if __name__ == "__main__":
    print("=== INICIANDO DEMOSTRACIÓN DE INTERBLOQUEO (DEADLOCK) ===")
    print("Nota: El programa se congelará porque todos esperarán un utensilio de forma circular.\n")
    
    hilos = []
    for i in range(N_COCINEROS):
        t = threading.Thread(target=cocinero_incauto_deadlock, args=(i,))
        hilos.append(t)
        t.start()
        
    for t in hilos:
        t.join()
# RECOMENDACIÓN TÉCNICA DE REEMPLAZO DE PÁGINAS

**Caso:** CocinaPerú Express — Gestión de Almacén y Memoria Virtual  
**Responsable:** Grupo M 

---

### 1. Recomendación para la Operación de la Cocina
Para la operación real de la cocina recomendamos implementar el algoritmo **LRU (Least Recently Used)**. 
En las pruebas del simulador, LRU mantuvo una tasa de aciertos de hasta **43.8%** y redujo los fallos de página frente a FIFO (por ejemplo, en la cadena de taller con 3 marcos logró **10 fallos** frente a los **12 de FIFO**, quedando a solo un **+25.0%** del Óptimo). LRU funciona bien porque aprovecha el principio de **localidad temporal**: si un ingrediente o utensilio se acaba de usar en una comanda, es muy probable que se vuelva a necesitar en los siguientes pasos del pedido.

### 2. Por qué el Algoritmo Óptimo no se puede aplicar en la práctica
Aunque el algoritmo **Óptimo (MIN/Belady)** obtiene el menor número de fallos teóricos (**9 en clase, 8 y 7 en taller**), **no es posible implementarlo en un sistema operativo real**. Para que funcione, el sistema tendría que predecir el futuro y saber de antemano el orden exacto en que los procesos van a solicitar páginas de memoria.
Por eso, el algoritmo Óptimo solo se utiliza como una **referencia teórica (benchmark)** para medir qué tan cerca logran quedar los algoritmos reales como LRU.

### 3. El problema con el Algoritmo FIFO
No conviene usar **FIFO** en el almacén debido a la **Anomalía de Belady**: al aumentar los marcos disponibles de 3 a 4 en la cadena de prueba, los fallos de página subieron de **9 a 10** en lugar de bajar. FIFO desaloja el insumo que llegó primero sin fijarse si la cocina lo sigue usando con frecuencia, lo que termina expulsando ingredientes clave que el cocinero necesita de inmediato.

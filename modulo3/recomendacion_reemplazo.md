# RECOMENDACIÓN TÉCNICA DE REEMPLAZO DE PÁGINAS

**Caso:** CocinaPerú Express — Gestión de Almacén y Memoria Virtual  
**Responsable:** Grupo M 

---

### 1. Recomendación Operativa para el Jefe de Cocina
Para la operación real de la cocina se recomienda implementar el algoritmo **LRU (Least Recently Used)**. 
Los resultados cuantitativos demuestran que LRU mantiene una tasa de aciertos de hasta **43.8%** y reduce los fallos de página frente a FIFO (por ejemplo, en la cadena de taller con 3 marcos logra **10 fallos** vs. **12 de FIFO**, con una brecha de solo **+25.0%** frente al Óptimo). LRU aprovecha el principio de **localidad temporal**: un ingrediente o utensilio utilizado recientemente tiene una probabilidad muy alta de volver a ser requerido en los siguientes pasos del pedido.

### 2. Por qué el Algoritmo Óptimo no es viable en la práctica
El algoritmo **Óptimo (MIN/Belady)** logra el mínimo absoluto de fallos teóricos (**9 en clase, 8 y 7 en taller**); sin embargo, **es físicamente imposible de implementar en un sistema operativo real**. Para funcionar, la MMU requeriría conocer con anticipación exacta la secuencia completa de accesos a memoria que realizarán los procesos en el futuro. 
Por este motivo, el algoritmo Óptimo se utiliza exclusivamente como una **cota superior ideal (benchmark)** contra la cual se mide la pérdida de rendimiento (*brecha frente al Óptimo*) de los algoritmos factibles.

### 3. Advertencia Crítica sobre el Algoritmo FIFO
Se desaconseja categóricamente el uso de **FIFO** en el almacén debido a su vulnerabilidad a la **Anomalía de Belady**: al aumentar la capacidad física de marcos de 3 a 4, los fallos de página se incrementan de **9 a 10** en lugar de disminuir. FIFO desaloja la página más antigua sin considerar su relevancia presente ni futura, pudiendo expulsar insumos esenciales que la cocina necesita de inmediato.

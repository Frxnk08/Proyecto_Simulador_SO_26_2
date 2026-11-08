# RECOMENDACIÓN TÉCNICA DE SISTEMAS DE ARCHIVOS

**Caso:** CocinaPerú Express — Estructura de Archivos y Asignación de Bloques  
**Responsable:** Grupo M  

---

### 1. Recomendación de Asignación de Bloques para DeliFIIS
Para las fichas de recetas oficiales (**P1 a P4**, que ocupan **10 bloques** en total) recomendamos **Asignación Contigua o Tabla FAT**. En las pruebas del simulador, la asignación contigua logró el acceso más rápido con solo **[1, 1, 1] lecturas** para los bloques lógicos 1, 3 y 5, permitiendo lecturas directas e inmediatas (tiempo constante). Para archivos dinámicos que crecen con los pedidos diarios como el inventario (**stock.csv**), recomendamos **Asignación Indexada** (**[2, 2, 2] lecturas**), ya que permite incorporar nuevos bloques dispersos sin reubicar los existentes y elimina la sobrecarga de atravesar enlaces en disco.

### 2. El problema de la Fragmentación Externa en Asignación Contigua
Aunque la asignación contigua es la más rápida para leer, no conviene utilizarla para archivos que crecen debido a la **fragmentación externa**. En la simulación del disco de control, habiendo **8 bloques libres** en total pero con un mayor hueco continuo de solo **5 bloques**, un nuevo archivo de **6 bloques** fue rechazado por falta de espacio contiguo consecutivo. En cambio, ese mismo archivo sí pudo almacenarse sin problemas mediante **Asignación Enlazada (6 bloques)** y mediante **Asignación Indexada (6 bloques de datos + 1 bloque índice = 7 bloques)**.

### 3. Política de Permisos y Seguridad por Rol
En la operación de la cocina recomendamos una política estricta de permisos por inodo. Las recetas maestras (`ceviche.txt`) deben configurarse con permisos **640 (rw-r-----)**: el **chef** puede modificarlas y los **ayudantes** pueden leerlas para preparar los pedidos sin alterar los ingredientes oficiales, mientras que los **visitantes** quedan bloqueados. El simulador verificó que al rechazar a un visitante en el paso 4 de apertura, el sistema operativo corta la operación de inmediato registrando exactamente **0 accesos de lectura al disco**, evitando consumo innecesario en el bus de E/S.

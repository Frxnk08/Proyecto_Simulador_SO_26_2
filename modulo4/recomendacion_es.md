# Recomendación Técnica de Entrada/Salida para la Torre de Control

**Sistema:** DeliFIIS — Módulo 4 (Entrada/Salida)  
**Para:** Jefe de Cocina / Director de Operaciones  
**De:** Alejandro del Salvador Meza Angulo (Rol 4 — Integración y Recomendación)  
**Fecha:** 31 de Octubre de 2026  

---

## 1. Diagnóstico del Hardware y Transferencias (Perfil `delifiis`)

Tras simular cuantitativamente las solicitudes de E/S generadas por los pedidos del restaurante, se han identificado cuellos de botella severos al emplear mecanismos de E/S tradicionales:

1. **Saturación por Interrupciones en Dispositivos de Alto Flujo:**
   Atender el disco o la red mediante **Interrupciones byte a byte** genera una sobrecarga crítica. Transferir un bloque de disco (4 096 B a $4\,\mu\text{s/byte}$) requiere $34\,406.4\,\mu\text{s}$ de tiempo CPU contra una transferencia total de $16\,384\,\mu\text{s}$ ($210\%$ de CPU), **saturando físicamente el procesador**. En la red ($1\,500\text{ B}$ a $1\,\mu\text{s/byte}$), el consumo alcanza $840\%$ de CPU.

2. **Ineficiencia Extrema de la Votación (Polling):**
   Aunque la Votación no satura la CPU (ocupa el $100\%$ exacto), desperdicia totalmente la capacidad de cómputo haciendo que el procesador espere activamente la finalización de cada transferencia ($471\,536\,\mu\text{s}$ de CPU para procesar $P1\text{--}P4$).

---

## 2. Recomendación de Métodos de E/S por Dispositivo

Basado en las métricas de CPU ($us$) obtenidas, se establece la siguiente política de asignación:

| Dispositivo | Tipo | Método Recomendado | Justificación Cuantitativa |
| :--- | :--- | :--- | :--- |
| **Disco de Recetas** | Bloque (4 096 B) | **DMA** | Reduce el costo de CPU de $16\,384\,\mu\text{s}$ (Votación) a solo **$38\,\mu\text{s}$ por bloque** ($0.232\%$ uso CPU). |
| **Ventanilla de Red** | Red (1 500 B) | **DMA** | Elimina la saturación por interrupciones, reduciendo la CPU de $12\,600\,\mu\text{s}$ a **$38\,\mu\text{s}$ por paquete**. |
| **Timbre de Control** | Carácter (1 B) | **Interrupciones** | Para $1\text{ B}$ a $100\,000\,\mu\text{s/byte}$, la interrupción cuesta solo **$8.4\,\mu\text{s}$** frente a los $100\,000\,\mu\text{s}$ que costaría la Votación. |
| **Impresora Comandas** | Carácter (Exclusivo)| **Spooling (Cola)** | Desacopla la velocidad de cocción de la velocidad de impresión física. |

> **Resultado del Modelo Integrado:** Aplicar la política **Recomendada** en la cadena de pedidos $P1\text{--}P4$ disminuye el consumo total de CPU de $471\,536\,\mu\text{s}$ (Votación) a **$337.6\,\mu\text{s}$**, logrando una **reducción del $99.93\%$ en el uso del procesador**.

---

## 3. Recomendación de Esquema de Búfer (Doble Búfer)

En el procesamiento iterativo de lotes de recetas (lectura de disco $L$ + preparación en CPU $P$):
* **Sin búfer:** El sistema opera de forma estrictamente secuencial ($n \times (L + P)$). Para 8 bloques ($L=8\text{ ms}, P=14\text{ ms}$), el tiempo total asciende a **$176\text{ ms}$**.
* **Doble Búfer:** Permite solapar la lectura del bloque $k+1$ con el procesamiento del bloque $k$. El tiempo total se reduce a $n \times \max(L,P) + \min(L,P) = 8 \times 14 + 8 =$ **$120\text{ ms}$** (ahorro del $31.8\%$).
* **Conclusión de Búfer:** Se recomienda utilizar **Doble Búfer** como estándar. Incorporar 3 o más búferes no ofrece ganancias adicionales ya que el sistema está acotado por el cuello de botella de la CPU.

---

*Nota: Los valores temporales y porcentajes de esta recomendación corresponden al modelo didáctico parametrizado `delifiis` del simulador SO-Sim.*
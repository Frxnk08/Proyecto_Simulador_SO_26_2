# Resultados — Semana 9, Parte C

Proyecto: **SO-Sim aplicado a DeliFIIS**
Responsable: **Frank Chuctaya — Persona 3**

## C.1 — Ejecutar y registrar SIGALRM

La predicción para un periodo de `0.50 s` y una observación de `3.25 s` es de
aproximadamente seis avisos:

```text
[0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
```

`interrupciones.py` realiza tres ejecuciones independientes, registra los
instantes realmente observados, las iteraciones de trabajo útil y confirma que
el temporizador queda desactivado mediante `getitimer()`.

**Estado de la evidencia:** pendiente de ejecución real en Linux/POSIX. El
entorno de desarrollo disponible es Windows y no dispone de WSL. No se han
simulado ni inventado avisos SIGALRM.

## C.2 — Modificar el periodo a 0,25 segundos

La predicción teórica es:

```text
3.25 / 0.25 = 13 avisos
```

Los instantes nominales van desde `0.25 s` hasta `3.25 s`. El aviso número 13
coincide con el límite temporal; su recepción efectiva puede variar según la
temporización del proceso y el instante exacto en que el bloque `finally`
desactive el temporizador. El programa no corrige ni fuerza el contador.

**Estado de la evidencia:** pendiente de ejecución real en Linux/POSIX por la
misma limitación indicada en C.1.

## C.3 — Versión por votación

`votacion.py` no instala manejadores ni temporizadores de señales. Consulta
`time.perf_counter()` continuamente y compara el tiempo transcurrido con el
próximo vencimiento. Es una espera activa real, no una lista predefinida.

La evidencia de la ejecución realizada en Windows se encuentra en
`evidencias/votacion_windows.txt`. Los valores medidos se consignan después de
ejecutar el programa y no deben considerarse constantes entre computadoras.

Medición obtenida el 27 de octubre de 2026:

- avisos detectados: `6`;
- instantes: `[0.500000, 1.000000, 1.500007, 2.000000, 2.500000, 3.000000] s`;
- consultas al reloj: `13 861 029`.

La cantidad elevada de consultas confirma que el programa permaneció en espera
activa. Este valor depende del procesador, del intérprete y de la carga del
sistema; no es un resultado teórico fijo.

## C.4 — Comparación técnica

SIGALRM permite que el proceso realice trabajo útil sin consultar continuamente
si llegó el siguiente vencimiento. El sistema entrega una señal y el manejador
registra el aviso. En la analogía DeliFIIS, el cocinero prepara otros platos y el
horno le avisa cuando corresponde.

En polling, el programa consulta el reloj repetidamente. Es equivalente a que el
cocinero revise el horno de manera constante. Aunque detecta los vencimientos,
consume tiempo de ejecución en la vigilancia activa.

El contador de iteraciones de trabajo útil permite comprobar que el flujo
principal siguió avanzando entre señales, pero **no representa por sí solo un
porcentaje de utilización de CPU**. Para medir utilización serían necesarias
métricas adicionales y una metodología de medición específica.

SIGALRM es una señal de software del sistema operativo. En esta práctica se usa
como analogía educativa de una interrupción de hardware; no es una interrupción
física producida directamente por un dispositivo.

## Validaciones realizadas

En Windows se completaron las siguientes comprobaciones:

- compilación sintáctica de los tres archivos Python;
- ayuda de ambas interfaces de línea de comandos;
- rechazo de periodos no positivos;
- comprobación AST de que `votacion.py` no importa `signal`;
- predicciones automáticas de 6 y 13 avisos;
- prueba en memoria de que el bloque `finally` desactiva el temporizador;
- ejecución real de polling durante 3,25 segundos;
- rechazo explícito de SIGALRM en una plataforma no POSIX.

La recepción real de SIGALRM y sus seis ejecuciones siguen pendientes de Linux.

## Parámetros compartidos de DeliFIIS

La configuración oficial del grupo está en `modulo4/parametros_delifiis.py`:

- entrega por byte: `8.0 µs`;
- copia por byte: `0.5 µs`;
- costo de interrupción: `3.5 µs`;
- preparación DMA: `16.0 µs`.

Son valores asumidos para el modelo educativo de la Parte D, no mediciones de
hardware. Los valores de control de la guía pertenecen a otra configuración y
no son los resultados principales de DeliFIIS. Ninguno reemplaza los periodos
de `0.50 s` y `0.25 s` establecidos para la Parte C.

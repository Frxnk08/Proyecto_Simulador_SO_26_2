# Semana 9 — Parte C: interrupciones y votación

Responsable: **Frank Chuctaya — Persona 3, Programador de Interrupciones**.

Esta carpeta implementa exclusivamente la Parte C de Entrada/Salida para SO-Sim,
aplicada al restaurante **DeliFIIS**.

## Archivos

- `interrupciones.py`: temporizador periódico con `SIGALRM` y trabajo útil simulado.
- `votacion.py`: versión independiente mediante polling y espera activa.
- `resultados_parte_C.md`: predicciones, mediciones y comparación C.1–C.4.
- `evidencias/`: salidas auténticas producidas por los programas.
- `../../parametros_delifiis.py`: parámetros oficiales compartidos del modelo educativo.

Los parámetros de rendimiento DeliFIIS pertenecen a la Parte D. No se usan como
periodos del temporizador: esta Parte C conserva `0.50 s` y `0.25 s`.

## Requisitos

- Python 3.10 o posterior.
- Linux u otro POSIX compatible para `SIGALRM`.
- La versión por polling también puede ejecutarse en Windows.

No se necesitan librerías externas.

## Ejecución de SIGALRM en Linux

Desde la raíz del repositorio:

```bash
python3 modulo4/semana09/parte_C_frank/interrupciones.py \
  --salida modulo4/semana09/parte_C_frank/evidencias/sigalrm_linux.txt
```

El comando realiza tres ejecuciones con periodo `0.50 s` y tres con `0.25 s`,
cada una durante `3.25 s`. La salida indica si el temporizador quedó desactivado.

## Ejecución de polling

```bash
python3 modulo4/semana09/parte_C_frank/votacion.py \
  --salida modulo4/semana09/parte_C_frank/evidencias/votacion.txt
```

## Validaciones rápidas

```bash
python3 -m py_compile \
  modulo4/parametros_delifiis.py \
  modulo4/semana09/parte_C_frank/interrupciones.py \
  modulo4/semana09/parte_C_frank/votacion.py

python3 modulo4/semana09/parte_C_frank/interrupciones.py --help
python3 modulo4/semana09/parte_C_frank/votacion.py --help
```

Un periodo o una duración menor o igual que cero produce un error. En una
plataforma sin `SIGALRM`, `interrupciones.py` termina con un mensaje explícito y
no fabrica resultados.

## Analogía DeliFIIS

- **SIGALRM:** el cocinero continúa preparando otros platos y el horno le avisa
  cuando corresponde revisar la cocción.
- **Polling:** el cocinero consulta constantemente el horno; puede detectar el
  momento esperado, pero emplea su atención en vigilarlo de forma continua.

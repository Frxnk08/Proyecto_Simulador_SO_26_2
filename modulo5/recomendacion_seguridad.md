# RECOMENDACIÓN TÉCNICA DE SEGURIDAD Y PROTECCIÓN

**Caso:** DeliFIIS — Protección de fichas, accesos y servidor de pedidos
**Responsable:** Grupo M (Rol 4, semana 11)
**Estado:** borrador con valores de control verificados. Los puntos marcados **[completar]** se llenan con la salida real de los archivos de los demás roles antes de entregar.

> Convención: **control** = valor de la PPT o práctica dirigida; **simulador** = lo que calcula nuestro código; **propio** = supuesto del equipo. Los tiempos de fuerza bruta usan 10⁹ intentos/s, un supuesto didáctico, no un dato de hardware real.

---

### 1. Orden de prioridad propuesto (a validar en equipo)

| # | Medida | Qué incidente del caso cubre | Evidencia |
|---|---|---|---|
| 1 | Contraseñas largas, hash con sal y segundo factor | Clave «ceviche123» adivinada; correo falso (phishing) | `sec_contrasenas.py`, `sec_amenazas.py` |
| 2 | Permisos de mínimo privilegio y cuentas individuales | Ayudante que modifica lo que solo debía leer; cuenta compartida | `sec_acceso.py`, `acceso_real.c`, `fs_permisos.py` |
| 3 | Firewall con política por defecto DROP | Puertos expuestos; pedidos falsos que saturan la ventanilla | `sec_firewall.py` |
| 4 | Huella y firma de las fichas | Receta alterada sin dejar rastro | `sec_cifrado.py` |
| 5 | Cifrado de la receta secreta | Receta copiada por un competidor | `sec_cifrado.py` |

**Criterio del orden:** primero lo que cierra la puerta de entrada (quién eres y qué puedes hacer), después lo que filtra el tráfico y por último lo que protege el contenido si lo anterior falla (defensa en capas). El orden no es único: si el chef prioriza la confidencialidad de la receta sobre la disponibilidad del servidor, el cifrado sube.

### 2. Contraseñas: la longitud pesa más que la variedad
Con el supuesto de control de 10⁹ intentos/s, una clave de **8 minúsculas** cae en ≈**3,5 minutos**, **8 letras y dígitos** en ≈**2,53 días**, **8 imprimibles** en ≈**70,55 días** y **12 minúsculas** en ≈**3,02 años**. Pasar de 8 a 12 caracteres aporta mucho más que ampliar el alfabeto. Además, sin sal el hash SHA-256 de «ceviche123» es siempre `55e006c75c2f282a…` (se nota la clave repetida y sirve a tablas precalculadas); con PBKDF2 y sal sale `d1dc65b61a3b43f6…` o `708b03c6f415e847…` según la sal. **[completar]** con la tabla propia de `sec_contrasenas.py` (velocidades 10⁹ y 10¹², supuestos del equipo) y con la política elegida.

### 3. Permisos: el modelo y el kernel coinciden
La matriz del chef se traduce a **640** (`receta.txt`), **660** (`stock.csv`) y **400** (`caja.log`). El simulador de S10 corta al usuario denegado en el paso 4 de la apertura, con **0 lecturas de disco**. En la propia cadena de custodia (`sec_integracion.py`): `ayudante` no puede leer `caja.log` ni escribir `ficha_P1.txt`, y puede escribir pero no leer `buzon_pedidos.txt` (420). **[completar]** con la tabla de `acceso_real.c` ejecutada con los tres usuarios en Linux y la conclusión sobre si el modelo coincide con el kernel. **Límite conocido:** el simulador no valora el permiso `x` de los directorios; Linux real sí.

### 4. Firewall: denegar por defecto
Con las reglas de control (22, 80, 443 ACCEPT; 3306 DROP) y política DROP, pasan tcp/22, tcp/80 y tcp/443 y se bloquean tcp/3306, tcp/23 y udp/53. Con política ACCEPT, tcp/23 y udp/53 pasarían; por eso se prefiere denegar y abrir solo lo imprescindible. El orden de las reglas importa: una regla `tcp/22 DROP` al inicio bloquea el 22 aunque exista una regla posterior que lo acepte. **[completar]** con las reglas propias (`REGLAS_DELIFIIS`) y el resultado sobre los 4 pedidos de M1 (tcp/443). Si se probó iptables en VM, anotar el orden en que aparecieron las reglas.

### 5. Integridad y confidencialidad de las fichas
Con el repo actual, la huella SHA-256 de `ficha_P1.txt` es `d27a687dff1b1207…`; tras `escribir_ficha(..., b'MODIFICADA', 'chef')` pasa a `5ab0e53df86574c5…`, así que la alteración se detecta, y el ayudante no puede escribirla (`PermissionError`). Con GPG, descifrar con la clave incorrecta da `Bad session key`, un llavero sin la clave privada da `No secret key`, y la firma pasa de `Good signature` a `BAD signature` si se modifica el archivo. **[completar]** con la salida de `sec_cifrado.py` en Linux/WSL. El cifrado simétrico es rápido pero exige compartir la clave; el asimétrico evita compartirla; GPG combina ambos.

### 6. Qué no cubre esta simulación
- Los valores de fuerza bruta son un modelo, no una medición de hardware.
- El firewall simulado omite las reglas de `lo` y de conexiones establecidas, y la cadena de iptables no filtra hasta enlazarla a INPUT.
- Solo hay tres usuarios (chef, ayudante, visitante); no se modelan ACL por usuario más finas.
- Ningún control basta solo: la recomendación es combinarlos.

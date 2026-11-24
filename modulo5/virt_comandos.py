from __future__ import annotations

import re

from virt_comun import imprimir_verificaciones

try:
    import sec_firewall
    REGLAS_DELIFIIS = getattr(
        sec_firewall,
        "REGLAS_DELIFIIS",
        [("tcp", 22, "ACCEPT"), ("tcp", 443, "ACCEPT"), ("tcp", 80, "DROP"), ("tcp", 3306, "DROP"), ("tcp", 8080, "DROP")],
    )
    POLITICA_DELIFIIS = getattr(sec_firewall, "POLITICA_DELIFIIS", "DROP")
except ImportError:
    sec_firewall = None
    REGLAS_DELIFIIS = [
        ("tcp", 22, "ACCEPT"), ("tcp", 443, "ACCEPT"),
        ("tcp", 80, "DROP"), ("tcp", 3306, "DROP"), ("tcp", 8080, "DROP"),
    ]
    POLITICA_DELIFIIS = "DROP"

PATRON_NOMBRE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def validar_nombre(nombre: str) -> str:
    """Valida nombres de VM o contenedor para evitar inyeccion de comandos."""
    if not isinstance(nombre, str) or not PATRON_NOMBRE.match(nombre):
        raise ValueError(f"Nombre invalido (posible inyeccion o caracteres no permitidos): {nombre!r}")
    return nombre


def comandos_vbox(nombre: str, memoria_mb: int, cpus: int | float, disco_mb: int) -> list[str]:
    """Genera las 7 instrucciones de VBoxManage para crear y configurar una VM."""
    validar_nombre(nombre)
    if memoria_mb <= 0 or cpus <= 0 or disco_mb <= 0:
        raise ValueError("Memoria, CPUs y disco deben ser mayores que cero")

    return [
        f"VBoxManage createvm --name {nombre} --ostype Ubuntu_64 --register",
        f"VBoxManage modifyvm {nombre} --memory {memoria_mb} --cpus {cpus:g} --nic1 nat",
        f"VBoxManage createmedium disk --filename {nombre}.vdi --size {disco_mb}",
        f"VBoxManage storagectl {nombre} --name SATA --add sata",
        f"VBoxManage storageattach {nombre} --storagectl SATA --port 0 --device 0 --type hdd --medium {nombre}.vdi",
        f'VBoxManage snapshot {nombre} take "instalacion-limpia"',
        "VBoxManage list vms",
    ]


def comando_docker_limitado(
    imagen: str,
    memoria_mb: int,
    cpus: int | float,
    comando: str,
) -> str:
    """Genera un comando docker run efimero con limites de memoria y CPU."""
    if not imagen or not comando:
        raise ValueError("La imagen y el comando no pueden estar vacios")
    if memoria_mb <= 0 or cpus <= 0:
        raise ValueError("La memoria y las CPUs deben ser mayores que cero")
    return f"docker run --rm --memory {memoria_mb}m --cpus {cpus:g} {imagen} {comando}"


def comando_docker_servicio(
    nombre: str,
    imagen: str,
    puerto_host: int | None = None,
    puerto_cont: int | None = None,
    memoria_mb: int | None = None,
    cpus: int | float | None = None,
    reglas: list[tuple[str, int, str]] | None = None,
    politica: str | None = None,
) -> str:
    """Genera comando docker run en segundo plano con orden fijo y filtro de firewall."""
    validar_nombre(nombre)
    if not imagen:
        raise ValueError("La imagen no puede estar vacia")

    if (puerto_host is None) != (puerto_cont is None):
        raise ValueError("Debe indicar tanto puerto_host como puerto_cont, o ninguno")

    if reglas is not None and puerto_host is not None:
        if sec_firewall is not None and hasattr(sec_firewall, "evaluar"):
            decision = sec_firewall.evaluar("tcp", puerto_host, reglas, politica)
            if decision != "ACCEPT":
                raise ValueError(f"Firewall bloquea el puerto tcp/{puerto_host} ({decision})")

    partes = ["docker", "run", "-d", "--name", nombre]
    if memoria_mb is not None:
        if memoria_mb <= 0:
            raise ValueError("memoria_mb debe ser mayor que cero")
        partes.extend(["--memory", f"{memoria_mb}m"])
    if cpus is not None:
        if cpus <= 0:
            raise ValueError("cpus debe ser mayor que cero")
        partes.extend(["--cpus", f"{cpus:g}"])
    if puerto_host is not None and puerto_cont is not None:
        partes.extend(["-p", f"{puerto_host}:{puerto_cont}"])
    partes.append(imagen)

    return " ".join(partes)


def verificar() -> list[tuple[str, bool]]:
    """Verifica comandos de control, propios, bloqueos de firewall e inyeccion."""
    pruebas: list[tuple[str, bool]] = []

    vbox_ctrl_esperado = [
        "VBoxManage createvm --name CocinaVM --ostype Ubuntu_64 --register",
        "VBoxManage modifyvm CocinaVM --memory 2048 --cpus 2 --nic1 nat",
        "VBoxManage createmedium disk --filename CocinaVM.vdi --size 20480",
        "VBoxManage storagectl CocinaVM --name SATA --add sata",
        "VBoxManage storageattach CocinaVM --storagectl SATA --port 0 --device 0 --type hdd --medium CocinaVM.vdi",
        'VBoxManage snapshot CocinaVM take "instalacion-limpia"',
        "VBoxManage list vms",
    ]
    pruebas.append((
        "control: comandos_vbox('CocinaVM', 2048, 2, 20480) devuelve las 7 lineas exactas",
        comandos_vbox("CocinaVM", 2048, 2, 20480) == vbox_ctrl_esperado,
    ))

    vbox_propio = comandos_vbox("DeliFIISVM", 2304, 2, 20480)
    pruebas.append((
        "propio: comandos_vbox('DeliFIISVM', 2304, 2, 20480) ajusta nombre, RAM y .vdi",
        vbox_propio[0] == "VBoxManage createvm --name DeliFIISVM --ostype Ubuntu_64 --register"
        and vbox_propio[1] == "VBoxManage modifyvm DeliFIISVM --memory 2304 --cpus 2 --nic1 nat"
        and vbox_propio[2] == "VBoxManage createmedium disk --filename DeliFIISVM.vdi --size 20480",
    ))

    cmd_lim = comando_docker_limitado("ubuntu:24.04", 100, 0.5, "sleep 5")
    cmd_srv = comando_docker_servicio("web", "nginx", 8080, 80)
    pruebas.append((
        "control: comando_docker_limitado coincide",
        cmd_lim == "docker run --rm --memory 100m --cpus 0.5 ubuntu:24.04 sleep 5",
    ))
    pruebas.append((
        "control: comando_docker_servicio('web', 'nginx', 8080, 80) coincide",
        cmd_srv == "docker run -d --name web -p 8080:80 nginx",
    ))

    cmd_p3 = comando_docker_servicio("delifiis-p3", "nginx", memoria_mb=960, cpus=0.5)
    cmd_web = comando_docker_servicio(
        "delifiis-web", "nginx", 443, 8443,
        memoria_mb=640, reglas=REGLAS_DELIFIIS, politica=POLITICA_DELIFIIS,
    )
    pruebas.append((
        "propio: comando_docker_servicio para delifiis-p3 (960m, 0.5 cpus)",
        cmd_p3 == "docker run -d --name delifiis-p3 --memory 960m --cpus 0.5 nginx",
    ))
    pruebas.append((
        "propio: comando_docker_servicio para delifiis-web con puerto 443 permitido",
        cmd_web == "docker run -d --name delifiis-web --memory 640m -p 443:8443 nginx",
    ))

    if sec_firewall is not None and hasattr(sec_firewall, "evaluar"):
        rechazos_ok = True
        for puerto_bloqueado in (80, 3306, 8080):
            try:
                comando_docker_servicio(
                    "test-fw", "nginx", puerto_bloqueado, 80,
                    reglas=REGLAS_DELIFIIS, politica=POLITICA_DELIFIIS,
                )
                rechazos_ok = False
            except ValueError:
                pass
        pruebas.append((
            "propio (S11 firewall): bloquea puertos 80, 3306 y 8080 con ValueError",
            rechazos_ok,
        ))
    else:
        print("[aviso] sec_firewall no disponible; se omite prueba de bloqueo de puertos")

    inyeccion_bloqueada = False
    try:
        validar_nombre("web; rm -rf /")
    except ValueError:
        inyeccion_bloqueada = True

    pruebas.append((
        "seguridad: rechaza nombres con inyeccion ('web; rm -rf /')",
        inyeccion_bloqueada,
    ))

    return pruebas


def main() -> int:
    print("=== MODULO 5 (SEMANA 12) - GENERADOR DE COMANDOS VBOX Y DOCKER ===")
    print("[aviso] Docker y VBoxManage no se ejecutan; se generan cadenas de texto validadas.")
    return imprimir_verificaciones(verificar())


if __name__ == "__main__":
    raise SystemExit(main())
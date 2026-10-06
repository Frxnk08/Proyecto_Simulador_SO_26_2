#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

struct Pedido {
    const char *id;
    const char *descripcion;
    int llegada;
    int duracion;
    int prioridad;
    pid_t pid;
};

static int escribir_json(const char *ruta, const struct Pedido *pedidos, size_t cantidad)
{
    FILE *archivo = fopen(ruta, "w");
    size_t i;

    if (archivo == NULL) {
        perror(ruta);
        return -1;
    }

    if (fprintf(archivo, "[\n") < 0) {
        goto error_escritura;
    }
    for (i = 0; i < cantidad; ++i) {
        if (fprintf(archivo,
                    "  {\n"
                    "    \"id\": \"%s\",\n"
                    "    \"pid\": %ld,\n"
                    "    \"descripcion\": \"%s\",\n"
                    "    \"llegada\": %d,\n"
                    "    \"duracion\": %d,\n"
                    "    \"prioridad\": %d\n"
                    "  }%s\n",
                    pedidos[i].id, (long)pedidos[i].pid, pedidos[i].descripcion,
                    pedidos[i].llegada, pedidos[i].duracion, pedidos[i].prioridad,
                    i + 1 < cantidad ? "," : "") < 0) {
            goto error_escritura;
        }
    }
    if (fprintf(archivo, "]\n") < 0) {
        goto error_escritura;
    }
    if (fclose(archivo) != 0) {
        perror(ruta);
        return -1;
    }
    return 0;

error_escritura:
    perror(ruta);
    fclose(archivo);
    return -1;
}

int main(int argc, char *argv[])
{
    struct Pedido pedidos[] = {
        {"P1", "Lomo Saltado", 0, 5, 3, 0},
        {"P2", "Ceviche Clasico", 1, 3, 4, 0},
        {"P3", "Anticuchos", 2, 8, 1, 0},
        {"P4", "Causa Limena", 3, 6, 2, 0}
    };
    const size_t cantidad = sizeof pedidos / sizeof pedidos[0];
    const char *ruta_json = argc == 2 ? argv[1] : "../pedidos.json";
    size_t creados = 0;
    size_t i;
    int fallo = 0;

    if (argc > 2) {
        fprintf(stderr, "Uso: %s [ruta_pedidos.json]\n", argv[0]);
        return EXIT_FAILURE;
    }

    /* Crear los cuatro hijos antes de esperar permite la preparación concurrente. */
    for (i = 0; i < cantidad; ++i) {
        pid_t pid = fork();
        if (pid < 0) {
            perror("fork");
            fallo = 1;
            break;
        }
        if (pid == 0) {
            execl("./preparar_pedido", "preparar_pedido", pedidos[i].id, (char *)NULL);
            perror("execl preparar_pedido");
            _exit(127);
        }
        pedidos[i].pid = pid;
        ++creados;
        printf("Mostrador: pedido %s, PID hijo %ld\n", pedidos[i].id, (long)pid);
        fflush(stdout);
    }

    for (i = 0; i < creados; ++i) {
        int estado;
        pid_t terminado;
        do {
            terminado = waitpid(pedidos[i].pid, &estado, 0);
        } while (terminado == -1 && errno == EINTR);

        if (terminado == -1) {
            perror("waitpid");
            fallo = 1;
        } else if (!WIFEXITED(estado) || WEXITSTATUS(estado) != 0) {
            fprintf(stderr, "El pedido %s (PID %ld) no terminó correctamente.\n",
                    pedidos[i].id, (long)pedidos[i].pid);
            fallo = 1;
        }
    }

    if (fallo || creados != cantidad) {
        fprintf(stderr, "No se generó el JSON porque falló un proceso.\n");
        return EXIT_FAILURE;
    }
    if (escribir_json(ruta_json, pedidos, cantidad) != 0) {
        return EXIT_FAILURE;
    }
    printf("Mostrador: cuatro pedidos finalizados; JSON generado en %s\n", ruta_json);
    return EXIT_SUCCESS;
}

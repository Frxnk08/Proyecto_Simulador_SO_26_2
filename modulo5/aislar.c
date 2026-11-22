#define _GNU_SOURCE
#include <sched.h>
#include <signal.h>
#include <sys/wait.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STACK_SIZE (1024 * 1024)
#define MAX_IDS 16
#define BUFFER_SIZE 4096

struct HijoArgs {
    const char *id;
    const char *ruta_ejecutable;
    int fd_escritura;
};

struct InfoPedido {
    const char *id;
    long pid_anfitrion;
    long pid_namespace;
    char hostname[64];
};

static int fn_hijo(void *arg)
{
    struct HijoArgs *hargs = (struct HijoArgs *)arg;
    char nuevo_host[64];

    snprintf(nuevo_host, sizeof(nuevo_host), "delifiis-%s", hargs->id);
    if (sethostname(nuevo_host, strlen(nuevo_host)) != 0) {
        perror("sethostname");
        _exit(1);
    }

    if (dup2(hargs->fd_escritura, STDOUT_FILENO) == -1) {
        perror("dup2");
        _exit(1);
    }
    close(hargs->fd_escritura);

    printf("hostname=%s\n", nuevo_host);
    fflush(stdout);

    execl(hargs->ruta_ejecutable, "preparar_pedido", hargs->id, (char *)NULL);
    perror("execl");
    _exit(127);
}

static int escribir_json(const char *ruta, struct InfoPedido *pedidos, int cantidad)
{
    FILE *f = fopen(ruta, "w");
    int i;

    if (!f) {
        perror(ruta);
        return -1;
    }

    fprintf(f, "[\n");
    for (i = 0; i < cantidad; i++) {
        fprintf(f, "  {\"id\": \"%s\", \"pid_anfitrion\": %ld, \"pid_namespace\": %ld, \"hostname\": \"%s\"}%s\n",
                pedidos[i].id,
                pedidos[i].pid_anfitrion,
                pedidos[i].pid_namespace,
                pedidos[i].hostname,
                (i + 1 < cantidad) ? "," : "");
    }
    fprintf(f, "]\n");
    fclose(f);
    return 0;
}

int main(int argc, char *argv[])
{
    char host_inicial[256] = {0};
    char host_final[256] = {0};
    const char *ruta_json;
    const char *ruta_preparar;
    int cantidad, i;
    struct InfoPedido pedidos[MAX_IDS];
    struct HijoArgs args[MAX_IDS];
    char *pilas[MAX_IDS];
    int fds_lectura[MAX_IDS];
    int fallo = 0;

    if (argc < 4) {
        fprintf(stderr, "Uso: %s salida.json ruta_a_preparar_pedido ID [ID ...] (hasta 16 IDs)\n", argv[0]);
        return 2;
    }

    cantidad = argc - 3;
    if (cantidad > MAX_IDS) {
        fprintf(stderr, "Error: Maximo %d IDs permitidos (recibidos: %d)\n", MAX_IDS, cantidad);
        return 2;
    }

    ruta_json = argv[1];
    ruta_preparar = argv[2];

    if (gethostname(host_inicial, sizeof(host_inicial)) != 0) {
        perror("gethostname inicial");
        return 1;
    }

    for (i = 0; i < cantidad; i++) {
        int pipefd[2];
        pid_t pid;

        pedidos[i].id = argv[3 + i];
        pedidos[i].pid_anfitrion = -1;
        pedidos[i].pid_namespace = -1;
        pedidos[i].hostname[0] = '\0';

        if (pipe(pipefd) != 0) {
            perror("pipe");
            fallo = 1;
            break;
        }

        pilas[i] = malloc(STACK_SIZE);
        if (!pilas[i]) {
            perror("malloc stack");
            close(pipefd[0]);
            close(pipefd[1]);
            fallo = 1;
            break;
        }

        args[i].id = pedidos[i].id;
        args[i].ruta_ejecutable = ruta_preparar;
        args[i].fd_escritura = pipefd[1];
        fds_lectura[i] = pipefd[0];

        pid = clone(fn_hijo, pilas[i] + STACK_SIZE, CLONE_NEWPID | CLONE_NEWUTS | SIGCHLD, &args[i]);
        if (pid == -1) {
            if (errno == EPERM) {
                fprintf(stderr, "Se requiere root (CAP_SYS_ADMIN)\n");
                close(pipefd[0]);
                close(pipefd[1]);
                free(pilas[i]);
                return 77;
            }
            perror("clone");
            close(pipefd[0]);
            close(pipefd[1]);
            free(pilas[i]);
            fallo = 1;
            break;
        }

        close(pipefd[1]);
        pedidos[i].pid_anfitrion = (long)pid;
    }

    if (fallo) {
        return 1;
    }

    for (i = 0; i < cantidad; i++) {
        char buffer[BUFFER_SIZE];
        ssize_t bytes_leidos;
        int status;
        char acumulado[BUFFER_SIZE] = {0};
        size_t total = 0;
        char *linea;

        while ((bytes_leidos = read(fds_lectura[i], buffer, sizeof(buffer) - 1)) > 0) {
            if (total + (size_t)bytes_leidos < sizeof(acumulado) - 1) {
                memcpy(acumulado + total, buffer, (size_t)bytes_leidos);
                total += (size_t)bytes_leidos;
                acumulado[total] = '\0';
            }
        }
        close(fds_lectura[i]);

        waitpid((pid_t)pedidos[i].pid_anfitrion, &status, 0);
        free(pilas[i]);

        linea = strtok(acumulado, "\r\n");
        while (linea != NULL) {
            char temp_host[64];
            long temp_pid;

            if (sscanf(linea, "hostname=%63s", temp_host) == 1) {
                strncpy(pedidos[i].hostname, temp_host, sizeof(pedidos[i].hostname) - 1);
            } else if (sscanf(linea, "Preparando pedido %*s en PID %ld", &temp_pid) == 1) {
                pedidos[i].pid_namespace = temp_pid;
            }
            linea = strtok(NULL, "\r\n");
        }
    }

    if (escribir_json(ruta_json, pedidos, cantidad) != 0) {
        return 1;
    }

    if (gethostname(host_final, sizeof(host_final)) == 0) {
        if (strcmp(host_inicial, host_final) == 0) {
            printf("hostname_anfitrion_intacto=1\n");
        }
    }

    return 0;
}

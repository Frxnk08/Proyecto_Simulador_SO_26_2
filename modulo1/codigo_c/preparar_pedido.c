#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main(int argc, char *argv[])
{
    const char *pedido;
    pid_t pid;

    if (argc != 2 || argv[1][0] != 'P' || argv[1][1] < '1' ||
        argv[1][1] > '4' || argv[1][2] != '\0') {
        fprintf(stderr, "Uso: %s P1|P2|P3|P4\n", argv[0]);
        return EXIT_FAILURE;
    }

    pedido = argv[1];
    pid = getpid();
    printf("Preparando pedido %s en PID %ld\n", pedido, (long)pid);
    fflush(stdout);

    /* La ráfaga simulada del planificador no es el tiempo real de preparación. */
    sleep(2);

    printf("Pedido %s terminado en PID %ld\n", pedido, (long)pid);
    return EXIT_SUCCESS;
}

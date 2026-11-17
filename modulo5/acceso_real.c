#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

int main(int argc, char *argv[])
{
    int i, fallo = 0;
    struct stat st;
    if (argc < 2) {
        fprintf(stderr, "Uso: %s ruta [ruta ...]\n", argv[0]);
        return 1;
    }
    for (i = 1; i < argc; i++) {
        if (stat(argv[i], &st) != 0) {
            perror(argv[i]);
            fallo = 1;
            continue;
        }
        printf("%s %o %s %s\n", argv[i], (unsigned)(st.st_mode & 0777),
               access(argv[i], R_OK) == 0 ? "SI" : "NO",
               access(argv[i], W_OK) == 0 ? "SI" : "NO");
    }
    return fallo;
}
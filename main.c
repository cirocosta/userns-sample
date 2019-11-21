#define _GNU_SOURCE
#include <fcntl.h>
#include <sched.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

#include <sys/sysmacros.h>
#ifndef NS_GET_USERNS
#define NSIO 0xb7
#define NS_GET_USERNS _IO(NSIO, 0x1)
#endif

#define STACK_SIZE 1024 * 1024

static char child_stack[STACK_SIZE];
static const char* mapping = "0 1001 1";

void
show_userns()
{
        int err;
        char buf[128] = { 0 };

        err = readlink("/proc/self/ns/user", buf, 128);
        if (err == -1) {
                perror("readlink");
                exit(1);
        }

        printf("userns: %s\n", buf);
}

void
show_info(char* fname)
{
        int fd, err;
        struct stat sb;

        fd = openat(AT_FDCWD, fname, O_RDONLY);
        if (fd == -1) {
                perror("openat");
                exit(1);
        }

        err = fstat(fd, &sb);
        if (err == -1) {
                perror("fstat");
                exit(1);
        }

        close(fd);

        show_userns();
        printf("%-8s %-8s %-8d\n", "process", "euid", geteuid());
        printf("%-8s %-8s %-8d\n", "process", "egid", getegid());
        printf("%-8s %-8s %-8d\n", "file", "uid", sb.st_uid);
        printf("%-8s %-8s %-8d\n", "file", "gid", sb.st_gid);
}

static int
child(void* arg)
{
        int fd, n;

        fd = open("/proc/self/uid_map", O_RDWR);
        if (fd == -1) {
                perror("open");
                exit(1);
        }

        n = write(fd, mapping, sizeof(mapping));
        if (n == -1) {
                perror("write");
                exit(1);
        }

        close(fd);

        show_info((char*)arg);
}

int
main(int argc, char** argv)
{
        int err;
        pid_t child_pid;

        int flags = CLONE_NEWUSER | SIGCHLD;
        void* stack = child_stack + STACK_SIZE;

        if (argc != 2) {
                printf("usage: %s <filename>\n", argv[0]);
                return 1;
        }

        setbuf(stdout, NULL);
        setbuf(stderr, NULL);

        show_info(argv[1]);

        child_pid = clone(child, stack, flags, argv[1]);
        if (child_pid == -1) {
                perror("clone: ");
                return 1;
        }

        err = waitpid(child_pid, NULL, 0);
        if (err == -1) {
                perror("waitpid: ");
                return 1;
        }

        return 0;
}

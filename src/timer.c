#define _POSIX_C_SOURCE 200809L
#include "../include/timer.h"

double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}
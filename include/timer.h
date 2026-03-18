#include <time.h>

#ifndef TIMER_H
#define TIMER_H
/*
 * Returns the current time as a double in seconds.
 * Uses CLOCK_MONOTONIC which is not affected by system clock changes,
 * making it suitable for measuring elapsed time.
 *
 * Returns:
 *     Current time in seconds as a double (nanosecond precision).
 */
double get_time();
#endif
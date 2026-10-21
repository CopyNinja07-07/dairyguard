/* Desktop driver for the C core: reads "temperature dt_hours" pairs on stdin and prints the status after each one.
 * Build: gcc -O2 -std=c99 -Idairyguard_monitor host_test.c dairyguard_monitor/dg_core.c -lm -o host_test */
#include <stdio.h>
#include "dg_core.h"

int main(void) {
    dg_monitor m; dg_init(&m, &DG_MILK, 20261021u);
    float T, dt;
    while (scanf("%f %f", &T, &dt) == 2) {
        dg_update(&m, T, dt);
        dg_status s = dg_status_now(&m);
        printf("%.4f %.6f %.4f %.3f %.3f %d\n", m.hours, s.shelf_life_used, s.probability_crossed,
               s.hours_left_4C, s.hours_left_4C_cautious, s.state);
    }
    return 0;
}

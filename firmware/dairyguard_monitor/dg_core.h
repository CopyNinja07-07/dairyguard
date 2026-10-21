/* DairyGuard Kinetic monitor: portable C core for microcontrollers (ESP32, Arduino, STM32) and desktops.
 *
 * Each temperature reading adds dt / SL(T) to the consumed shelf life (CSL), where SL(T) is the modified-Gompertz
 * time to the limit at a steady temperature T under the square-root growth law. The same sum is kept for
 * DG_DRAWS plausible batches drawn from the product's between-batch spread, which gives the probability that the
 * batch has crossed the limit and a cautious estimate of the hours left at 4 deg C.
 *
 * Memory: about 30 bytes per plausible batch (DG_DRAWS = 64 uses under 2 kB). No dynamic allocation.
 * The Python package (src/dairyguard) is the reference; tests/test_firmware.py checks this code against it. */
#ifndef DG_CORE_H
#define DG_CORE_H
#include <stdint.h>

#ifndef DG_DRAWS
#define DG_DRAWS 64
#endif

typedef struct {
    float b;          /* square-root slope, 1/(h^0.5 K) */
    float Tmin;       /* minimum growth temperature, deg C */
    float h0;         /* lag parameter */
    float log10N0;    /* starting count, log10 CFU/mL */
    float log10Nmax;  /* maximum count, log10 CFU/mL */
    float limit;      /* limit, CFU/mL */
    float cv_b;       /* between-batch coefficient of variation of b */
    float Tmin_sd;    /* between-batch SD of Tmin, K */
    float h0_lo, h0_hi;
    float n0_lo, n0_hi;
} dg_product;

typedef struct {
    float csl;                      /* consumed shelf life of the nominal batch */
    float csl_draw[DG_DRAWS];
    float b[DG_DRAWS], Tmin[DG_DRAWS], h0[DG_DRAWS], n0[DG_DRAWS];
    float sl4[DG_DRAWS];            /* each batch's shelf life at 4 deg C, for hours-left */
    float hours;
    dg_product p;
} dg_monitor;

typedef struct {
    float shelf_life_used;      /* 1.0 = limit predicted */
    float probability_crossed;  /* 0..1 */
    float hours_left_4C;        /* typical batch held at 4 deg C */
    float hours_left_4C_cautious; /* 9 batches in 10 last at least this long */
    uint8_t state;              /* 0 fresh, 1 use soon, 2 check before use, 3 likely over the limit */
} dg_status;

extern const dg_product DG_MILK;

float dg_shelf_life(float T, float b, float Tmin, float h0, float log10N0, float log10Nmax, float limit);
void dg_init(dg_monitor *m, const dg_product *p, uint32_t seed);
void dg_update(dg_monitor *m, float temperature_C, float dt_hours);
dg_status dg_status_now(const dg_monitor *m);

#endif

#include "dg_core.h"
#include <math.h>

/* Pasteurised milk, psychrotrophic spoilage flora; FSSAI limit 3e4 CFU/mL (see data/params.csv). */
const dg_product DG_MILK = {0.030f, -7.7f, 3.8f, 1.7f, 9.0f, 3e4f, 0.10f, 1.5f, 2.5f, 5.0f, 1.5f, 2.0f};

float dg_shelf_life(float T, float b, float Tmin, float h0, float log10N0, float log10Nmax, float limit) {
    float d = T > Tmin ? b * (T - Tmin) : 0.0f;
    float mu = d * d;                              /* natural-log growth rate, 1/h */
    if (mu < 1e-9f) mu = 1e-9f;
    float mu10 = mu / 2.302585093f;
    float A = log10Nmax - log10N0;
    float L = log10f(limit) - log10N0;
    float lam = h0 / mu;
    return lam + A / (mu10 * 2.718281828f) * (1.0f - logf(-logf(L / A)));
}

/* xorshift32 and Box-Muller: small, deterministic, no library state */
static uint32_t rng_next(uint32_t *s) { uint32_t x = *s; x ^= x << 13; x ^= x >> 17; x ^= x << 5; return *s = x; }
static float rng_unit(uint32_t *s) { return ((rng_next(s) >> 8) + 0.5f) / 16777216.0f; }
static float rng_normal(uint32_t *s) { float u = rng_unit(s), v = rng_unit(s); return sqrtf(-2.0f * logf(u)) * cosf(6.283185307f * v); }

void dg_init(dg_monitor *m, const dg_product *p, uint32_t seed) {
    uint32_t s = seed ? seed : 2463534242u;
    m->p = *p; m->csl = 0.0f; m->hours = 0.0f;
    for (int k = 0; k < DG_DRAWS; k++) {
        m->b[k] = p->b * expf(p->cv_b * rng_normal(&s) - 0.5f * p->cv_b * p->cv_b);
        m->Tmin[k] = p->Tmin + p->Tmin_sd * rng_normal(&s);
        m->h0[k] = p->h0_lo + (p->h0_hi - p->h0_lo) * rng_unit(&s);
        m->n0[k] = p->n0_lo + (p->n0_hi - p->n0_lo) * rng_unit(&s);
        m->csl_draw[k] = 0.0f;
        m->sl4[k] = dg_shelf_life(4.0f, m->b[k], m->Tmin[k], m->h0[k], m->n0[k], p->log10Nmax, p->limit);
    }
}

void dg_update(dg_monitor *m, float T, float dt) {
    const dg_product *p = &m->p;
    m->csl += dt / dg_shelf_life(T, p->b, p->Tmin, p->h0, p->log10N0, p->log10Nmax, p->limit);
    for (int k = 0; k < DG_DRAWS; k++)
        m->csl_draw[k] += dt / dg_shelf_life(T, m->b[k], m->Tmin[k], m->h0[k], m->n0[k], p->log10Nmax, p->limit);
    m->hours += dt;
}

static void sort_floats(float *a, int n) {           /* insertion sort: n is small */
    for (int i = 1; i < n; i++) { float v = a[i]; int j = i - 1; while (j >= 0 && a[j] > v) { a[j + 1] = a[j]; j--; } a[j + 1] = v; }
}

dg_status dg_status_now(const dg_monitor *m) {
    dg_status s; float left[DG_DRAWS]; int over = 0;
    for (int k = 0; k < DG_DRAWS; k++) {
        if (m->csl_draw[k] >= 1.0f) over++;
        float r = 1.0f - m->csl_draw[k];
        left[k] = (r > 0.0f ? r : 0.0f) * m->sl4[k];
    }
    sort_floats(left, DG_DRAWS);
    s.shelf_life_used = m->csl;
    s.probability_crossed = (float)over / DG_DRAWS;
    s.hours_left_4C = left[DG_DRAWS / 2];
    s.hours_left_4C_cautious = left[DG_DRAWS / 10];
    s.state = s.probability_crossed < 0.15f ? 0 : s.probability_crossed < 0.40f ? 1 : s.probability_crossed < 0.75f ? 2 : 3;
    return s;
}

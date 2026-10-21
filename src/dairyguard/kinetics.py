"""DairyGuard kinetic kernel: reference (truth) model + edge estimator.

Truth     : Baranyi-Roberts dynamic growth with Ratkowsky sqrt secondary model (ln basis).
Estimator : Modified-Gompertz isothermal shelf life SL(T) + fractional accumulation
            CSL = sum(dt / SL(T_i))  (time-temperature-tolerance idea).
The two are structurally different on purpose, so the benchmark is not circular.
"""
import numpy as np

LN10 = np.log(10.0)


def mu_sqrt(T, b, Tmin):
    """Ratkowsky: sqrt(mu) = b (T - Tmin) for T > Tmin; mu in 1/h (ln basis)."""
    return np.where(T > Tmin, (b * (T - Tmin)) ** 2, 0.0)


def sl_gompertz(T, b, Tmin, h0, log10N0, log10Nmax, Nlimit):
    """Closed-form time (h) for Modified Gompertz to reach Nlimit at constant T.
    SL = lam + A/(mu_log10 * e) * [1 - ln(-ln(L/A))],  lam = h0/mu_ln."""
    mu = np.maximum(mu_sqrt(T, b, Tmin), 1e-9)
    mu10 = mu / LN10
    A = log10Nmax - log10N0
    L = np.log10(Nlimit) - log10N0
    lam = h0 / mu
    return lam + A / (mu10 * np.e) * (1.0 - np.log(-np.log(L / A)))


def make_sl_lookup(b, Tmin, h0, log10N0, log10Nmax, Nlimit, lo=-5.0, hi=50.0, step=0.01):
    grid = np.arange(lo, hi + step, step)
    sl = sl_gompertz(grid, b, Tmin, h0, log10N0, log10Nmax, Nlimit)
    return lambda T: np.interp(T, grid, sl)


def baranyi_isothermal_time(T, b, Tmin, h0, log10N0, log10Nmax, Nlimit, dt=1 / 60, tmax=2000):
    """Numerical time-to-limit for the truth model at constant T (used in tests)."""
    mu = float(mu_sqrt(np.array(T), b, Tmin))
    y = np.log(10 ** log10N0)
    ymax = np.log(10 ** log10Nmax)
    yl = np.log(Nlimit)
    q = 1.0 / (np.exp(h0) - 1.0)
    t = 0.0
    while y < yl and t < tmax:
        a = q / (1 + q)
        y += dt * mu * a * (1 - np.exp(y - ymax))
        q += dt * mu * q
        t += dt
    return t

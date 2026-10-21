import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
from dairyguard.kinetics import mu_sqrt, sl_gompertz, make_sl_lookup, baranyi_isothermal_time

P = dict(b=0.016, Tmin=-7.75, h0=1.5, log10N0=1.7, log10Nmax=9.0)


def test_gompertz_matches_exponential_growth_estimate():
    T = 8.0
    mu = float(mu_sqrt(np.array(T), P["b"], P["Tmin"]))
    sl = sl_gompertz(T, P["b"], P["Tmin"], P["h0"], P["log10N0"], P["log10Nmax"], 3e4)
    approx = P["h0"] / mu + np.log(3e4 / 10 ** P["log10N0"]) / mu
    assert abs(sl - approx) / approx < 0.06


def test_truth_and_estimator_agree_isothermally_with_equal_params():
    for T in (4.0, 8.0, 18.0):
        a = sl_gompertz(T, P["b"], P["Tmin"], P["h0"], P["log10N0"], P["log10Nmax"], 3e4)
        b = baranyi_isothermal_time(T, P["b"], P["Tmin"], P["h0"], P["log10N0"], P["log10Nmax"], 3e4)
        assert abs(a - b) / a < 0.12, (T, a, b)


def test_lookup_matches_closed_form():
    sl = make_sl_lookup(P["b"], P["Tmin"], P["h0"], P["log10N0"], P["log10Nmax"], 3e4)
    for T in (3.7, 9.123, 25.5):
        exact = sl_gompertz(T, P["b"], P["Tmin"], P["h0"], P["log10N0"], P["log10Nmax"], 3e4)
        assert abs(float(sl(T)) - float(exact)) / float(exact) < 1e-3


def test_shelf_life_decreases_with_temperature():
    Ts = np.linspace(0, 35, 36)
    sl = sl_gompertz(Ts, P["b"], P["Tmin"], P["h0"], P["log10N0"], P["log10Nmax"], 3e4)
    assert np.all(np.diff(sl) < 0)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)

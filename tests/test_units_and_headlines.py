"""Unit audit for growth rates, and regression checks that pin the headline numbers to the saved results.

ComBase reports maximum growth rates in log10 units (log10 CFU/mL per hour). The model works in natural-log
units, so every rate must be multiplied by ln(10) before it is fitted. These tests check that this happens,
and that the numbers quoted on the website, in the demo and in the technical report still follow from the result files."""
import json
import math
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
import numpy as np
import pandas as pd
from dairyguard.kinetics import LN10, mu_sqrt, sl_gompertz

J = lambda *p: json.load(open(os.path.join(ROOT, *p)))


def _tasmania():
    d = pd.read_csv(os.path.join(ROOT, "data", "combase_tasmania_pasteurised_milk.csv"))
    return d[d.temp_C < 30]


def test_combase_rates_are_log10_and_converted_to_ln():
    d = _tasmania()
    b_ln, i_ln = np.polyfit(d.temp_C, np.sqrt(d.max_rate_log10_per_h * LN10), 1)
    b_10, _ = np.polyfit(d.temp_C, np.sqrt(d.max_rate_log10_per_h), 1)
    saved = J("results", "validation_combase.json")["all"]
    # The saved fit is the natural-log one, not the raw log10 one.
    assert abs(b_ln - saved["b_ln"]) < 5e-4
    assert abs(-i_ln / b_ln - saved["Tmin_C"]) < 0.01
    # Converting units scales the square-root slope by sqrt(ln 10) and leaves Tmin unchanged.
    assert abs(b_ln / b_10 - math.sqrt(LN10)) < 1e-9


def test_gompertz_shelf_life_uses_consistent_units():
    # With no lag, the Gompertz time to a limit scales as 1/mu: halving the rate doubles the time.
    T, b, Tmin = 8.0, 0.03, -6.0
    sl1 = float(sl_gompertz(T, b, Tmin, 0.0, 2.0, 9.0, 1e6))
    sl2 = float(sl_gompertz(T, b / math.sqrt(2), Tmin, 0.0, 2.0, 9.0, 1e6))
    assert abs(sl2 / sl1 - 2.0) < 1e-9
    # A natural-log rate of mu means a log10 rate of mu / ln 10, so 4 log10 units of growth take
    # at least 4 * ln10 / mu hours (the Gompertz curve is never faster than its maximum rate).
    mu = float(mu_sqrt(T, b, Tmin))
    assert sl1 >= 4 * LN10 / mu


def test_headline_biology_gap_and_sensor_gain():
    base = J("results", "summary.json")["base"]
    assert round(base["biology_gap"]["min"], 2) == 0.27
    assert round(base["biology_gap"]["max"], 2) == 0.40
    assert base["sensor_PT1000_vs_DS18B20"]["max"] <= 0.02
    assert base["sampling_60_vs_1"]["n_excl_zero"] == 1


def test_headline_calorimetry_fraction():
    d = pd.read_csv(os.path.join(ROOT, "results", "calorimetry_info.csv"))
    w = d.pivot_table(index=["thr", "tau", "cv"], columns="method", values="AUC")
    frac = 100 * (w.calorimetry - w.nominal) / (w.oracle - w.nominal)
    assert round(frac.min()) == 69 and round(frac.max()) == 94


def test_numbers_file_matches_results():
    tex = open(os.path.join(ROOT, "generated", "numbers.tex")).read()
    mac = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}", tex))
    base = J("results", "summary.json")["base"]
    assert mac["NumBaseGapMin"] == "%.2f" % base["biology_gap"]["min"]
    assert mac["NumBaseGapMax"] == "%.2f" % base["biology_gap"]["max"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)

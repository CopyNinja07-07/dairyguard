"""Tests for the monitor, the command line, log reading and the growth laws."""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
import numpy as np

from dairyguard import ColdChainMonitor, growthlaws as G, sl_gompertz
from dairyguard.io import read_log, write_log


def test_monitor_matches_closed_form_at_constant_temperature():
    m = ColdChainMonitor("milk", n_draws=50)
    for _ in range(40):
        s = m.update(8.0, 0.5)
    p = m.product
    expect = 20.0 / float(sl_gompertz(np.array(8.0), p.b, p.Tmin, p.h0, p.log10N0, p.log10Nmax, p.limit))
    assert abs(s.shelf_life_used - expect) < 1e-9


def test_warmer_trip_is_riskier():
    cold, warm = ColdChainMonitor("milk"), ColdChainMonitor("milk")
    t = np.arange(0, 48, 0.25)
    sc = cold.run(t, np.full(len(t), 4.0))[-1]
    sw = warm.run(t, np.where((t > 20) & (t < 26), 15.0, 4.0))[-1]
    assert sw.probability_crossed >= sc.probability_crossed
    assert sw.shelf_life_used > sc.shelf_life_used
    assert sw.hours_left_at_4C < sc.hours_left_at_4C
    assert sw.hours_left_at_4C_cautious <= sw.hours_left_at_4C


def test_log_roundtrip_and_cli():
    t = np.arange(0, 30, 0.25)
    T = np.where((t > 10) & (t < 12), 17.5, 4.0)
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "trip.csv")
        write_log(f, t, T)
        t2, T2 = read_log(f)
        assert np.allclose(t2, t) and np.allclose(T2, T)
        env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))
        out = subprocess.check_output([sys.executable, "-m", "dairyguard", "assess", f, "--json"], env=env, text=True)
        r = json.loads(out)
        assert 0 <= r["probability_crossed"] <= 1 and r["log"]["readings"] == len(t)


def test_square_root_recovers_known_parameters():
    rng = np.random.default_rng(0)
    T = rng.uniform(2, 15, 80)
    mu = (0.03 * (T + 7.7)) ** 2 * np.exp(rng.normal(0, 0.05, 80))
    law = G.SquareRoot().fit(T, mu)
    assert abs(law.b - 0.03) < 0.003 and abs(law.Tmin + 7.7) < 1.0


def test_neural_law_rises_with_temperature():
    T = np.linspace(0, 15, 30)
    mu = (0.025 * (T + 3)) ** 2
    net = G.MonotoneNet(units=3, ensemble=2, seed=0).fit(T, mu)
    grid = np.linspace(-5, 25, 200)
    assert np.all(np.diff(net.predict(grid)) >= -1e-12)
    assert G.performance(net.predict(T), mu)["Af"] < 1.1


def test_combase_rates_converted():
    assert abs(G.to_ln_rate(1.0) - np.log(10)) < 1e-12


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)

"""The microcontroller code (firmware/) must give the same shelf-life numbers as the Python reference."""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
import numpy as np

from dairyguard import ColdChainMonitor


def run_c(pairs):
    cc = shutil.which("gcc") or shutil.which("cc") or shutil.which("clang")
    if cc is None:
        return None
    fw = os.path.join(ROOT, "firmware")
    with tempfile.TemporaryDirectory() as d:
        exe = os.path.join(d, "host_test")
        subprocess.check_call([cc, "-O2", "-std=c99", "-I", os.path.join(fw, "dairyguard_monitor"),
                               os.path.join(fw, "host_test.c"), os.path.join(fw, "dairyguard_monitor", "dg_core.c"),
                               "-lm", "-o", exe])
        out = subprocess.run([exe], input="\n".join(f"{T} {dt}" for T, dt in pairs), capture_output=True, text=True,
                             check=True).stdout
    return np.array([[float(x) for x in line.split()] for line in out.strip().splitlines()])


def trip():
    rng = np.random.default_rng(3)
    T = 4 + 0.3 * rng.normal(size=300)
    T[100:112] = 17.5
    T[200:206] = 28.0
    return [(float(t), 0.25) for t in T]


def test_c_core_matches_python_shelf_life():
    pairs = trip()
    c = run_c(pairs)
    if c is None:
        print("SKIP (no C compiler)")
        return
    m = ColdChainMonitor("milk", n_draws=10)
    py = np.array([m.update(T, dt).shelf_life_used for T, dt in pairs])
    np.testing.assert_allclose(c[:, 1], py, rtol=2e-4)


def test_c_core_probability_is_sane():
    c = run_c(trip())
    if c is None:
        print("SKIP (no C compiler)")
        return
    p = c[:, 2]
    assert np.all((p >= 0) & (p <= 1)) and np.all(np.diff(p) >= 0)
    assert np.all(c[:, 4] <= c[:, 3] + 1e-6)          # cautious hours-left never exceeds the typical value


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)

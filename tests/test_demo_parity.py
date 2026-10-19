"""The web demo ships its own JavaScript copy of the shelf-life kernel.
This test checks that it gives the same answers as the Python original."""
import json, shutil, subprocess, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dg_kinetics import sl_gompertz  # noqa: E402

TEMPS = [0, 2, 4, 6, 8, 10, 12, 15, 17.5, 20, 25]
LIMITS = [1e5, 1e6, 1e7]


def js_values():
    code = (f"const k=require('{ROOT/'demo'/'kernel.js'}');const out=[];"
            f"for(const N of {LIMITS})for(const T of {TEMPS})out.push(k.slGompertz(T,N));"
            "console.log(JSON.stringify(out));")
    return np.array(json.loads(subprocess.check_output(["node", "-e", code], text=True)))


def test_js_kernel_matches_python():
    if shutil.which("node") is None:
        print("SKIP (node not installed)"); return
    b, tmin, h0, logn0, lmax = 0.030, -7.7, 3.8, 1.7, 9.0
    py = np.array([float(sl_gompertz(T, b, tmin, h0, logn0, lmax, N)) for N in LIMITS for T in TEMPS])
    np.testing.assert_allclose(js_values(), py, rtol=1e-9)


if __name__ == "__main__":
    test_js_kernel_matches_python()
    print("PASS test_js_kernel_matches_python")

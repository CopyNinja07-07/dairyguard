"""Run one simulated world of the DairyGuard benchmark.

Usage, from the repository root:
    DG_PARAMS=ref python experiments/run_benchmark.py 4000 results/base

DG_PARAMS selects the world (ref, comb, lis); DG_SHIFT and DG_N0 switch on the extra-lag and
low-starting-load variants. All random numbers come from fixed seeds."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from dairyguard.benchmark import run

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    out = sys.argv[2] if len(sys.argv) > 2 else "results"
    os.makedirs(out, exist_ok=True)
    run(N=n, out=out)

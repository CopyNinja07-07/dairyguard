import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
import benchmark as B
import simulate as S


def test_auc_fast_matches_reference():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 500)
    s = rng.normal(size=500) + y * 0.7
    assert abs(B.auc_fast(s, y) - S.auc(s, y)) < 1e-9


def test_auc_known_values():
    y = np.array([0, 0, 1, 1])
    assert B.auc_fast(np.array([0.1, 0.2, 0.8, 0.9]), y) == 1.0
    assert B.auc_fast(np.array([0.9, 0.8, 0.2, 0.1]), y) == 0.0


def test_paired_diff_identical_scores_is_zero():
    rng = np.random.default_rng(1)
    y = rng.integers(0, 2, 300)
    s = rng.normal(size=300) + y
    d, lo, hi = B.paired_diff(s, s.copy(), y, rng, B=50)
    assert d == 0 and lo == 0 and hi == 0


def test_paired_diff_detects_real_improvement():
    rng = np.random.default_rng(2)
    y = rng.integers(0, 2, 2000)
    good = rng.normal(size=2000) + 1.5 * y
    bad = rng.normal(size=2000) + 0.2 * y
    d, lo, hi = B.paired_diff(good, bad, y, rng, B=200)
    assert d > 0.1 and lo > 0


def test_mc_posterior_monotone_in_temperature():
    rng = np.random.default_rng(3)
    steps = 100 * 4                       # 100 h at 15 min
    cold = np.full((20, steps), 4.0)
    warm = np.full((20, steps), 18.0)
    Pc = B.mc_posterior(cold, 0.25, 3e4, 0.1, B.N0_RANGE, rng, K=40, chunk=10)
    Pw = B.mc_posterior(warm, 0.25, 3e4, 0.1, B.N0_RANGE, rng, K=40, chunk=10)
    assert Pc.mean() < 0.1 and Pw.mean() > 0.9


def test_calibration_perfect_and_bad():
    y = np.array([0, 0, 1, 1] * 50)
    br, ece = B.calibration(y.astype(float), y)
    assert br == 0 and ece == 0
    br2, ece2 = B.calibration(1.0 - y, y)
    assert br2 == 1.0 and ece2 == 1.0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)

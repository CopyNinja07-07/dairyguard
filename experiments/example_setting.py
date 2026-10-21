"""Per-trip scores for one representative setting (baseline biology, limit 3e4 CFU/mL, low-mass pouch, cv = 0.10),
used for the ROC curves, reliability diagram and bootstrap distribution in the paper.
Run from the repository root: DG_PARAMS=ref python experiments/example_setting.py  ->  results/example_setting.npz"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import numpy as np
from dairyguard import simulate as S
from dairyguard import benchmark as B
from dairyguard.kinetics import make_sl_lookup

rng = np.random.default_rng(2026)
Nlim = S.THR["A_3e4"]; hz = S.label_horizon_h(Nlim); steps = hz * 60
sl = make_sl_lookup(S.B0, S.TMIN, S.H0_EST, S.LOGN0_EST, S.LOG10NMAX, Nlim)
Tp, _ = S.gen_profiles(4000, steps, rng, tau_h=B.TAU_H["low_mass"])
y, pars = S.truth_labels(Tp, steps, 0.10, B.N0_RANGE, rng)
label = (y > np.log(Nlim)).astype(int)
sc = S.scores_fixed(Tp, steps, "DS18B20", 15, sl, rng)
orc = S.oracle_csl(Tp, steps, pars, Nlim)
idx = np.arange(0, steps, 15)
meas = S.measure(Tp[:, idx].astype(float), "DS18B20", rng, len(label))
P = B.mc_posterior(meas, 0.25, Nlim, cv_prior=0.10, n0_range=B.N0_RANGE, rng=rng)
A = B.mc_posterior(meas, 0.25, Nlim, cv_prior=0.0, n0_range=B.N0_RANGE, rng=rng, point=True)
boot = []
for _ in range(1000):
    i = rng.integers(0, len(label), len(label))
    boot.append(B.auc_fast(sc["CSL"][i], label[i]) - B.auc_fast(sc["deg_hours_4C"][i], label[i]))
np.savez_compressed("results/example_setting.npz", label=label, oracle=orc, P_mc=P, P_alarm=A, boot_diff=np.array(boot),
                    **{k: v for k, v in sc.items() if k != "n_samples"})
print("prevalence", label.mean(), "AUC CSL", B.auc_fast(sc["CSL"], label), "AUC DH", B.auc_fast(sc["deg_hours_4C"], label))

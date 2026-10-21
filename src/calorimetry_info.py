"""Value of a calorimetric measurement of the lot, baseline biology (run with DG_PARAMS=ref).

For each of the 12 baseline settings the trips are regenerated with a separate seed and scored from a DS18B20
record sampled every 15 min:
  nominal      CSL with nominal parameters (the monitor of the main benchmark)
  budget       CSL with each trip's true lag h0 and starting load N0, nominal rate law
  ratelaw      CSL with each trip's true b and Tmin, nominal h0 and N0
  calorimetry  integral of the nominal rate along the record divided by an isothermal calorimetric detection time
               t_det of the same biology at T_ref (time to reach N_det), measured with a relative error cv_det
  oracle       true parameters and true temperature
Writes results/calorimetry_info.csv and results/calorimetry_info_paired.csv.
"""
import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import simulate as S
from dg_kinetics import sl_gompertz, make_sl_lookup, mu_sqrt
from benchmark import auc_fast, paired_diff, TAU_H, CVS, N0_RANGE

T_REF, N_DET, CV_DET = 20.0, 1e5, 0.05


def per_trip_csl(meas, dt, b, tmin, h0, l0, nlim, chunk=500):
    out = np.zeros(meas.shape[0])
    for a in range(0, meas.shape[0], chunk):
        s = slice(a, a + chunk)
        sl = sl_gompertz(meas[s], b[s, None], tmin[s, None], h0[s, None], l0[s, None], S.LOG10NMAX, nlim)
        out[s] = (dt / sl).sum(1)
    return out


def main(N=4000, seed=2027, out="results", t_ref=T_REF, cv_det=CV_DET, tag=""):
    rng = np.random.default_rng(seed)
    rows, paired = [], []
    for tn, nlim in S.THR.items():
        hz = S.label_horizon_h(nlim); steps = hz * 60
        sl_nom = make_sl_lookup(S.B0, S.TMIN, S.H0_EST, S.LOGN0_EST, S.LOG10NMAX, nlim)
        for taun, tau in TAU_H.items():
            Tp, _ = S.gen_profiles(N, steps, rng, tau_h=tau)
            for cv in CVS:
                y, p = S.truth_labels(Tp, steps, cv, N0_RANGE, rng)
                label = (y > np.log(nlim)).astype(int)
                idx = np.arange(0, steps, 15)
                meas = S.measure(Tp[:, idx].astype(float), "DS18B20", rng, N); dt = 0.25
                one = np.ones(N)
                sc = {
                    "nominal": (dt / sl_nom(meas)).sum(1),
                    "budget": per_trip_csl(meas, dt, S.B0 * one, S.TMIN * one, p["h0"], p["log10N0"], nlim),
                    "ratelaw": per_trip_csl(meas, dt, p["b"], p["Tmin"], S.H0_EST * one, S.LOGN0_EST * one, nlim),
                    "oracle": S.oracle_csl(Tp, steps, p, nlim),
                }
                tdet = sl_gompertz(t_ref, p["b"], p["Tmin"], p["h0"], p["log10N0"], S.LOG10NMAX, N_DET)
                tdet = tdet * np.exp(rng.normal(0, cv_det, N))
                sc["calorimetry"] = (mu_sqrt(meas, S.B0, S.TMIN) * dt).sum(1) / tdet
                key = dict(thr=tn, tau=taun, cv=cv, prevalence=label.mean(),
                           tdet_median_h=float(np.median(tdet)), tdet_p05_h=float(np.percentile(tdet, 5)),
                           tdet_p95_h=float(np.percentile(tdet, 95)))
                for m, s in sc.items():
                    rows.append(dict(**key, method=m, AUC=auc_fast(s, label)))
                for a, b in (("calorimetry", "nominal"), ("budget", "nominal"), ("ratelaw", "nominal"), ("oracle", "calorimetry")):
                    d, lo, hi = paired_diff(sc[a], sc[b], label, rng)
                    paired.append(dict(thr=tn, tau=taun, cv=cv, contrast=f"{a} - {b}", diff=d, lo=lo, hi=hi,
                                       excludes_zero=bool(lo > 0 or hi < 0)))
                print(tn, taun, cv, {m: round(auc_fast(s, label), 3) for m, s in sc.items()}, flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(out, f"calorimetry_info{tag}.csv"), index=False)
    pd.DataFrame(paired).to_csv(os.path.join(out, f"calorimetry_info{tag}_paired.csv"), index=False)


if __name__ == "__main__":
    main()
    main(cv_det=0.15, tag="_cv15")
    main(t_ref=10.0, tag="_t10")

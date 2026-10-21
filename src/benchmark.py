"""The DairyGuard benchmark: scores every prediction rule on the same simulated trips.

Includes:
  * thermal-inertia axis (low-mass pouch vs insulated crate)
  * PAIRED bootstrap contrasts on the same trips (valid CIs for differences)
  * uncertainty-aware score: Monte-Carlo posterior P(spoiled | measured history)
    with calibration metrics (Brier, ECE) under matched / overconfident priors
  * loss budget: oracle -> biology-limited -> +sensor -> +sampling

Parameter provenance (sourced, fitted or assumed) is recorded in data/params.csv.
"""
import sys
import numpy as np
import pandas as pd
from scipy.stats import rankdata
import simulate as S
from dg_kinetics import sl_gompertz, make_sl_lookup

TAU_H = {"low_mass": (5 / 60, 20 / 60), "insulated": (1.0, 4.0)}      # product time constant, hours
CVS = (0.0, 0.10, 0.25)
N0_RANGE = S.N0_RANGES["narrow"]
SAMPLINGS = (1, 15, 60)
SENS = ("DS18B20", "PT1000", "ideal")


def auc_fast(score, label):
    n1 = int(label.sum())
    n0 = len(label) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(score)
    return (r[label == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def boot_ci(score, label, rng, B=200):
    n = len(label)
    v = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        v.append(auc_fast(score[i], label[i]))
    return np.nanpercentile(v, [2.5, 97.5])


def paired_diff(s1, s2, label, rng, B=400):
    """AUC(s1) - AUC(s2) on the SAME trips, with a paired bootstrap 95% CI."""
    n = len(label)
    d0 = auc_fast(s1, label) - auc_fast(s2, label)
    v = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        v.append(auc_fast(s1[i], label[i]) - auc_fast(s2[i], label[i]))
    lo, hi = np.nanpercentile(v, [2.5, 97.5])
    return d0, lo, hi


def mc_posterior(meas, dt_h, Nlim, cv_prior, n0_range, rng, K=80, chunk=100, point=False):
    """P(spoiled | measured history) by Monte Carlo over the biological prior.
    point=True collapses the prior to nominal values (a 0/1 'alarm')."""
    n = meas.shape[0]
    if point:
        b = np.array([S.B0]); tmin = np.array([S.TMIN]); h0 = np.array([S.H0_EST]); l0 = np.array([S.LOGN0_EST])
    else:
        b = S.B0 * (rng.lognormal(0, cv_prior, K) if cv_prior > 0 else np.ones(K))
        tmin = rng.normal(S.TMIN, S.TMIN_SD, K)
        h0 = rng.uniform(S.H0_RANGE[0], S.H0_RANGE[1], K)
        l0 = rng.uniform(n0_range[0], n0_range[1], K)
    P = np.empty(n)
    for a in range(0, n, chunk):
        T = meas[a:a + chunk][:, None, :]
        sl = sl_gompertz(T, b[None, :, None], tmin[None, :, None], h0[None, :, None],
                         l0[None, :, None], S.LOG10NMAX, Nlim)
        csl = (dt_h / sl).sum(2)
        P[a:a + chunk] = (csl >= 1.0).mean(1)
    return P


def calibration(P, y, bins=10):
    brier = float(np.mean((P - y) ** 2))
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    for k in range(bins):
        m = (P >= edges[k]) & ((P < edges[k + 1]) if k < bins - 1 else (P <= edges[k + 1]))
        if m.any():
            ece += m.mean() * abs(P[m].mean() - y[m].mean())
    return brier, float(ece)


def run(N=4000, seed=11, out="results"):
    import os; os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(seed)
    rng2 = np.random.default_rng(seed + 1000)    # separate stream for the additional integrators
    rows, paired, cal = [], [], []
    for tn, Nlim in S.THR.items():
        hz = S.label_horizon_h(Nlim)
        steps = hz * 60
        sl = make_sl_lookup(S.B0, S.TMIN, S.H0_EST, S.LOGN0_EST, S.LOG10NMAX, Nlim)
        for taun, tau in TAU_H.items():
            Tp, nev = S.gen_profiles(N, steps, rng, tau_h=tau)
            for cv in CVS:
                y, pars = S.truth_labels(Tp, steps, cv, N0_RANGE, rng)
                label = (y > np.log(Nlim)).astype(int)
                prev = label.mean()
                key = dict(thr=tn, tau=taun, cv=cv, horizon_h=hz)
                if prev < S.MIN_PREV or prev > 1 - S.MIN_PREV:
                    print("SKIP", key, prev, file=sys.stderr)
                    continue
                sc = {}
                for sen in SENS:
                    for s in SAMPLINGS:
                        sc[(sen, s)] = S.scores_fixed(Tp, steps, sen, s, sl, rng)
                for sen in ("DS18B20", "PT1000"):
                    sc[(sen, "adaptive")] = S.scores_adaptive(Tp, steps, sen, sl, rng)
                orc = S.oracle_csl(Tp, steps, pars, Nlim)
                # absolute AUCs with CIs
                for (sen, s), d in sc.items():
                    for m in S.METHODS:
                        a = auc_fast(d[m], label)
                        lo, hi = boot_ci(d[m], label, rng)
                        rows.append(dict(**key, sensor=sen, sampling=s, method=m, prevalence=prev,
                                         AUC=a, lo=lo, hi=hi, mean_samples=float(np.mean(d["n_samples"]))))
                for (sen, s), d in sc.items():
                    for m in S.EXTRA:
                        a = auc_fast(d[m], label)
                        lo, hi = boot_ci(d[m], label, rng2)
                        rows.append(dict(**key, sensor=sen, sampling=s, method=m, prevalence=prev,
                                         AUC=a, lo=lo, hi=hi, mean_samples=float(np.mean(d["n_samples"]))))
                a = auc_fast(orc, label)
                lo, hi = boot_ci(orc, label, rng)
                rows.append(dict(**key, sensor="oracle", sampling=1, method="CSL_oracle", prevalence=prev,
                                 AUC=a, lo=lo, hi=hi, mean_samples=float(steps)))
                # paired contrasts
                base = sc[("DS18B20", 15)]
                C = {
                    "CSL - degree_hours_4C": (base["CSL"], base["deg_hours_4C"]),
                    "CSL - time_above_5C": (base["CSL"], base["t_above_5C"]),
                    "CSL - max_temperature": (base["CSL"], base["maxT"]),
                    "sensor: PT1000 - DS18B20 (CSL,15min)": (sc[("PT1000", 15)]["CSL"], base["CSL"]),
                    "sensor: ideal - DS18B20 (CSL,15min)": (sc[("ideal", 15)]["CSL"], base["CSL"]),
                    "sampling: 60min - 1min (DS18B20,CSL)": (sc[("DS18B20", 60)]["CSL"], sc[("DS18B20", 1)]["CSL"]),
                    "sampling: 15min - 1min (DS18B20,CSL)": (base["CSL"], sc[("DS18B20", 1)]["CSL"]),
                    "adaptive - fixed1min (DS18B20,CSL)": (sc[("DS18B20", "adaptive")]["CSL"], sc[("DS18B20", 1)]["CSL"]),
                    "biology gap: oracle - ideal(1min,CSL)": (orc, sc[("ideal", 1)]["CSL"]),
                }
                for name, (x1, x2) in C.items():
                    d0, lo, hi = paired_diff(x1, x2, label, rng)
                    paired.append(dict(**key, contrast=name, diff=d0, lo=lo, hi=hi,
                                       excludes_zero=bool(lo > 0 or hi < 0)))
                for m in S.EXTRA:
                    d0, lo, hi = paired_diff(base["CSL"], base[m], label, rng2)
                    paired.append(dict(**key, contrast=f"CSL - {m}", diff=d0, lo=lo, hi=hi, excludes_zero=bool(lo > 0 or hi < 0)))
                    d0, lo, hi = paired_diff(base[m], base["deg_hours_4C"], label, rng2)
                    paired.append(dict(**key, contrast=f"{m} - degree_hours_4C", diff=d0, lo=lo, hi=hi, excludes_zero=bool(lo > 0 or hi < 0)))
                # uncertainty-aware score on a realistic device record (DS18B20, 15 min)
                idx = np.arange(0, steps, 15)
                meas = S.measure(Tp[:, idx].astype(float), "DS18B20", rng, N)
                variants = {
                    "MC matched prior": dict(cv_prior=cv),
                    "MC overconfident b (cv_prior=0)": dict(cv_prior=0.0),
                    "point alarm (nominal params)": dict(cv_prior=0.0, point=True),
                }
                for vn, kw in variants.items():
                    P = mc_posterior(meas, 0.25, Nlim, n0_range=N0_RANGE, rng=rng, **kw)
                    br, ece = calibration(P, label)
                    cal.append(dict(**key, variant=vn, AUC=auc_fast(P, label), brier=br, ECE=ece,
                                    mean_P=float(P.mean()), prevalence=prev))
                print("done", key, f"prev={prev:.3f}", file=sys.stderr, flush=True)
            del Tp
    pd.DataFrame(rows).to_csv(f"{out}/auc_results.csv", index=False)
    pd.DataFrame(paired).to_csv(f"{out}/paired_contrasts.csv", index=False)
    pd.DataFrame(cal).to_csv(f"{out}/calibration.csv", index=False)


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    out = sys.argv[2] if len(sys.argv) > 2 else "results"
    run(N=N, out=out)

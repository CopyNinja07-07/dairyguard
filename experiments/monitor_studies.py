"""Further tests of the DairyGuard Kinetic monitor, in the baseline simulated world (DG_PARAMS=ref).

1. Trained baseline. A logistic regression on simple log features (degree-hours, time above 5 and 8 deg C, maximum and
   mean temperature, consumed shelf life) is trained on one set of simulated trips and tested on another, against the
   monitor's Monte Carlo probability and a single alarm. This answers whether a probability learned from data does as
   well as one built from biology.
2. Monte Carlo convergence. The monitor's probability uses K plausible batches; how many are needed?
3. Correlated biology. Real strains that grow fast in the cold often also have a lower minimum temperature. Does a
   correlation between b and Tmin change the loss to biology?
4. Hours left. After each trip the monitor says how long the batch will last at 4 deg C, typically and cautiously
   (9 in 10). The true time is computed from the reference model; how often is the cautious figure safe?

Writes results/monitor_studies.json. Run from the repository root:
    DG_PARAMS=ref python experiments/monitor_studies.py
"""
import json
import os
import sys

os.environ.setdefault("DG_PARAMS", "ref")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from dairyguard import simulate as S
from dairyguard.benchmark import auc_fast, calibration, mc_posterior, TAU_H, N0_RANGE
from dairyguard.kinetics import make_sl_lookup, sl_gompertz, mu_sqrt, LN10

N, NLIM, SMIN = 4000, 3e4, 15


def world(seed, cv=0.10, tau="insulated", rho=0.0):
    """Simulated trips with sensed 15-min readings and true labels. rho correlates ln b with -Tmin."""
    rng = np.random.default_rng(seed)
    hz = S.label_horizon_h(NLIM); steps = hz * 60
    Tp, _ = S.gen_profiles(N, steps, rng, tau_h=TAU_H[tau])
    z1, z2 = rng.normal(size=N), rng.normal(size=N)
    b = S.B0 * np.exp(cv * z1) if cv > 0 else np.full(N, S.B0)
    tmin = S.TMIN + S.TMIN_SD * (-rho * z1 + np.sqrt(1 - rho ** 2) * z2)
    h0 = rng.uniform(*S.H0_RANGE, N); l0 = rng.uniform(*N0_RANGE, N)
    y = l0 * LN10; q = 1 / (np.exp(h0) - 1); ymax = S.LOG10NMAX * LN10
    for i in range(steps):
        m = mu_sqrt(Tp[:, i].astype(float), b, tmin); a = q / (1 + q)
        y = y + m * a * (1 - np.exp(y - ymax)) / 60; q = q + m * q / 60
    label = (y > np.log(NLIM)).astype(int)
    idx = np.arange(0, steps, SMIN)
    meas = S.measure(Tp[:, idx].astype(float), "DS18B20", rng, N)
    pars = dict(b=b, Tmin=tmin, h0=h0, log10N0=l0)
    return dict(Tp=Tp, steps=steps, meas=meas, label=label, y=y, q=q, pars=pars, rng=rng)


def features(meas):
    dt = SMIN / 60
    sl = make_sl_lookup(S.B0, S.TMIN, S.H0_EST, S.LOGN0_EST, S.LOG10NMAX, NLIM)
    csl = (dt / sl(meas)).sum(1)
    return np.column_stack([np.maximum(meas - 4, 0).sum(1) * dt, (meas > 5).sum(1) * dt, (meas > 8).sum(1) * dt,
                            meas.max(1), meas.mean(1), np.log(csl)]), csl


def trained_baseline():
    out = {}
    for tau in TAU_H:
        tr, te = world(101, tau=tau), world(202, tau=tau)
        Xtr, _ = features(tr["meas"]); Xte, csl = features(te["meas"])
        sc = StandardScaler().fit(Xtr)
        lr = LogisticRegression(max_iter=2000).fit(sc.transform(Xtr), tr["label"])
        p_lr = lr.predict_proba(sc.transform(Xte))[:, 1]
        p_mc = mc_posterior(te["meas"], SMIN / 60, NLIM, 0.10, N0_RANGE, np.random.default_rng(5))
        alarm = (csl >= 1).astype(float)
        y = te["label"]
        res = {}
        for k, p in (("logistic regression (trained)", p_lr), ("DairyGuard probability", p_mc), ("single alarm", alarm)):
            br, ece = calibration(p, y)
            res[k] = dict(AUC=round(auc_fast(p, y), 4), Brier=round(br, 4), ECE=round(ece, 4))
        res["prevalence"] = round(float(y.mean()), 3)
        out[tau] = res
        print("trained baseline", tau, res, flush=True)
    return out


def mc_convergence():
    te = world(303)
    y = te["label"]; out = {}
    for K in (10, 20, 40, 80, 160, 320):
        p = mc_posterior(te["meas"], SMIN / 60, NLIM, 0.10, N0_RANGE, np.random.default_rng(K), K=K)
        br, ece = calibration(p, y)
        out[K] = dict(AUC=round(auc_fast(p, y), 4), Brier=round(br, 4), ECE=round(ece, 4))
    print("mc convergence", out, flush=True)
    return out


def correlated_biology():
    out = {}
    for rho in (-0.6, 0.0, 0.6):
        w = world(404, cv=0.25, rho=rho)
        y = w["label"]
        nominal = features(w["meas"])[1]
        oracle = S.oracle_csl(w["Tp"], w["steps"], w["pars"], NLIM)
        out[rho] = dict(AUC_log=round(auc_fast(nominal, y), 4), AUC_oracle=round(auc_fast(oracle, y), 4),
                        loss_to_biology=round(auc_fast(oracle, y) - auc_fast(nominal, y), 4),
                        prevalence=round(float(y.mean()), 3))
    print("correlated biology", out, flush=True)
    return out


def hours_left():
    """Cautious and typical hours left at 4 deg C, judged against the reference model, for trips under the limit."""
    w = world(505)
    ok = w["label"] == 0
    meas = w["meas"][ok]; y, q = w["y"][ok], w["q"][ok]
    pars = {k: v[ok] for k, v in w["pars"].items()}
    # truth: continue the reference model at 4 deg C until the limit
    mu4 = mu_sqrt(np.full(ok.sum(), 4.0), pars["b"], pars["Tmin"])
    t_true = np.full(ok.sum(), np.nan); t = 0.0; dt = 0.1; yl = np.log(NLIM); ymax = S.LOG10NMAX * LN10
    yy, qq = y.copy(), q.copy()
    while np.isnan(t_true).any() and t < 2000:
        a = qq / (1 + qq); yy = yy + dt * mu4 * a * (1 - np.exp(yy - ymax)); qq = qq + dt * mu4 * qq; t += dt
        t_true[np.isnan(t_true) & (yy >= yl)] = t
    # monitor: K plausible batches
    rng = np.random.default_rng(9); K = 200
    b = S.B0 * np.exp(rng.normal(0, 0.10, K) - 0.005); tmin = rng.normal(S.TMIN, S.TMIN_SD, K)
    h0 = rng.uniform(*S.H0_RANGE, K); l0 = rng.uniform(*N0_RANGE, K)
    dtm = SMIN / 60
    left_typ, left_cau = np.empty(len(meas)), np.empty(len(meas))
    sl4 = sl_gompertz(np.full(K, 4.0), b, tmin, h0, l0, S.LOG10NMAX, NLIM)
    for a0 in range(0, len(meas), 200):
        T = meas[a0:a0 + 200][:, None, :]
        csl = (dtm / sl_gompertz(T, b[None, :, None], tmin[None, :, None], h0[None, :, None], l0[None, :, None],
                                  S.LOG10NMAX, NLIM)).sum(2)
        left = np.maximum(1 - csl, 0) * sl4[None, :]
        left_typ[a0:a0 + 200] = np.median(left, 1); left_cau[a0:a0 + 200] = np.percentile(left, 10, 1)
    good = ~np.isnan(t_true)
    res = dict(trips=int(good.sum()), cautious_was_safe=round(float((t_true[good] >= left_cau[good]).mean()), 3),
               typical_was_safe=round(float((t_true[good] >= left_typ[good]).mean()), 3),
               median_abs_error_typical_h=round(float(np.median(np.abs(t_true[good] - left_typ[good]))), 1),
               median_true_hours_left=round(float(np.median(t_true[good])), 1),
               spearman=round(float(np.corrcoef(np.argsort(np.argsort(t_true[good])), np.argsort(np.argsort(left_typ[good])))[0, 1]), 3))
    print("hours left", res, flush=True)
    return res


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    out = dict(world="baseline (DG_PARAMS=ref), FSSAI limit, DS18B20 every 15 min, cv 0.10 unless stated",
               trained_baseline=trained_baseline(), mc_convergence=mc_convergence(),
               correlated_biology=correlated_biology(), hours_left=hours_left())
    json.dump(out, open("results/monitor_studies.json", "w"), indent=1)

"""Monte Carlo benchmark: do kinetic scores beat threshold rules, and how much do sensor
error / sampling interval matter?  Parameter provenance is recorded in data/params.csv.

Label definition (fixed before any method comparison was looked at):
  a trip is 'spoiled' if the reference (Baranyi) population exceeds the threshold within the
  nominal label shelf life, defined as the isothermal 4 degC time-to-limit of the estimator
  at nominal parameters, rounded up to whole hours.  Excursion rate is 1 per 144 h on average.
"""
import sys
import numpy as np
import pandas as pd
from .kinetics import mu_sqrt, sl_gompertz, make_sl_lookup, LN10

TMIN, TMIN_SD, B0 = -7.75, 0.7, 0.016
H0_EST, LOGN0_EST, LOG10NMAX = 1.5, 1.7, 9.0
H0_RANGE = (0.5, 3.0)
import os
if os.environ.get("DG_PARAMS") == "lin":   # Lin et al. 2016 anchored (P. fluorescens in milk): T0 -9.15 C, b 0.0273 (ln basis), h0 ~ lag*mu
    TMIN, B0, H0_EST, H0_RANGE = -9.15, 0.0273, 3.8, (2.5, 5.0)
if os.environ.get("DG_PARAMS") == "ref":   # Neumeyer 1995 (Tmin -7.7 C, b 0.030 ln basis) + Lin 2016 lag; Tmin SD is an ASSUMED 1.5 K (literature spread 2.8 K includes method noise)
    TMIN, TMIN_SD, B0, H0_EST, H0_RANGE = -7.7, 1.5, 0.030, 3.8, (2.5, 5.0)
if os.environ.get("DG_PARAMS") == "lis":
    pass
if os.environ.get("DG_N0") == "low":   # realistic post-pasteurisation load (Martin 2021: 1-50 cells per 100 mL up to ~1 cell/mL)
    LOGN0_EST = -0.25
if os.environ.get("DG_PARAMS") == "comb":   # fitted to 50 ComBase records (Tasmanian Inst. of Agriculture, aerobic spoilage flora in pasteurised milk, 2.7-14.9 C), see experiments/validate_combase.py
    TMIN, TMIN_SD, B0, H0_EST, H0_RANGE = -6.6, 1.5, 0.0256, 3.8, (2.5, 5.0)
if os.environ.get("DG_PARAMS") == "lis":   # Listeria monocytogenes in milk, fitted to 40 ComBase records (conditions 'not specified', 3-15 C), see experiments/validate_combase_lis.py.
    # Hazard case study: label 'A' = +0.5 log10 growth, 'B' = +1 log10 over the starting load (round-number growth labels, NOT regulatory limits). Tmin SD, lag and starting load are ASSUMED.
    TMIN, TMIN_SD, B0, H0_EST, H0_RANGE, LOGN0_EST = -2.3, 1.0, 0.0235, 3.0, (2.0, 4.5), -1.0
SHIFT_F = float(os.environ.get("DG_SHIFT", "0"))   # extra lag after a temperature shift, as a fraction of h0 (Zwietering 1994: 0.25)
THR = {"A_3e4": 3e4, "B_1e6": 1e6}
if os.environ.get("DG_PARAMS") == "lis":   # keys kept so the pipeline is unchanged; values are +0.5 and +1 log10 over the starting load
    THR = {"A_3e4": 10 ** (LOGN0_EST + 0.5), "B_1e6": 10 ** (LOGN0_EST + 1.0)}
SENSORS = {"DS18B20": (0.5, 0.05, 0.0625), "PT1000": (0.15, 0.03, 0.03125), "ideal": (0.0, 0.0, 0.0)}
PEAKS, PW = np.array([12, 14.3, 17.5, 30.7]), np.array([.30, .25, .30, .15])
METHODS = ("CSL", "maxT", "t_above_8C", "t_above_5C", "deg_hours_4C")
# Additional single-parameter integrators with a fixed temperature law (evaluated with a separate random stream so that
# the results of METHODS are unchanged). Arrhenius activation energies: fitted to the ComBase records of the run's
# organism (experiments/compare_secondary.py; spoilage flora 92 kJ/mol, L. monocytogenes 130 kJ/mol) and 120 kJ/mol reported for
# spoilage of carrot juice by isothermal calorimetry (Wadso et al. 2011); Q10 = 3 as in Zou et al. 2023.
EA_FIT = 130.1e3 if os.environ.get("DG_PARAMS") == "lis" else 92.3e3
EXTRA = {"arrhenius_fit": ("arr", EA_FIT), "arrhenius_120kJ": ("arr", 120e3), "q10_3": ("q10", 3.0)}


def extra_rate(T, kind, par, Tref=4.0):
    T = np.asarray(T, float)
    if kind == "arr":
        return np.exp(-par / 8.314 * (1 / (T + 273.15) - 1 / (Tref + 273.15)))
    return par ** ((T - Tref) / 10.0)
MIN_PREV = 0.02                      # skip scenarios where one class is under 2 percent


def label_horizon_h(Nlim):
    return int(np.ceil(float(sl_gompertz(4.0, B0, TMIN, H0_EST, LOGN0_EST, LOG10NMAX, Nlim))))


def gen_profiles(n, steps, rng, tau_h=(1.0, 4.0)):
    """Product temperature (n x steps+1): first-order inertia + random ambient excursions."""
    t = np.arange(steps + 1)
    base = rng.uniform(2.5, 5.0, n)
    tau = rng.uniform(tau_h[0], tau_h[1], n) * 60.0
    amb = np.repeat(base[:, None], steps + 1, 1).astype(np.float32)
    nev = np.minimum(rng.poisson(steps / 60.0 / 144.0, n), 8)
    for k in range(8):
        on = nev > k
        if not on.any():
            break
        dur = np.clip(rng.lognormal(np.log(60), 0.8, n), 10, 480)
        s = rng.uniform(0, np.maximum(steps - dur, 1))
        pk = rng.choice(PEAKS, n, p=PW).astype(np.float32)
        m = (t[None, :] >= s[:, None]) & (t[None, :] < (s + dur)[:, None]) & on[:, None]
        amb = np.where(m, pk[:, None], amb)
        del m
    Tp = np.empty_like(amb)
    Tp[:, 0] = base
    ar = np.zeros(n)
    for i in range(1, steps + 1):
        ar = 0.97 * ar + rng.normal(0, 0.05, n)
        Tp[:, i] = Tp[:, i - 1] + (amb[:, i] - Tp[:, i - 1]) / tau + ar * 0.1
    return Tp, nev


N0_RANGES = {"narrow": (1.5, 2.0), "wide": (1.0, 2.5)}   # log10 CFU/mL, ASSUMED (see params.csv)
if os.environ.get("DG_N0") == "low":
    N0_RANGES = {"narrow": (-1.0, 0.5), "wide": (-1.5, 1.0)}
if os.environ.get("DG_PARAMS") == "lis":
    N0_RANGES = {"narrow": (-1.25, -0.75), "wide": (-1.5, -0.6)}   # must stay below the +0.5 log label (-0.5): a start above the limit makes labels degenerate


def truth_labels(Tp, steps, cv, n0_range, rng):
    """Baranyi dynamic reference with strain / parameter variability.
    Returns ln N at the horizon and the per-trip true parameters (for the oracle score)."""
    n = Tp.shape[0]
    b = B0 * rng.lognormal(0, cv, n) if cv > 0 else np.full(n, B0)
    Tmin = rng.normal(TMIN, TMIN_SD, n)
    h0 = rng.uniform(H0_RANGE[0], H0_RANGE[1], n)
    log10N0 = rng.uniform(n0_range[0], n0_range[1], n)
    pars = dict(b=b, Tmin=Tmin, h0=h0, log10N0=log10N0)
    y = log10N0 * LN10
    ymax = LOG10NMAX * LN10
    q = 1.0 / (np.exp(h0) - 1.0)
    dt = 1 / 60
    Tbar = Tp[:, 0].astype(float); flag = np.zeros(n, bool)
    for i in range(steps):
        T = Tp[:, i].astype(float)
        if SHIFT_F:
            Tbar = Tbar + (T - Tbar) * (dt / 2.0)          # 2 h running reference
            fl = np.abs(T - Tbar) > 4.0
            tr = fl != flag
            q = np.where(tr, q * np.exp(-SHIFT_F * h0), q)  # a shift (onset or recovery) re-imposes part of the lag
            flag = fl
        mu = mu_sqrt(T, b, Tmin)
        a = q / (1 + q)
        y = y + dt * mu * a * (1 - np.exp(y - ymax))
        q = q + dt * mu * q
    return y, pars


def oracle_csl(Tp, steps, pars, Nlim, chunk=500):
    """Upper bound: CSL using each trip's TRUE parameters and the TRUE (noise-free) temperature.
    Anything below this is lost to unobservable biology; anything between this and a real
    score is lost to sensing / sampling / model-structure error."""
    n = Tp.shape[0]
    out = np.zeros(n)
    for a in range(0, n, chunk):
        sl = slice(a, a + chunk)
        T = Tp[sl, :steps].astype(float)
        sl_h = sl_gompertz(T, pars["b"][sl, None], pars["Tmin"][sl, None], pars["h0"][sl, None],
                           pars["log10N0"][sl, None], LOG10NMAX, Nlim)
        out[sl] = ((1 / 60) / sl_h).sum(1)
    return out


def measure(cols, sensor, rng, n):
    lim, sd, res = SENSORS[sensor]
    bias = rng.uniform(-lim, lim, (n, 1)) if lim else 0.0
    x = cols + bias + (rng.normal(0, sd, cols.shape) if sd else 0.0)
    return np.round(x / res) * res if res else x


def scores_fixed(Tp, steps, sensor, s_min, sl, rng):
    n = Tp.shape[0]
    idx = np.arange(0, steps, s_min)
    meas = measure(Tp[:, idx].astype(float), sensor, rng, n)
    dt = s_min / 60.0
    return {"CSL": (dt / sl(meas)).sum(1), "maxT": meas.max(1),
            "t_above_8C": (meas > 8.0).sum(1) * dt, "t_above_5C": (meas > 5.0).sum(1) * dt,
            "deg_hours_4C": np.maximum(meas - 4.0, 0).sum(1) * dt, "n_samples": np.full(n, len(idx)),
            **{k: (extra_rate(meas, *v) * dt).sum(1) for k, v in EXTRA.items()}}


def scores_adaptive(Tp, steps, sensor, sl, rng, base_min=15):
    """Research-plan 4.1 rule: relax to 15 min when |dT|<0.2 and 2<=T<=5, else 1-min cycles."""
    n = Tp.shape[0]
    lim, sd, res = SENSORS[sensor]
    bias = rng.uniform(-lim, lim, n) if lim else np.zeros(n)

    def rd(T):
        x = T + bias + (rng.normal(0, sd, n) if sd else 0.0)
        return np.round(x / res) * res if res else x

    held = rd(Tp[:, 0].astype(float))
    last = held.copy()
    nxt = np.full(n, base_min)
    ns = np.ones(n)
    csl = np.zeros(n)
    mx = held.copy()
    ta = np.zeros(n)
    ta5 = np.zeros(n)
    dh = np.zeros(n)
    ex = {k: np.zeros(n) for k in EXTRA}
    for i in range(steps):
        due = i >= nxt
        if due.any():
            new = rd(Tp[:, i].astype(float))
            steady = (np.abs(new - last) < 0.2) & (new >= 2) & (new <= 5)
            held = np.where(due, new, held)
            last = np.where(due, new, last)
            nxt = np.where(due, i + np.where(steady, base_min, 1), nxt)
            ns += due
        csl += (1 / 60) / sl(held)
        mx = np.maximum(mx, held)
        ta += (held > 8.0) / 60
        ta5 += (held > 5.0) / 60
        dh += np.maximum(held - 4.0, 0) / 60
        for k, v in EXTRA.items():
            ex[k] += extra_rate(held, *v) / 60
    return {"CSL": csl, "maxT": mx, "t_above_8C": ta, "t_above_5C": ta5, "deg_hours_4C": dh, "n_samples": ns, **ex}


def auc(score, label):
    pos, neg = score[label == 1], score[label == 0]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    r = pd.Series(np.concatenate([pos, neg])).rank().values
    return (r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def boot_auc(score, label, rng, B=100):
    n = len(label)
    out = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        out.append(auc(score[i], label[i]))
    return np.nanpercentile(out, [2.5, 97.5])


def best_operating_point(score, label):
    """Threshold maximising Youden J = sensitivity + specificity - 1."""
    ths = np.unique(np.quantile(score, np.linspace(0.01, 0.99, 197)))
    best = None
    for th in ths:
        f = score >= th
        tp = (f & (label == 1)).sum()
        fn = ((~f) & (label == 1)).sum()
        tn = ((~f) & (label == 0)).sum()
        fp = (f & (label == 0)).sum()
        se, sp = tp / max(tp + fn, 1), tn / max(tn + fp, 1)
        if best is None or se + sp - 1 > best[0]:
            best = (se + sp - 1, th, se, sp)
    return best


def _row(cv, n0, thr, hz, sensor, s, mode, m, sc, label, rng):
    a = auc(sc[m], label)
    lo, hi = boot_auc(sc[m], label, rng)
    J, th, se, sp = best_operating_point(sc[m], label)
    return dict(cv=cv, n0_spread=n0, thr=thr, horizon_h=hz, sensor=sensor, sampling_min=s, mode=mode, method=m,
                prevalence=label.mean(), AUC=a, AUC_lo=lo, AUC_hi=hi,
                youdenJ=J, sens=se, spec=sp, mean_samples=float(np.mean(sc["n_samples"])))


def run(N=4000, seed=7, cvs=(0.0, 0.10, 0.25), samplings=(1, 5, 15, 30, 60), out="results"):
    rng = np.random.default_rng(seed)
    rows, skipped = [], []
    for tn, Nlim in THR.items():
        hz = label_horizon_h(Nlim)
        steps = hz * 60
        Tp, nev = gen_profiles(N, steps, rng)
        sl = make_sl_lookup(B0, TMIN, H0_EST, LOGN0_EST, LOG10NMAX, Nlim)
        print(f"{tn}: horizon {hz} h, mean excursions {nev.mean():.2f}", file=sys.stderr)
        for n0name, n0r in N0_RANGES.items():
          for cv in cvs:
            y, pars = truth_labels(Tp, steps, cv, n0r, rng)
            label = (y > np.log(Nlim)).astype(int)
            prev = label.mean()
            if prev < MIN_PREV or prev > 1 - MIN_PREV:
                skipped.append(dict(thr=tn, cv=cv, n0_spread=n0name, horizon_h=hz, prevalence=prev))
                print(f"  SKIP {tn} n0={n0name} cv={cv}: prevalence {prev:.3f}", file=sys.stderr)
                continue
            orc = {"CSL_oracle": oracle_csl(Tp, steps, pars, Nlim), "n_samples": np.full(N, steps)}
            rows.append(_row(cv, n0name, tn, hz, "oracle", 1, "fixed", "CSL_oracle", orc, label, rng))
            for sensor in SENSORS:
                for s in samplings:
                    sc = scores_fixed(Tp, steps, sensor, s, sl, rng)
                    for m in METHODS:
                        rows.append(_row(cv, n0name, tn, hz, sensor, s, "fixed", m, sc, label, rng))
                sc = scores_adaptive(Tp, steps, sensor, sl, rng)
                for m in METHODS:
                    rows.append(_row(cv, n0name, tn, hz, sensor, np.nan, "adaptive", m, sc, label, rng))
            print(f"  done {tn} n0={n0name} cv={cv} prevalence {prev:.3f}", file=sys.stderr)
        if tn == "A_3e4":
            np.savez_compressed(f"{out}/example_profiles.npz", Tp=Tp[:50].astype(np.float32), nev=nev[:50])
        del Tp
    pd.DataFrame(rows).to_csv(f"{out}/benchmark_results.csv", index=False)
    pd.DataFrame(skipped, columns=["thr", "cv", "n0_spread", "horizon_h", "prevalence"]).to_csv(f"{out}/skipped_scenarios.csv", index=False)
    return pd.DataFrame(rows)

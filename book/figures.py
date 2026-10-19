"""Figures for the DairyGuard research book. Reads results/*/*.csv. Palette validated with the
dataviz skill's validate_palette.js (light + dark: all checks pass; light contrast WARN for aqua,
yellow, magenta -> visible value labels and tables are provided as relief)."""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from dg_kinetics import mu_sqrt, sl_gompertz

RES = os.path.join(os.path.dirname(__file__), "..", "results/base")
OUT = os.path.join(os.path.dirname(__file__), "fig")
os.makedirs(OUT, exist_ok=True)

SURF, INK, INK2, MUTED, GRID = "#fcfcfb", "#1b1b1a", "#52514e", "#8a8984", "#e4e3df"
C = {"CSL": "#2a78d6", "deg_hours_4C": "#eb6834", "t_above_5C": "#1baf7a", "t_above_8C": "#eda100", "maxT": "#e87ba4"}
LABEL = {"CSL": "Kinetic score (CSL)", "deg_hours_4C": "Degree-hours above 4 °C",
         "t_above_5C": "Time above 5 °C", "t_above_8C": "Time above 8 °C", "maxT": "Maximum temperature"}
TAU_LABEL = {"low_mass": "Low-mass pouch (time constant 5-20 min)", "insulated": "Insulated crate (time constant 1-4 h)"}
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "font.family": "DejaVu Sans", "font.size": 8.5, "text.color": INK, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": GRID, "axes.linewidth": 0.8})


def _clean(ax, grid_axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def load():
    a = pd.read_csv(f"{RES}/auc_results.csv")
    a["sampling"] = a["sampling"].astype(str)
    return a, pd.read_csv(f"{RES}/paired_contrasts.csv"), pd.read_csv(f"{RES}/calibration.csv")


def fig_trace():
    """Illustration of one trip: temperature, reference growth, and the CSL accumulator."""
    from dg_kinetics import baranyi_isothermal_time  # noqa: F401  (import check)
    P = dict(b=0.030, Tmin=-7.7, h0=3.8, N0=1.7, Nmax=9.0)
    dt = 1 / 60
    hrs = 120
    n = hrs * 60
    t = np.arange(n) / 60
    amb = np.full(n, 4.0)
    amb[(t >= 40) & (t < 42)] = 18.0
    tau = 2.0 * 60
    Tp = np.empty(n)
    Tp[0] = 4.0
    for i in range(1, n):
        Tp[i] = Tp[i - 1] + (amb[i] - Tp[i - 1]) / tau
    y = P["N0"] * np.log(10)
    ymax = P["Nmax"] * np.log(10)
    q = 1 / (np.exp(P["h0"]) - 1)
    logN = np.empty(n)
    for i in range(n):
        mu = float(mu_sqrt(np.array(Tp[i]), P["b"], P["Tmin"]))
        a = q / (1 + q)
        y += dt * mu * a * (1 - np.exp(y - ymax))
        q += dt * mu * q
        logN[i] = y / np.log(10)
    csl = np.cumsum(dt / sl_gompertz(Tp, P["b"], P["Tmin"], P["h0"], P["N0"], P["Nmax"], 3e4))
    cold = np.cumsum(dt / sl_gompertz(np.full(n, 4.0), P["b"], P["Tmin"], P["h0"], P["N0"], P["Nmax"], 3e4))
    fig, ax = plt.subplots(3, 1, figsize=(6.4, 5.6), sharex=True, gridspec_kw=dict(hspace=0.35))
    ax[0].plot(t, amb, color=MUTED, lw=1.2, ls=(0, (4, 2)))
    ax[0].plot(t, Tp, color=C["CSL"], lw=2)
    ax[0].set_ylabel("Temperature (°C)")
    ax[0].text(43, 15.5, "ambient: 2 h at 18 °C", color=INK2, fontsize=8)
    ax[0].text(43, 10.0, "milk peaks near %.0f °C\n(time constant 2 h)" % Tp.max(), color=INK2, fontsize=8)
    ax[1].plot(t, logN, color=C["CSL"], lw=2)
    ax[1].axhline(np.log10(3e4), color=MUTED, lw=1)
    ax[1].text(2, np.log10(3e4) + 0.12, "limit 3×10⁴ CFU/mL (FSSAI process-hygiene m)", color=INK2, fontsize=8)
    ax[1].set_ylabel("Reference growth\n(log₁₀ CFU/mL)")
    ax[2].plot(t, csl, color=C["CSL"], lw=2, label="with the excursion")
    ax[2].plot(t, cold, color=MUTED, lw=1.5, label="held at 4 °C throughout")
    ax[2].axhline(1.0, color=INK2, lw=0.8)
    ax[2].set_ylabel("Shelf life used\n(CSL, 1 = all)")
    ax[2].set_xlabel("Time (h)")
    ax[2].legend(frameon=False, loc="upper left", fontsize=8)
    for a_ in ax:
        _clean(a_)
    fig.savefig(f"{OUT}/trace.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return float(csl[-1]), float(cold[-1])


def _dot(ax, x, y, lo, hi, color, filled=True, label=None):
    ax.plot([lo, hi], [y, y], color=color, lw=2, solid_capstyle="round", zorder=2)
    ax.plot([x], [y], marker="o", ms=7, mfc=color if filled else SURF, mec=color, mew=1.6, zorder=3, label=label)


def fig_lin():
    import validate_lin as V
    fig, ax = plt.subplots(figsize=(7.0, 3.1))
    H = 130 * 60; t = np.arange(H) / 60
    const = np.full(H, 4.0); fl = const.copy()
    for st in (24, 52): fl[st * 60:(st + 4) * 60] = 29.0
    g0 = V.run(const, V.b, V.T0, V.h0_4); g1 = V.run(fl, V.b, V.T0, V.h0_4)
    ax.plot(t, g0, color=MUTED, lw=2, label="Model, held at 4 \u00b0C")
    ax.plot(t, g1, color=C["CSL"], lw=2, label="Model, two 4 h excursions to 29 \u00b0C")
    ax.axhline(6, color=C["deg_hours_4C"], lw=1, ls=(0, (2, 3)))
    ax.text(2, 6.12, "10\u2076 CFU/mL", fontsize=8, color=INK2)
    for x, lab, col in ((90, "Lin et al.: about 90 h", MUTED), (55, "Lin et al.: about 55 h", C["CSL"])):
        ax.plot([x], [6], marker="D", ms=8, mfc=SURF, mec=col, mew=2, zorder=4)
        ax.text(x + (3 if x == 55 else 0), 5.55 if x == 90 else 6.45, lab, ha="center" if x == 90 else "left", fontsize=8, color=INK)
    ax.set_xlabel("Storage time (h)"); ax.set_ylabel("log\u2081\u2080 CFU/mL")
    ax.set_ylim(2.5, 7.2); ax.set_xlim(0, 125)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    _clean(ax); fig.tight_layout()
    fig.savefig(f"{OUT}/lin.png", dpi=220, bbox_inches="tight"); plt.close(fig)


def fig_combase():
    import math
    d = pd.read_csv(os.path.join(os.path.dirname(__file__), "..", "data", "combase_tasmania_pasteurised_milk.csv"))
    d = d[d.temp_C < 30]
    T = np.linspace(2, 16, 100)
    f = lambda b, T0: ((b * (T - T0)) ** 2) / math.log(10)
    fig, ax = plt.subplots(figsize=(7.0, 3.3))
    ax.scatter(d.temp_C, d.max_rate_log10_per_h, s=22, color=MUTED, zorder=3, label="ComBase records (51, natural spoilage flora)")
    ax.plot(T, f(0.030, -7.7), color=C["deg_hours_4C"], lw=2, label="Neumeyer-anchored model used in Chapter 7 baseline")
    ax.plot(T, f(0.0273, -9.15), color=C["t_above_5C"], lw=2, ls=(0, (5, 2)), label="Lin-anchored model")
    ax.plot(T, f(0.0256, -6.6), color=C["CSL"], lw=2.2, label="Fitted to these records")
    ax.set_xlabel("Temperature (\u00b0C)"); ax.set_ylabel("Maximum growth rate (log\u2081\u2080 CFU/mL per h)")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left"); _clean(ax); fig.tight_layout()
    fig.savefig(f"{OUT}/combase.png", dpi=220, bbox_inches="tight"); plt.close(fig)


def fig_methods(a, thr="A_3e4", sensor="DS18B20", sampling="15"):
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.4), sharey=True)
    meths = ["CSL", "deg_hours_4C", "t_above_5C", "t_above_8C", "maxT"]
    for ax, tau in zip(axs, ["low_mass", "insulated"]):
        d = a[(a.thr == thr) & (a.tau == tau) & (a.sensor == sensor) & (a.sampling == sampling)]
        for gi, cv in enumerate([0.0, 0.10, 0.25]):
            for mi, m in enumerate(meths):
                r = d[(d.cv == cv) & (d.method == m)].iloc[0]
                x = gi + (mi - 2) * 0.13
                ax.plot([x, x], [r.lo, r.hi], color=C[m], lw=2, zorder=2)
                ax.plot([x], [r.AUC], marker="o", ms=7, color=C[m], zorder=3)
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(["cv 0", "cv 0.10", "cv 0.25"])
        ax.set_xlabel("Strain / parameter variability")
        ax.set_title(TAU_LABEL[tau], fontsize=8.5, color=INK2, loc="left")
        ax.set_ylim(0.45, 0.92)
        _clean(ax)
    axs[0].set_ylabel("AUC (95% CI)")
    handles = [plt.Line2D([], [], marker="o", ls="", ms=7, color=C[m], label=LABEL[m]) for m in meths]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=8, bbox_to_anchor=(0.5, -0.1))
    fig.tight_layout()
    fig.savefig(f"{OUT}/methods.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fig_budget(a, thr="A_3e4", cv=0.10):
    steps = [("Oracle: true biology and true temperature", ("oracle", "1", "CSL_oracle")),
             ("Nominal biology, ideal sensor, 1-min", ("ideal", "1", "CSL")),
             ("PT1000 sensor, 15-min", ("PT1000", "15", "CSL")),
             ("DS18B20 sensor, 15-min", ("DS18B20", "15", "CSL")),
             ("DS18B20 sensor, 60-min", ("DS18B20", "60", "CSL"))]
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.9), sharey=True)
    for ax, tau in zip(axs, ["low_mass", "insulated"]):
        for i, (lab, (sen, s, m)) in enumerate(steps):
            r = a[(a.thr == thr) & (a.tau == tau) & (a.cv == cv) & (a.sensor == sen) & (a.sampling == s) & (a.method == m)].iloc[0]
            col = MUTED if sen == "oracle" else C["CSL"]
            _dot(ax, r.AUC, i, r.lo, r.hi, col)
            ax.text(min(r.hi + 0.015, 1.02), i, f"{r.AUC:.2f}", va="center", fontsize=8, color=INK)
        ax.set_yticks(range(len(steps)))
        ax.set_yticklabels([s[0] for s in steps], fontsize=7.5)
        if tau != "low_mass": ax.tick_params(labelleft=False)
        if tau == "low_mass": ax.invert_yaxis()
        ax.set_xlim(0.45, 1.08)
        ax.set_xlabel("AUC (95% CI)")
        ax.set_title(TAU_LABEL[tau].split(" (")[0], fontsize=8.5, color=INK2, loc="left")
        _clean(ax, "x")
    fig.tight_layout(w_pad=0.5)
    fig.savefig(f"{OUT}/budget.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fig_forest(p, thr="A_3e4", cv=0.10):
    order = ["CSL - degree_hours_4C", "CSL - time_above_5C", "CSL - max_temperature",
             "sensor: PT1000 - DS18B20 (CSL,15min)", "sampling: 60min - 1min (DS18B20,CSL)",
             "adaptive - fixed1min (DS18B20,CSL)"]
    nice = ["Kinetic score minus degree-hours", "Kinetic score minus time above 5 °C",
            "Kinetic score minus maximum temperature", "Sensor: PT1000 minus DS18B20",
            "Sampling: 60-min minus 1-min", "Adaptive minus fixed 1-min"]
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)
    for ax, tau in zip(axs, ["low_mass", "insulated"]):
        for i, (c, nn) in enumerate(zip(order, nice)):
            r = p[(p.thr == thr) & (p.tau == tau) & (p.cv == cv) & (p.contrast == c)].iloc[0]
            _dot(ax, r["diff"], i, r.lo, r.hi, C["CSL"], filled=bool(r.excludes_zero))
        ax.axvline(0, color=INK2, lw=0.9)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels(nice, fontsize=7.5)
        if tau != "low_mass": ax.tick_params(labelleft=False)
        if tau == "low_mass": ax.invert_yaxis()
        ax.set_xlabel("Difference in AUC (paired 95% CI)")
        ax.set_title(TAU_LABEL[tau].split(" (")[0], fontsize=8.5, color=INK2, loc="left")
        _clean(ax, "x")
    fig.text(0.5, -0.04, "Filled marker: interval excludes zero.  Hollow marker: it does not.", ha="center", fontsize=8, color=INK2)
    fig.tight_layout()
    fig.savefig(f"{OUT}/forest.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fig_cal(c, thr="A_3e4"):
    variants = ["MC matched prior", "MC overconfident b (cv_prior=0)", "point alarm (nominal params)"]
    vlab = ["Uncertainty-aware (matched)", "Uncertainty-aware (overconfident growth rate)", "Single alarm (nominal values)"]
    cols = [C["CSL"], C["deg_hours_4C"], "#8a8984"]
    fig, axs = plt.subplots(2, 2, figsize=(7.0, 4.4), sharex=True)
    for j, tau in enumerate(["low_mass", "insulated"]):
        for i, (met, ttl) in enumerate([("brier", "Brier score (lower is better)"), ("ECE", "Calibration error, ECE (lower is better)")]):
            ax = axs[i, j]
            d = c[(c.thr == thr) & (c.tau == tau)]
            for vi, v in enumerate(variants):
                for gi, cv in enumerate([0.0, 0.10, 0.25]):
                    r = d[(d.cv == cv) & (d.variant == v)].iloc[0]
                    x = gi + (vi - 1) * 0.22
                    ax.bar(x, r[met], width=0.2, color=cols[vi], zorder=2)
                    ax.text(x, r[met] + 0.008, f"{r[met]:.2f}", ha="center", fontsize=6.5, color=INK)
            ax.set_xticks([0, 1, 2])
            ax.set_xticklabels(["cv 0", "cv 0.10", "cv 0.25"])
            ax.set_title((TAU_LABEL[tau].split(" (")[0] + " – " + ttl) if i == 0 else ttl, fontsize=7.8, color=INK2, loc="left")
            _clean(ax)
    handles = [plt.Rectangle((0, 0), 1, 1, color=cols[k]) for k in range(3)]
    fig.legend(handles, vlab, loc="lower center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout()
    fig.savefig(f"{OUT}/calibration.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fig_lis():
    """Listeria monocytogenes in milk: ComBase records, fitted curve, held-out records, and the temperature sensitivity of the two organisms."""
    import math, json
    root = os.path.join(os.path.dirname(__file__), "..")
    d = pd.read_csv(os.path.join(root, "data", "combase_milk_full_ocr.csv"))
    d = d[d.organism.fillna("").str.startswith("Listeria") & d.max_rate_log10_per_h.notna()].copy()
    d["T"] = pd.to_numeric(d.temp_C, errors="coerce"); d = d[d["T"].between(2, 16)]
    clean = d.conditions.fillna("").str.contains("Not specified")
    v = json.load(open(os.path.join(root, "results", "validation_lis.json")))
    T = np.linspace(2, 16, 100)
    f = lambda b, T0: ((b * (T - T0)) ** 2) / math.log(10)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 3.3), gridspec_kw={"width_ratios": [1.25, 1]})
    a1.scatter(d[clean]["T"], d[clean].max_rate_log10_per_h, s=20, color=C["CSL"], zorder=3, label=f"Fitted records (n = {v['n_fit']})")
    a1.scatter(d[~clean]["T"], d[~clean].max_rate_log10_per_h, s=20, facecolors="none", edgecolors=C["deg_hours_4C"], zorder=3, label=f"Held-out records (n = {v['n_heldout']})")
    a1.plot(T, f(v["b_ln"], v["Tmin_C"]), color=INK, lw=1.8, label="Square-root fit")
    a1.set_xlabel("Temperature (\u00b0C)"); a1.set_ylabel("Max growth rate (log\u2081\u2080 CFU/mL per h)")
    a1.set_title("Listeria monocytogenes in milk", fontsize=8.5, color=INK2, loc="left"); a1.legend(frameon=False, fontsize=7, loc="upper left"); _clean(a1)
    ref = lambda b, T0, t: (b * (t - T0)) ** 2
    pseud = ref(0.0256, -6.6, T) / ref(0.0256, -6.6, 4.0); lis = ref(v["b_ln"], v["Tmin_C"], T) / ref(v["b_ln"], v["Tmin_C"], 4.0)
    a2.plot(T, pseud, color=C["CSL"], lw=2, label="Spoilage flora"); a2.plot(T, lis, color=C["deg_hours_4C"], lw=2, label="Listeria")
    a2.set_xlabel("Temperature (\u00b0C)"); a2.set_ylabel("Growth rate relative to 4 \u00b0C"); a2.legend(frameon=False, fontsize=7.5, loc="upper left")
    a2.set_title("A warm hour costs a pathogen more", fontsize=8.5, color=INK2, loc="left"); _clean(a2)
    fig.tight_layout(); fig.savefig(f"{OUT}/lis.png", dpi=220, bbox_inches="tight"); plt.close(fig)


RUNS = [("results/base", "Baseline"), ("results/lag", "Extra lag after shifts"), ("results/low", "Low starting load"),
        ("results/comb", "Fitted to milk flora"), ("results/lis", "Listeria (hazard)")]


def fig_runs():
    """Range of four headline effects across the 12 settings of each benchmark run."""
    root = os.path.join(os.path.dirname(__file__), "..")
    q = [("CSL - degree_hours_4C", "Kinetic score beats degree-hours by"), ("biology gap: oracle - ideal(1min,CSL)", "Loss to unobservable biology"),
         ("sensor: PT1000 - DS18B20 (CSL,15min)", "Gain from a better sensor"), ("sampling: 60min - 1min (DS18B20,CSL)", "Change from sampling hourly vs every minute")]
    runs = [(d, n) for d, n in RUNS if os.path.exists(os.path.join(root, d, "paired_contrasts.csv"))]
    cols = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
    fig, axes = plt.subplots(1, 4, figsize=(7.6, 2.9), sharey=True)
    for ax, (cn, ttl) in zip(axes, q):
        for i, (d, n) in enumerate(runs):
            p = pd.read_csv(os.path.join(root, d, "paired_contrasts.csv")); x = p[p.contrast == cn]["diff"]
            ax.plot([x.min(), x.max()], [i, i], color=cols[i], lw=5, solid_capstyle="butt")
            ax.plot([x.median()], [i], "o", color=SURF, ms=3.5, zorder=4)
        ax.axvline(0, color=MUTED, lw=0.8); ax.set_title(ttl, fontsize=7, color=INK2, loc="left", wrap=True); _clean(ax, "x")
        ax.set_xlabel("AUC difference", fontsize=7)
    axes[0].set_yticks(range(len(runs))); axes[0].set_yticklabels([n for _, n in runs], fontsize=7.5); axes[0].invert_yaxis()
    fig.tight_layout(); fig.savefig(f"{OUT}/runs.png", dpi=220, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    used, cold = fig_trace()
    print("trace ok; CSL end with excursion %.3f vs cold %.3f" % (used, cold))
    if os.path.exists(f"{RES}/calibration.csv"):
        a, p, c = load()
        fig_methods(a)
        fig_budget(a)
        fig_forest(p)
        fig_cal(c)
        fig_lin()
        fig_combase()
        fig_lis()
        fig_runs()
        print("result figures ok")

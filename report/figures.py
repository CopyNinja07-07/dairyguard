"""Figures for the DairyGuard book. Reads results/*/*.csv. Palette validated with the
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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "experiments"))
from dairyguard.kinetics import mu_sqrt, sl_gompertz

RES = os.path.join(os.path.dirname(__file__), "..", "results/base")
OUT = os.path.join(os.path.dirname(__file__), "fig")
os.makedirs(OUT, exist_ok=True)

SURF, INK, INK2, MUTED, GRID = "#fcfcfb", "#1b1b1a", "#52514e", "#8a8984", "#e4e3df"
C = {"CSL": "#5a1f52", "deg_hours_4C": "#eb6834", "t_above_5C": "#1baf7a", "t_above_8C": "#eaaa00", "maxT": "#e87ba4"}
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
    from dairyguard.kinetics import baranyi_isothermal_time  # noqa: F401  (import check)
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


if __name__ == "__main__":
    used, cold = fig_trace()
    print("trace ok; CSL end with excursion %.3f vs cold %.3f" % (used, cold))
    a, p, c = load()
    fig_methods(a); fig_forest(p); fig_cal(c); fig_lin()
    print("report figures ok")

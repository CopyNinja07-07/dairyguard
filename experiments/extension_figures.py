"""Figures for the growth-law study and the monitor studies (book chapter 'Further results').

Reads results/growth_laws/* and results/monitor_studies.json; writes PDFs to generated/fig/ and PNG copies to
docs/img/ for the website and README. Run after experiments/growth_law_study.py and experiments/monitor_studies.py."""
import json
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "generated"))
OUT, IMG = os.path.join(ROOT, "generated", "fig"), os.path.join(ROOT, "docs", "img")
os.makedirs(OUT, exist_ok=True); os.makedirs(IMG, exist_ok=True)

INK, INK2, GRID = "#1a1a1a", "#4a4a4a", "#e3e3e3"
BLUE, ORANGE, GREEN, GOLD, PINK, GREY = "#5a1f52", "#d1622b", "#2e8b57", "#d99e00", "#b4467a", "#8c8c8c"
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "DejaVu Sans"],
                     "font.size": 8, "axes.labelsize": 8, "legend.fontsize": 7.5, "xtick.labelsize": 7.5,
                     "ytick.labelsize": 7.5, "axes.edgecolor": INK2, "axes.linewidth": 0.6, "pdf.fonttype": 42,
                     "figure.facecolor": "white", "savefig.facecolor": "white"})
W2 = 174 / 25.4
LAWCOL = {"square-root": BLUE, "Arrhenius": ORANGE, "Q10": GOLD, "Davey": PINK, "neural": GREEN}


def clean(ax, grid="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if grid:
        ax.grid(axis=grid, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".pdf"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(os.path.join(IMG, name + ".png"), bbox_inches="tight", pad_inches=0.05, dpi=200)
    plt.close(fig)


def fig_growth_laws():
    cv = pd.read_csv(os.path.join(ROOT, "results/growth_laws/cv_scores.csv"))
    pr = pd.read_csv(os.path.join(ROOT, "results/growth_laws/heldout_predictions.csv"))
    nc = pd.read_csv(os.path.join(ROOT, "results/growth_laws/neural_curve.csv"))
    var = json.load(open(os.path.join(ROOT, "results/growth_laws/variation.json")))
    fig, axs = plt.subplots(1, 3, figsize=(W2, 2.35), gridspec_kw=dict(width_ratios=[1.05, 1, 1]))
    ax = axs[0]
    laws = list(LAWCOL)
    for j, data in enumerate(cv.data.unique()):
        sub = cv[cv.data == data].set_index("law").loc[laws]
        y = np.arange(len(laws)) + (0.2 if j else -0.2)
        ax.barh(y, sub.Af - 1, height=0.36, left=1, color=[LAWCOL[l] for l in laws], alpha=1 if j == 0 else 0.45,
                label=data.split(" (")[0])
    ax.set_yticks(range(len(laws))); ax.set_yticklabels(laws); ax.invert_yaxis()
    ax.set_xlim(1, 1.8); ax.set_xlabel("held-out accuracy factor (1 = perfect)")
    ax.legend(frameon=False, loc="lower right", handlelength=1, fontsize=7)
    ax.set_title("(a) Held-out accuracy", loc="left", fontweight="bold"); clean(ax, "x")
    ax = axs[1]
    lis = pr[(pr.data.str.startswith("Listeria")) & (pr.law == "square-root")]
    ax.scatter(lis["T"], np.log10(lis.mu_obs / np.log(10)), s=7, color=GREY, alpha=.7, lw=0, label="ComBase records")
    ax.plot(nc["T"], np.log10(nc.mu_sqrt / np.log(10)), color=BLUE, lw=1.2, label="square-root law")
    lo, hi = nc.mu_neural * np.exp(-2 * nc.sd_ln_neural), nc.mu_neural * np.exp(2 * nc.sd_ln_neural)
    ax.fill_between(nc["T"], np.log10(lo / np.log(10)), np.log10(hi / np.log(10)), color=GREEN, alpha=.18, lw=0)
    ax.plot(nc["T"], np.log10(nc.mu_neural / np.log(10)), color=GREEN, lw=1.2, label="monotone neural law")
    ax.set_xlabel("temperature (°C)"); ax.set_ylabel("log$_{10}$ growth rate (log CFU/mL per h)")
    ax.legend(frameon=False, loc="upper left", fontsize=7); ax.set_title("(b) Listeria, 0–15 °C", loc="left", fontweight="bold"); clean(ax)
    ax = axs[2]
    b = np.array(sorted(var["study_b"].values()))
    ax.barh(range(len(b)), b, color=BLUE, alpha=.75, height=.7)
    ax.axvline(var["b_median"], color=INK2, lw=.8, ls="--")
    ax.set_yticks([]); ax.set_xlabel(f"slope b of each study (cv {var['cv_b']:.2f})")
    ax.set_title(f"(c) Spread between studies", loc="left", fontweight="bold"); clean(ax, "x")
    fig.tight_layout(w_pad=1.2)
    save(fig, "growthlaws")


def fig_monitor():
    m = json.load(open(os.path.join(ROOT, "results/monitor_studies.json")))
    fig, axs = plt.subplots(1, 3, figsize=(W2, 2.2))
    ax = axs[0]
    tb = m["trained_baseline"]["insulated"]
    names = ["single alarm", "logistic regression (trained)", "DairyGuard probability"]
    labels = ["single alarm", "logistic regression\n(trained on 4,000 trips)", "DairyGuard probability\n(no training labels)"]
    ax.barh(range(3), [tb[n]["ECE"] for n in names], color=[ORANGE, GREY, GREEN], height=.6)
    ax.set_yticks(range(3)); ax.set_yticklabels(labels); ax.set_xlabel("calibration error (lower is better)")
    for i, n in enumerate(names):
        ax.text(tb[n]["ECE"] + .008, i, f"AUC {tb[n]['AUC']:.3f}", va="center", fontsize=7, color=INK2)
    ax.set_xlim(0, .5); ax.set_title("(a) Calibration", loc="left", fontweight="bold"); clean(ax, "x")
    ax = axs[1]
    mc = m["mc_convergence"]; K = sorted(int(k) for k in mc)
    ax.plot(K, [mc[str(k)]["ECE"] for k in K], "o-", color=GREEN, ms=3, lw=1)
    ax.axvline(80, color=INK2, lw=.7, ls="--"); ax.text(84, .14, "80 used", fontsize=7, color=INK2)
    ax.set_xscale("log", base=2); ax.set_xticks(K); ax.set_xticklabels(K)
    ax.set_xlabel("plausible batches K"); ax.set_ylabel("calibration error")
    ax.set_title("(b) Batches needed", loc="left", fontweight="bold"); clean(ax)
    ax = axs[2]
    cb = m["correlated_biology"]; r = sorted(float(k) for k in cb)
    ax.bar(range(3), [cb[str(k) if str(k) in cb else repr(k)]["loss_to_biology"] for k in r], color=BLUE, alpha=.8, width=.6)
    ax.set_xticks(range(3)); ax.set_xticklabels([f"ρ = {k:+.1f}" for k in r])
    ax.set_ylabel("AUC lost to biology"); ax.set_ylim(0, .5)
    ax.set_title("(c) Correlated biology", loc="left", fontweight="bold"); clean(ax)
    fig.tight_layout(w_pad=1.0)
    save(fig, "monitorstudies")


if __name__ == "__main__":
    fig_growth_laws()
    fig_monitor()
    print("extension figures ok")

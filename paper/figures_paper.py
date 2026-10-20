"""Vector figures for the research paper (white background, serif type, lettered panels).
Run from the repository root: python paper/figures_paper.py"""
import os
import sys
import json
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "paper", "fig")
os.makedirs(OUT, exist_ok=True)

INK, INK2, MUTED, GRID = "#1a1a1a", "#4a4a4a", "#8c8c8c", "#e3e3e3"
BLUE, ORANGE, GREEN, GOLD, PINK = "#1f5fa8", "#d1622b", "#2e8b57", "#c99400", "#b4467a"
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["STIXGeneral", "DejaVu Serif"], "mathtext.fontset": "stix",
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8, "legend.fontsize": 7,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": INK2, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "figure.facecolor": "white",
    "savefig.facecolor": "white", "pdf.fonttype": 42})
W1, W2 = 3.45, 7.1   # column and page width, inches


def clean(ax, grid="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if grid:
        ax.grid(axis=grid, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def tag(ax, letter, title=""):
    ax.set_title(f"({letter}) {title}".strip(), loc="left", fontsize=8, color=INK, pad=4)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


# ---------------------------------------------------------------- Fig. 1: benchmark design
def fig_design():
    fig, ax = plt.subplots(figsize=(W2, 2.25))
    ax.set_xlim(0, 100); ax.set_ylim(2, 32.5); ax.axis("off")

    def box(x, y, w, h, text, fc="#eef3fa", ec=BLUE, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2",
                                    fc=fc, ec=ec, lw=0.8))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=7,
                fontweight="bold" if bold else "normal", color=INK, linespacing=1.25)

    def arrow(x0, y0, x1, y1, c=INK2):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", lw=0.8, color=c, shrinkA=1, shrinkB=1, mutation_scale=8))

    # top row: what is true
    ax.text(62, 30.2, "Simulated truth (hidden from the monitor)", fontsize=7.5, color=ORANGE, fontweight="bold")
    box(0.5, 20.5, 19, 7.5, "Trip temperature\n(excursions, product\nthermal inertia)", "#fdf1ea", ORANGE)
    box(24, 20.5, 19, 7.5, "Trip biology\n(strain rate $b$, $T_{\\min}$,\nlag, starting load)", "#fdf1ea", ORANGE)
    box(47.5, 20.5, 21, 7.5, "Reference growth model\n(Baranyi–Roberts,\nsquare-root law)", "#fdf1ea", ORANGE)
    box(73, 20.5, 26, 7.5, "True label:\nlimit exceeded within\nthe label horizon?", "#fdf1ea", ORANGE, bold=True)
    ax.plot([10, 10, 58], [28.3, 29.4, 29.4], color=ORANGE, lw=0.8, solid_capstyle="butt")
    arrow(58, 29.4, 58, 28.3, ORANGE)
    arrow(43.1, 24.2, 47.4, 24.2, ORANGE); arrow(68.6, 24.2, 72.9, 24.2, ORANGE)

    # bottom row: what the monitor does
    ax.text(13, 14.2, "What a monitor sees and computes", fontsize=7.5, color=BLUE, fontweight="bold")
    box(0.5, 3.5, 17, 8, "Sensor\n(offset, noise,\nquantisation)")
    box(21, 3.5, 15, 8, "Sampling\n(1, 15 or\n60 min)")
    box(39.5, 3.5, 22, 8, "Score from the record\n(kinetic CSL or\nsimple rule)")
    box(65, 3.5, 34, 8, "Compare scores with the true label\nAUC with paired bootstrap\non identical trips", bold=False)
    arrow(10, 20.4, 9, 11.6)
    arrow(17.6, 7.5, 20.9, 7.5); arrow(36.1, 7.5, 39.4, 7.5); arrow(61.6, 7.5, 64.9, 7.5)
    arrow(86, 20.4, 86, 11.6, ORANGE)
    save(fig, "design.pdf")


# ---------------------------------------------------------------- Fig. 2: ComBase spoilage flora
def fig_combase():
    d = pd.read_csv(os.path.join(ROOT, "data", "combase_tasmania_pasteurised_milk.csv"))
    d = d[d.temp_C < 30]
    T = np.linspace(2, 16, 100)
    f = lambda b, T0: ((b * (T - T0)) ** 2) / math.log(10)
    fig, ax = plt.subplots(figsize=(W1, 2.35))
    ax.scatter(d.temp_C, d.max_rate_log10_per_h, s=11, color=MUTED, lw=0, zorder=3, label="ComBase records ($n=51$)")
    ax.plot(T, f(0.030, -7.7), color=ORANGE, lw=1.3, label="Neumeyer-anchored (baseline)")
    ax.plot(T, f(0.0273, -9.15), color=GREEN, lw=1.3, ls=(0, (4, 2)), label="Lin-anchored")
    ax.plot(T, f(0.0256, -6.6), color=BLUE, lw=1.5, label="Fitted to the records")
    ax.set_xlabel("Temperature (°C)"); ax.set_ylabel("Max. growth rate (log$_{10}$ CFU mL$^{-1}$ h$^{-1}$)")
    ax.set_xlim(1.5, 16.5); ax.set_ylim(0, None)
    ax.legend(frameon=False, loc="upper left", handlelength=1.8); clean(ax)
    save(fig, "combase.pdf")


# ---------------------------------------------------------------- Fig. 3: Listeria
def fig_lis():
    d = pd.read_csv(os.path.join(ROOT, "data", "combase_milk_full.csv"))
    d = d[d.organism.fillna("").str.startswith("Listeria") & d.max_rate_log10_per_h.notna()].copy()
    d["T"] = pd.to_numeric(d.temp_C, errors="coerce"); d = d[d["T"].between(2, 16)]
    fitset = d.conditions.fillna("").str.contains("Not specified")
    v = json.load(open(os.path.join(ROOT, "results", "validation_lis.json")))
    T = np.linspace(2, 16, 100)
    f = lambda b, T0: ((b * (T - T0)) ** 2) / math.log(10)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W2 * 0.82, 2.35), gridspec_kw={"width_ratios": [1.2, 1]})
    a1.scatter(d[fitset]["T"], d[fitset].max_rate_log10_per_h, s=11, color=BLUE, lw=0, zorder=3, label=f"Fitted ($n={v['n_fit']}$)")
    a1.scatter(d[~fitset]["T"], d[~fitset].max_rate_log10_per_h, s=11, facecolors="none", edgecolors=ORANGE, lw=0.7, zorder=3, label=f"Held out ($n={v['n_heldout']}$)")
    a1.plot(T, f(v["b_ln"], v["Tmin_C"]), color=INK, lw=1.2, label="Square-root fit")
    a1.set_xlabel("Temperature (°C)"); a1.set_ylabel("Max. growth rate (log$_{10}$ CFU mL$^{-1}$ h$^{-1}$)")
    tag(a1, "a", "$\\it{L.\\ monocytogenes}$ in milk"); a1.legend(frameon=False, loc="upper left"); clean(a1)
    r = lambda b, T0, t: (b * (t - T0)) ** 2
    a2.plot(T, r(0.0256, -6.6, T) / r(0.0256, -6.6, 4.0), color=BLUE, lw=1.4, label="Spoilage flora")
    a2.plot(T, r(v["b_ln"], v["Tmin_C"], T) / r(v["b_ln"], v["Tmin_C"], 4.0), color=ORANGE, lw=1.4, label="$\\it{Listeria}$")
    a2.axhline(1, color=MUTED, lw=0.5, ls=":")
    a2.set_xlabel("Temperature (°C)"); a2.set_ylabel("Growth rate relative to 4 °C")
    tag(a2, "b", "Sensitivity to warming"); a2.legend(frameon=False, loc="upper left"); clean(a2)
    fig.tight_layout(w_pad=1.5)
    save(fig, "lis.pdf")


# ---------------------------------------------------------------- Fig. 4: loss budget
def fig_budget(thr="A_3e4", cv=0.10):
    a = pd.read_csv(os.path.join(ROOT, "results", "base", "auc_results.csv")); a["sampling"] = a["sampling"].astype(str)
    steps = [("Oracle (true biology,\ntrue temperature)", ("oracle", "1", "CSL_oracle")),
             ("Nominal biology,\nideal sensor, 1 min", ("ideal", "1", "CSL")),
             ("PT1000, 15 min", ("PT1000", "15", "CSL")),
             ("DS18B20, 15 min", ("DS18B20", "15", "CSL")),
             ("DS18B20, 60 min", ("DS18B20", "60", "CSL"))]
    fig, axs = plt.subplots(1, 2, figsize=(W1, 2.3), sharey=True)
    for ax, tau, letter, ttl in zip(axs, ["low_mass", "insulated"], "ab", ["Low-mass pouch", "Insulated crate"]):
        for i, (lab, (sen, s, m)) in enumerate(steps):
            row = a[(a.thr == thr) & (a.tau == tau) & (a.cv == cv) & (a.sensor == sen) & (a.sampling == s) & (a.method == m)].iloc[0]
            col = MUTED if sen == "oracle" else BLUE
            ax.plot([row.lo, row.hi], [i, i], color=col, lw=1.2)
            ax.plot([row.AUC], [i], "o", color=col, ms=3.6)
            if sen == "oracle":
                ax.text(row.AUC - 0.03, i, f"{row.AUC:.2f}", ha="right", va="center", fontsize=7, color=INK2)
            else:
                ax.text(row.hi + 0.025, i, f"{row.AUC:.2f}", ha="left", va="center", fontsize=7, color=INK2)
        ax.set_yticks(range(len(steps))); ax.set_yticklabels([s[0] for s in steps], fontsize=7)
        ax.set_xlim(0.5, 1.04); ax.set_ylim(len(steps) - 0.5, -0.6)
        ax.set_xlabel("AUC (95% CI)"); tag(ax, letter, ttl); clean(ax, "x")
        if letter == "b":
            ax.tick_params(labelleft=False)
    fig.tight_layout(w_pad=0.6)
    save(fig, "budget.pdf")


# ---------------------------------------------------------------- Fig. 5: robustness across runs
RUNS = [("base", "Baseline"), ("lag", "Extra lag after shifts"), ("low", "Low starting load"),
        ("comb", "Fitted to milk flora"), ("lis", "$\\it{Listeria}$ (hazard)")]


def fig_runs():
    q = [("biology gap: oracle - ideal(1min,CSL)", "Loss to unobserved biology"),
         ("CSL - degree_hours_4C", "Kinetic score minus degree-hours"),
         ("sensor: PT1000 - DS18B20 (CSL,15min)", "PT1000 minus DS18B20"),
         ("sampling: 60min - 1min (DS18B20,CSL)", "Hourly minus every-minute sampling")]
    cols = [BLUE, ORANGE, GREEN, GOLD, PINK]
    fig, axs = plt.subplots(2, 2, figsize=(W2, 3.3), sharey=True)
    axes = axs.ravel()
    for ax, (cn, ttl), letter in zip(axes, q, "abcd"):
        for i, (d, n) in enumerate(RUNS):
            p = pd.read_csv(os.path.join(ROOT, "results", d, "paired_contrasts.csv"))
            x = p[p.contrast == cn]["diff"]
            ax.plot([x.min(), x.max()], [i, i], color=cols[i], lw=4, solid_capstyle="butt")
            ax.plot([x.median()], [i], "o", color="white", mec=INK, mew=0.5, ms=3, zorder=4)
        ax.axvline(0, color=INK2, lw=0.6)
        tag(ax, letter, ttl)
        ax.set_xlabel("AUC difference"); clean(ax, "x")
        ax.margins(x=0.12)
    for ax in (axes[0], axes[2]):
        ax.set_yticks(range(len(RUNS))); ax.set_yticklabels([n for _, n in RUNS])
    axes[0].set_ylim(len(RUNS) - 0.5, -0.6)
    fig.tight_layout(w_pad=1.2, h_pad=1.0)
    save(fig, "runs.pdf")


if __name__ == "__main__":
    fig_design(); fig_combase(); fig_lis(); fig_budget(); fig_runs()
    print("paper figures ok:", sorted(os.listdir(OUT)))

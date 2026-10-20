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
    "font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "DejaVu Sans"], "mathtext.fontset": "custom", "mathtext.rm": "Liberation Sans", "mathtext.it": "Liberation Sans:italic", "mathtext.bf": "Liberation Sans:bold",
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8, "legend.fontsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": INK2, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "figure.facecolor": "white",
    "savefig.facecolor": "white", "pdf.fonttype": 42})
W1, W2 = 84 / 25.4, 174 / 25.4   # column and page width (84 mm, 174 mm)


def clean(ax, grid="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if grid:
        ax.grid(axis=grid, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def tag(ax, letter, title=""):
    ax.set_title(f"({letter})", loc="left", fontsize=8, color=INK, pad=4, fontweight="bold")


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


# ---------------------------------------------------------------- Fig. 1: benchmark design
def fig_design():
    fig, ax = plt.subplots(figsize=(W2, 2.75)); ax.set_xlim(0, 100); ax.set_ylim(-1, 40); ax.axis("off")
    ax.text(0, 38.5, "Simulated truth, hidden from the monitor", fontsize=8, color=ORANGE, fontweight="bold", va="center")
    top = [(0, "Trip temperature\n(warm spells,\nthermal inertia)"), (25.5, "Trip biology\n(b, T$_{\\min}$, lag,\nstarting load)"),
           (51, "Reference growth\nmodel\n(Baranyi–Roberts)"), (76.5, "True label:\nlimit passed by\nthe horizon?")]
    for x, t in top:
        _box(ax, x, 22, 23.5, 12.5, t, "#fdf1ea", ORANGE, bold=t.startswith("True"))
    _arr(ax, 49.3, 28.2, 50.7, 28.2, ORANGE); _arr(ax, 74.8, 28.2, 76.2, 28.2, ORANGE)
    ax.plot([11.75, 11.75, 62.75], [34.8, 36.3, 36.3], color=ORANGE, lw=.8); _arr(ax, 62.75, 36.3, 62.75, 34.8, ORANGE)
    ax.text(0, 17.5, "What a monitor sees and computes", fontsize=8, color=BLUE, fontweight="bold", va="center")
    bot = [(0, "Sensor\n(offset, noise,\nresolution)"), (25.5, "Sampling\n(every 1, 15\nor 60 min)"), (51, "Score from\nthe record\n(CSL or a rule)"), (76.5, "Compare with the\ntrue label: AUC,\npaired bootstrap")]
    for x, t in bot:
        _box(ax, x, 1, 23.5, 12.5, t)
    for x in (23.7, 49.2):
        _arr(ax, x, 7.2, x + 1.6, 7.2)
    _arr(ax, 74.7, 7.2, 76.3, 7.2)
    _arr(ax, 11.75, 21.6, 11.75, 13.9); _arr(ax, 88.25, 21.6, 88.25, 13.9, ORANGE)
    save(fig, "design.pdf")


# ---------------------------------------------------------------- Fig. 2: ComBase spoilage flora
def fig_combase():
    d = pd.read_csv(os.path.join(ROOT, "data", "combase_tasmania_pasteurised_milk.csv"))
    d = d[d.temp_C < 30]
    T = np.linspace(2, 16, 100)
    f = lambda b, T0: ((b * (T - T0)) ** 2) / math.log(10)
    fig, ax = plt.subplots(figsize=(W1, 2.35))
    ax.scatter(d.temp_C, d.max_rate_log10_per_h, s=11, color=MUTED, lw=0, zorder=3, label="ComBase records ($n=51$)")
    ax.plot(T, f(0.030, -7.7), color=ORANGE, lw=1.3, ls=(0, (1.5, 1.2)), label="Neumeyer-anchored (baseline)")
    ax.plot(T, f(0.0273, -9.15), color=GREEN, lw=1.3, ls=(0, (4, 2)), label="Lin-anchored")
    ax.plot(T, f(0.0256, -6.6), color=BLUE, lw=1.5, label="Fitted to the records")
    ax.set_xlabel("Temperature/°C"); ax.set_ylabel("Max. growth rate/log$_{10}$ CFU mL$^{-1}$ h$^{-1}$")
    ax.set_xlim(1.5, 16.5); ax.set_ylim(0, None)
    ax.legend(frameon=False, loc="upper left", handlelength=1.8); clean(ax)
    save(fig, "combase.pdf")


# ---------------------------------------------------------------- Fig. 3: Listeria
def fig_lis():
    d = pd.read_csv(os.path.join(ROOT, "data", "combase_milk_records.csv"))
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
    a1.set_xlabel("Temperature/°C"); a1.set_ylabel("Max. growth rate/log$_{10}$ CFU mL$^{-1}$ h$^{-1}$")
    tag(a1, "a", "$\\it{L.\\ monocytogenes}$ in milk"); a1.legend(frameon=False, loc="upper left"); clean(a1)
    r = lambda b, T0, t: (b * (t - T0)) ** 2
    a2.plot(T, r(0.0256, -6.6, T) / r(0.0256, -6.6, 4.0), color=BLUE, lw=1.4, label="Spoilage flora")
    a2.plot(T, r(v["b_ln"], v["Tmin_C"], T) / r(v["b_ln"], v["Tmin_C"], 4.0), color=ORANGE, lw=1.4, ls=(0, (4, 2)), label="$\\it{Listeria}$")
    a2.axhline(1, color=MUTED, lw=0.5, ls=":")
    a2.set_xlabel("Temperature/°C"); a2.set_ylabel("Growth rate relative to 4 °C")
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
                ax.text(row.AUC - 0.03, i, f"{row.AUC:.2f}", ha="right", va="center", fontsize=8, color=INK2)
            else:
                ax.text(row.hi + 0.025, i, f"{row.AUC:.2f}", ha="left", va="center", fontsize=8, color=INK2)
        ax.set_yticks(range(len(steps))); ax.set_yticklabels([s[0] for s in steps], fontsize=8)
        ax.set_xlim(0.5, 1.04); ax.set_ylim(len(steps) - 0.5, -0.6)
        ax.set_xlabel("AUC (95 % CI)"); tag(ax, letter, ttl); clean(ax, "x")
        if letter == "b":
            ax.tick_params(labelleft=False)
    fig.tight_layout(w_pad=0.6)
    save(fig, "budget.pdf")


# ---------------------------------------------------------------- Fig. 5: robustness across runs
RUNS = [("base", "Baseline"), ("lag", "Extra lag after shifts"), ("low", "Low starting load"),
        ("comb", "Fitted to milk flora"), ("lis", "$\\it{Listeria}$ (hazard)")]


def fig_runs():
    q = [("biology gap: oracle - ideal(1min,CSL)", "What biology costs: oracle minus best monitor"),
         ("CSL - degree_hours_4C", "What a growth model adds over degree-hours"),
         ("sensor: PT1000 - DS18B20 (CSL,15min)", "What a better sensor adds: PT1000 minus DS18B20"),
         ("sampling: 60min - 1min (DS18B20,CSL)", "What slower sampling costs: hourly minus every minute")]
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
        ax.set_xlabel("AUC difference (right of 0 = first option better)"); clean(ax, "x")
        ax.margins(x=0.12)
    for ax in (axes[0], axes[2]):
        ax.set_yticks(range(len(RUNS))); ax.set_yticklabels([n for _, n in RUNS])
    axes[0].set_ylim(len(RUNS) - 0.5, -0.6)
    fig.tight_layout(w_pad=1.2, h_pad=1.0)
    save(fig, "runs.pdf")


def _box(ax, x, y, w, h, text, fc="#eef3fa", ec=BLUE, bold=False, fs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=1.0", fc=fc, ec=ec, lw=.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=INK, linespacing=1.2)


def _arr(ax, x0, y0, x1, y1, c=INK2):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=.8, color=c, shrinkA=1, shrinkB=1, mutation_scale=7))


# ---------------------------------------------------------------- flowchart of the benchmark
# ================================================================= explanatory figures
B0, TM0 = 0.030, -7.7
mu_of = lambda T, b=B0, tm=TM0: np.where(T > tm, (b * (T - tm)) ** 2, 0.0)


def baranyi_path(T, dt, b, tm, h0, l0, ymax=9.0):
    y = l0 * math.log(10); q = 1 / (math.exp(h0) - 1); ym = ymax * math.log(10); out = np.empty(len(T))
    for i, Ti in enumerate(T):
        mu = (b * (Ti - tm)) ** 2 if Ti > tm else 0.0
        y += dt * mu * q / (1 + q) * (1 - math.exp(y - ym)); q += dt * mu * q; out[i] = y / math.log(10)
    return out


def K_of(h0, l0, NL=3e4, nmax=9.0):
    A, L = nmax - l0, math.log10(NL) - l0
    return h0 + A * math.log(10) / math.e * (1 - math.log(-math.log(L / A)))


def callout(ax, x, y, n, col=INK):
    ax.scatter([x], [y], s=95, color="white", edgecolor=col, lw=1.0, zorder=6, clip_on=False)
    ax.text(x, y, str(n), ha="center", va="center", fontsize=8, fontweight="bold", color=col, zorder=7, clip_on=False)


# ---------------------------------------------------------------- Fig: one trip, three cartons (story)
def fig_story():
    H = 72; dt = 1 / 60; n = H * 60
    t = np.arange(n) * dt
    amb = np.full(n, 4.0)
    ev = [(6, 7.5, 18.0, "truck door left open, 90 min"), (30, 31, 12.0, "shelf restocking, 1 h"), (48, 50, 22.0, "left on the kitchen counter, 2 h")]
    for a0_, a1_, Tv, _ in ev:
        amb[(t >= a0_) & (t < a1_)] = Tv
    T = np.empty(n); x = 4.0; k = 1 - math.exp(-dt / 0.6)
    for i in range(n):
        x += (amb[i] - x) * k; T[i] = x
    cart = [("A", "few bacteria, slow strain", 0.026, -9.0, 5.0, 1.3, GREEN),
            ("B", "typical carton", 0.030, -7.7, 4.5, 1.55, GOLD),
            ("C", "more bacteria, fast strain", 0.034, -6.5, 2.7, 2.00, ORANGE)]
    lim = math.log10(3e4)
    fig = plt.figure(figsize=(W2, 8.0))
    gs = fig.add_gridspec(5, 1, height_ratios=[0.5, 1.05, 1.3, 1.0, 0.62], hspace=0.62)
    a0 = fig.add_subplot(gs[0]); a1 = fig.add_subplot(gs[1]); a2 = fig.add_subplot(gs[2], sharex=a1)
    a3 = fig.add_subplot(gs[3], sharex=a1); a4 = fig.add_subplot(gs[4])
    ttl = dict(loc="left", fontsize=8, pad=5, fontweight="bold")
    # (a) the journey
    a0.set_xlim(0, H); a0.set_ylim(0, 1); a0.axis("off")
    stages = [(0, 5.5, "Dairy", "0–6 h"), (5.5, 12, "Truck", "6–12 h"), (12, 30, "Depot cold store", "12–30 h"),
              (30, 48, "Shop shelf", "30–48 h"), (48, 72, "Home fridge", "48–72 h")]
    for i, (x0, x1, h, sub) in enumerate(stages):
        a0.add_patch(FancyBboxPatch((x0 + .35, .05), x1 - x0 - .7, .8, boxstyle="round,pad=0,rounding_size=.25", fc="#eef3fa", ec=BLUE, lw=.8, mutation_aspect=0.1))
        a0.text((x0 + x1) / 2, .58, h, ha="center", va="center", fontsize=8 if x1 - x0 > 7 else 6.8, fontweight="bold")
        a0.text((x0 + x1) / 2, .27, sub, ha="center", va="center", fontsize=8, color=INK2)
    for j, (s0, s1, _, _) in enumerate(ev):
        callout(a0, (s0 + s1) / 2 + (1.2 if j == 0 else 0), 1.0, j + 1, ORANGE)
    a0.set_title("(a)", **ttl)
    # (b) the log
    a1.axhspan(2, 8, color="#eef7f1", lw=0, zorder=0)
    a1.text(71.5, 7.7, "recommended 2–8 °C", ha="right", va="top", fontsize=8, color=GREEN)
    a1.plot(t, amb, color=ORANGE, lw=.9, ls=(0, (2, 1.5)), label="ambient air")
    a1.plot(t, T, color=BLUE, lw=1.7, label="product temperature")
    a1.plot(t[::60], T[::60], "o", ms=2.3, color=INK, label="logger reading, every hour")
    for j, (s0, s1, Tv, lab) in enumerate(ev):
        callout(a1, s0 - 2.2, Tv - 1, j + 1, ORANGE)
        a1.text(s1 + 1.0, Tv - 1, lab, fontsize=8, va="center", color=INK2)
    a1.set_ylim(0, 25); a1.set_ylabel("Temperature/°C")
    a1.legend(frameon=False, ncol=3, loc="lower left", fontsize=8, bbox_to_anchor=(0.05, 0.99), borderaxespad=0, handlelength=2.2, columnspacing=1.2); clean(a1); a1.tick_params(labelbottom=False)
    a1.set_title("(b)", **ttl)
    # (c) the bacteria
    ends = []
    LS = {"A": "-", "B": (0, (5, 2)), "C": (0, (6, 1.5, 1.5, 1.5))}
    for c, desc, b, tm, h0, l0, col in cart:
        y = baranyi_path(T, dt, b, tm, h0, l0)
        a2.plot(t, y, color=col, lw=1.9, ls=LS[c])
        a2.text(72.6, y[-1], f"Carton {c}", color=col, fontsize=8, fontweight="bold", va="center")
        ic = int(np.argmax(y >= lim)) if (y >= lim).any() else None
        ends.append((y[-1], None if ic is None else t[ic]))
        if ic is not None:
            a2.plot([t[ic]], [lim], "o", ms=5.5, color=col, mec="white", mew=.8, zorder=5)
            a2.annotate(f"Carton {c} passes the limit at {t[ic]:.0f} h", xy=(t[ic], lim), xytext=(30, 5.45), fontsize=8, color=col,
                        ha="center", arrowprops=dict(arrowstyle="-|>", color=col, lw=.7, mutation_scale=7))
    a2.axhline(lim, color=INK2, lw=.8, ls=(0, (4, 3)))
    a2.text(1, lim + .1, "spoilage limit: 3 × 10$^4$ CFU mL$^{-1}$", fontsize=8, color=INK2)
    for c, desc, *_, col in cart:
        pass
    a2.set_ylabel("log$_{10}$ count/CFU mL$^{-1}$"); a2.set_ylim(1, 6.2)
    clean(a2); a2.tick_params(labelbottom=False)
    a2.set_title("(c)", **ttl)
    # (d) the gauge the monitor computes
    K = K_of(3.8, 1.7); csl = np.cumsum(mu_of(T)) * dt / K
    a3.fill_between(t, 0, csl, color=BLUE, alpha=.08, lw=0)
    a3.plot(t, csl, color=BLUE, lw=1.9)
    a3.axhline(1, color=INK2, lw=.8, ls=(0, (4, 3))); a3.text(1, 1.03, "CSL = 1: shelf life consumed", fontsize=8, color=INK2)
    for j, (s0, s1, _, _) in enumerate(ev):
        i0, i1 = int(s0 / dt), min(int((s1 + 1.5) / dt), n - 1)
        a3.plot(t[i0:i1], csl[i0:i1], color=ORANGE, lw=3.2, alpha=.7, solid_capstyle="round")
        callout(a3, s0 - 2.2, csl[i0] + .17, j + 1, ORANGE)
    tc = t[np.argmax(csl >= 1)]
    a3.plot([tc], [1], "o", ms=5.5, color=BLUE, mec="white", mew=.8, zorder=5)
    a3.annotate(f"monitor: limit reached at {tc:.0f} h,\nidentical for all three cartons", xy=(tc, 1), xytext=(54, .22), fontsize=8,
                ha="center", arrowprops=dict(arrowstyle="-|>", color=INK2, lw=.7, mutation_scale=7))
    a3.text(10, .62, "warm spells (thick segments)\nconsume shelf life faster", fontsize=8, color=ORANGE, ha="left", va="bottom")
    a3.set_ylim(0, 1.2); a3.set_ylabel("Shelf life used"); a3.set_xlabel("Time since pasteurisation/h")
    clean(a3); a3.set_xlim(0, H)
    a3.set_title("(d)", **ttl)
    # (e) verdicts
    a4.set_xlim(0, 100); a4.set_ylim(0, 1); a4.axis("off")
    for i, ((c, desc, *_, col), (ye, tcross)) in enumerate(zip(cart, ends)):
        x0 = 0.5 + i * 21
        v = 10 ** ye; v = round(v, -3) if v > 1e4 else round(v, -2)
        fate = f"spoiled at {tcross:.0f} h" if tcross is not None else (f"close to the limit\n≈{v:,.0f} CFU mL$^{{-1}}$" if v > 1e4 else f"below the limit\n≈{v:,.0f} CFU mL$^{{-1}}$")
        a4.add_patch(FancyBboxPatch((x0, .0), 20, .98, boxstyle="round,pad=0,rounding_size=.08", fc="white", ec=col, lw=1.4, mutation_aspect=8))
        a4.text(x0 + 10, .74, f"Carton {c}", ha="center", fontsize=8, fontweight="bold", color=col)
        a4.text(x0 + 10, .32, fate, ha="center", va="center", linespacing=1.3, fontsize=8, color=INK)
    a4.text(64.5, .47, f"The monitor predicts {tc:.0f} h for all three.\nIt is late for C and early for A and B.\nThe error is biological: a more accurate\nsensor cannot remove it.",
            fontsize=8, va="center", color=INK)
    a4.set_title("(e)", **ttl)
    save(fig, "story.pdf")


# ---------------------------------------------------------------- Fig: the biological clock (Proposition 1, shown numerically)
def fig_system():
    fig, ax = plt.subplots(figsize=(W2, 3.6)); ax.set_xlim(0, 100); ax.set_ylim(-9, 62); ax.axis("off")
    ax.text(0, 60, "Example values under each block: 40 min after a truck door was left open.  Steps 2–5 run on the logger.", fontsize=8, color=INK2, style="italic", va="center")
    W, Hb = 28, 15
    blocks = [((0, 37), "1  Sense", "probe in the crate\n(DS18B20 or PT1000)", "#fdf1ea", ORANGE, "T = 13.2 °C"),
              ((36, 37), "2  Schedule", "every minute while changing,\nevery 15 min when steady", "#eef3fa", BLUE, "Δt = 1 min"),
              ((72, 37), "3  Look up", "rate of shelf-life use\n1/SL(T) from a stored table", "#eef3fa", BLUE, "1/SL = 0.039 h$^{-1}$"),
              ((72, 8), "4  Accumulate", "cumulative shelf life\nCSL ← CSL + Δt/SL", "#eef3fa", BLUE, "CSL = 0.71"),
              ((36, 8), "5  Propagate", "same sum for 80 sampled\nbiological parameter sets", "#eef3fa", BLUE, "P(spoiled) = 72 %"),
              ((0, 8), "6  Show", "risk band and alert,\nsent over Bluetooth", "#f4f4f4", INK2, "“inspect before use”")]
    for (x, y), ttl, body, fc, ec, val in blocks:
        ax.add_patch(FancyBboxPatch((x, y), W, Hb, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec, lw=.9))
        ax.text(x + W / 2, y + Hb - 3.2, ttl, ha="center", va="center", fontsize=8, fontweight="bold")
        ax.text(x + W / 2, y + 5.0, body, ha="center", va="center", fontsize=8, color=INK2, linespacing=1.2)
        ax.text(x + W / 2, y - 4.3, val, ha="center", va="center", fontsize=8, color=ec, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=ec, lw=.6))
    _arr(ax, 28.6, 44.5, 35.4, 44.5); _arr(ax, 64.6, 44.5, 71.4, 44.5)
    _arr(ax, 86, 36.4, 86, 31.2 - 6.5)
    _arr(ax, 71.4, 15.5, 64.6, 15.5); _arr(ax, 35.4, 15.5, 28.6, 15.5)
    ax.text(100, -6.5, "Done once, offline: fit b, T$_{\\min}$, lag and starting load to ComBase and published data;\nstore the table (step 3) and the 80 parameter sets (step 5) on the logger",
            fontsize=8, ha="right", va="center", color=GREEN, linespacing=1.2)
    save(fig, "system.pdf")



# ================================================================= model comparison and statistics figures


if __name__ == "__main__":
    fig_story(); fig_design(); fig_combase(); fig_lis(); fig_budget(); fig_runs(); fig_system()

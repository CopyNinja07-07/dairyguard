"""Animated GIFs for the README: a monitored trip, and the biological clock.

Writes docs/img/trip.gif and docs/img/clock.gif. Both are drawn from the package's own models."""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from dairyguard import ColdChainMonitor, mu_sqrt
from dairyguard.kinetics import LN10

IMG = os.path.join(ROOT, "docs", "img"); os.makedirs(IMG, exist_ok=True)
BG, PANEL, INK, MUT, LINE = "#E6EAED", "#F4F6F8", "#2B0A27", "#66525F", "#D3CBD3"
SIG, HOT, COLD, OK = "#D49B00", "#B3261E", "#5E7F99", "#2F7A52"
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "font.size": 10,
                     "text.color": INK, "axes.labelcolor": MUT, "xtick.color": MUT, "ytick.color": MUT,
                     "axes.edgecolor": LINE, "figure.facecolor": BG, "axes.facecolor": PANEL})


def baranyi(Tseries, b, tmin, h0, n0, nmax=9.0, dt=1 / 60):
    y, q = n0 * LN10, 1 / (np.exp(h0) - 1)
    out = np.empty(len(Tseries))
    for i, T in enumerate(Tseries):
        m = float(mu_sqrt(np.array(T), b, tmin)); a = q / (1 + q)
        y += dt * m * a * (1 - np.exp(y - nmax * LN10)); q += dt * m * q; out[i] = y / LN10
    return out


def frames_to_gif(figs, path, fps, hold=0):
    imgs = []
    for f in figs:
        f.canvas.draw(); imgs.append(np.asarray(f.canvas.buffer_rgba())[..., :3].copy()); plt.close(f)
    imgs += [imgs[-1]] * hold
    imageio.mimsave(path, imgs, duration=1 / fps, loop=0)


def trip_gif():
    H = 54; t = np.arange(0, H, 1 / 60)
    air = np.where((t > 18) & (t < 21), 17.5, 4.0)
    milk = np.empty_like(air); T = 4.0
    for i, a in enumerate(air):
        T += (a - T) * (1 - np.exp(-(1 / 60) / 1.0)); milk[i] = T
    rng = np.random.default_rng(7); K = 40
    bs = 0.030 * np.exp(rng.normal(0, .1, K)); tm = rng.normal(-7.7, 1.5, K)
    h0s = rng.uniform(2.5, 5, K); n0s = rng.uniform(1.5, 2.0, K)
    curves = np.array([baranyi(milk, *p) for p in zip(bs, tm, h0s, n0s)])
    lim = np.log10(3e4)
    mon = ColdChainMonitor("milk", n_draws=200, seed=1)
    stat = []
    for i in range(0, len(t), 15):
        stat.append(mon.update(milk[i], 0.25))
    figs = []
    for f in np.linspace(0.02, 1, 46):
        n = max(2, int(f * len(t)))
        fig = plt.figure(figsize=(8, 3.6), dpi=90)
        a1 = fig.add_axes([0.07, 0.58, 0.58, 0.32]); a2 = fig.add_axes([0.07, 0.13, 0.58, 0.38])
        a1.plot(t[:n], air[:n], color=HOT, lw=1, alpha=.8); a1.plot(t[:n], milk[:n], color=COLD, lw=2)
        a1.set_xlim(0, H); a1.set_ylim(0, 20); a1.set_xticks([]); a1.set_ylabel("°C")
        a1.text(25, 15, "the trip: air (red), milk (blue)", color=MUT, fontsize=9)
        for c in curves:
            over = c[n - 1] >= lim
            a2.plot(t[:n], c[:n], color=HOT if over else COLD, lw=.8, alpha=.5)
        a2.axhline(lim, color=HOT, ls="--", lw=1); a2.text(1, lim + .15, "FSSAI limit", color=HOT, fontsize=8)
        a2.set_xlim(0, H); a2.set_ylim(1, 7); a2.set_xlabel("hours"); a2.set_ylabel("log10 CFU/mL")
        a2.text(1, 6.3, "bacteria in 40 cartons with the same log", color=MUT, fontsize=9)
        for ax in (a1, a2):
            for s in ax.spines.values():
                s.set_color(LINE)
        s = stat[min(len(stat) - 1, n // 15)]
        col = OK if s.probability_crossed < .15 else SIG if s.probability_crossed < .75 else HOT
        fig.text(.70, .84, "DAIRYGUARD KINETIC", color=SIG, fontsize=9, fontweight="bold")
        fig.text(.70, .66, f"{s.probability_crossed * 100:.0f}%", color=col, fontsize=34, fontweight="bold")
        fig.text(.70, .58, "chance it crossed the limit", color=MUT, fontsize=9)
        fig.text(.70, .46, f"{s.shelf_life_used * 100:.0f}% of shelf life used", color=INK, fontsize=10)
        fig.text(.70, .38, f"{s.hours_left_at_4C:.0f} h left at 4 °C (typical)", color=INK, fontsize=10)
        fig.text(.70, .30, f"{s.hours_left_at_4C_cautious:.0f} h left at 4 °C (cautious)", color=MUT, fontsize=10)
        fig.text(.70, .20, s.state.upper(), color=col, fontsize=13, fontweight="bold")
        figs.append(fig)
    frames_to_gif(figs, os.path.join(IMG, "trip.gif"), fps=9, hold=14)


def clock_gif():
    P = dict(b=.030, tmin=-7.7, h0=3.8, n0=1.7)
    t = np.arange(0, 240, .1)
    curves = {T: baranyi(np.full(len(t), T), P["b"], P["tmin"], P["h0"], P["n0"], dt=.1) for T in (4, 8, 12)}
    mu = lambda T: (P["b"] * (T - P["tmin"])) ** 2
    cols = {4: COLD, 8: SIG, 12: HOT}
    ks = np.concatenate([np.zeros(8), (1 - np.cos(np.linspace(0, np.pi, 26))) / 2, np.ones(12),
                         (1 + np.cos(np.linspace(0, np.pi, 26))) / 2])
    figs = []
    for k in ks:
        fig, ax = plt.subplots(figsize=(8, 3.4), dpi=90); fig.subplots_adjust(left=.08, right=.97, bottom=.17, top=.86)
        for T, c in curves.items():
            f = 1 + k * (mu(T) / mu(4) - 1)
            m = t * f <= 240
            ax.plot(t[m] * f, c[m], color=cols[T], lw=2.4, label=f"{T} °C")
        ax.axhline(np.log10(3e4), color=HOT, ls="--", lw=1, alpha=.7)
        ax.set_xlim(0, 240); ax.set_ylim(1, 9.5); ax.set_ylabel("log10 CFU/mL")
        ax.set_xlabel("biological hours (equivalent hours at 4 °C)" if k > .5 else "ordinary hours")
        ax.legend(frameon=False, loc="lower right", labelcolor=INK)
        fig.text(.08, .92, "Bacteria keep their own clock: switch to it and three temperatures become one curve",
                 color=INK, fontsize=10.5, fontweight="bold")
        for s in ax.spines.values():
            s.set_color(LINE)
        figs.append(fig)
    frames_to_gif(figs, os.path.join(IMG, "clock.gif"), fps=12)


if __name__ == "__main__":
    trip_gif()
    clock_gif()
    print({f: os.path.getsize(os.path.join(IMG, f)) // 1024 for f in ("trip.gif", "clock.gif")}, "kB")

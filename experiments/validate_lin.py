"""Reproduce Lin et al. 2016 (J Dairy Sci 99:1822) with the project kernel.
Fit: Ratkowsky b, T0 from Lin's Table 2 growth rates at 4/15/29 C (log10 basis -> ln basis); h0 from lag*mu (4 C).
Out-of-sample check: Lin report ~90 h to 1e6 at constant 4 C and 55 h after two 4-h excursions to 29 C
(first at 24 h, second 24 h after the first ended). Initial population 2.9 log CFU/mL (Lin Table 2, 4 C)."""
import math, json, sys
import numpy as np
LN10 = math.log(10)
T = np.array([4., 15., 29.]); mu10 = np.array([0.056, 0.17, 0.46]); lag = np.array([29.5, 12.7, 2.8])
mu_ln = mu10 * LN10
slope, icpt = np.polyfit(T, np.sqrt(mu_ln), 1)
b, T0 = slope, -icpt / slope
h0 = float(np.mean(lag * mu_ln))                  # Baranyi: lag*mu = ln(1+1/q0) is constant
h0_4 = float(lag[0] * mu_ln[0])
def run(profile, b, Tmin, h0, l0=2.9, lmax=9.0, dt=1 / 60):
    y = l0 * LN10; ym = lmax * LN10; q = 1 / (math.exp(h0) - 1); out = np.empty(len(profile))
    for k, Tk in enumerate(profile):
        mu = (b * (Tk - Tmin)) ** 2 if Tk > Tmin else 0.0
        a = q / (1 + q); y += dt * mu * a * (1 - math.exp(y - ym)); q += dt * mu * q; out[k] = y / LN10
    return out
def t_hit(g, level=6.0):
    i = np.argmax(g >= level); return float(i / 60) if g.max() >= level else float("nan")
H = 160 * 60
const = np.full(H, 4.0); fl = const.copy()
for s in (24, 52): fl[s * 60:(s + 4) * 60] = 29.0
res = {"b_ln": round(b, 4), "T0_C": round(T0, 2), "h0_mean": round(h0, 2), "h0_at_4C": round(h0_4, 2)}
for nm, h in (("h0_mean", h0), ("h0_at_4C", h0_4)):
    res[nm + "_const_h"] = round(t_hit(run(const, b, T0, h)), 1)
    res[nm + "_two_excursions_h"] = round(t_hit(run(fl, b, T0, h)), 1)
res["lin_reported_const_h"] = 90; res["lin_reported_two_excursions_h"] = 55
if __name__ == "__main__":
    print(json.dumps(res, indent=1))
    json.dump(res, open("results/validation_lin.json", "w"), indent=1)

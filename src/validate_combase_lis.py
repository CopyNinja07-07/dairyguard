"""Fit the square-root model to ComBase records of Listeria monocytogenes in milk, and test it on held-out records.
Fit set: records with conditions 'Not specified' and 2-16 C. Held-out: the other Listeria records with a stated rate
(sterilised or previously heated milk, added salt or acids, other conditions), temperature 2-16 C.
Records come from the ComBase milk search."""
import math, json
import numpy as np, pandas as pd
d = pd.read_csv("data/combase_milk_full.csv")
d = d[d.organism.fillna("").str.startswith("Listeria") & d.max_rate_log10_per_h.notna()].copy()
d["T"] = pd.to_numeric(d.temp_C, errors="coerce"); d = d[d["T"].between(2, 16)]
clean = d.conditions.fillna("").str.contains("Not specified")
fit_set, held = d[clean], d[~clean]
y = np.sqrt(fit_set.max_rate_log10_per_h * math.log(10)); b, i = np.polyfit(fit_set["T"], y, 1); Tmin = -i / b
def pred(t): return ((b * (t["T"] - Tmin)) ** 2) / math.log(10)
def factors(t):
    r = np.log10(pred(t) / t.max_rate_log10_per_h); return round(float(10 ** r.mean()), 2), round(float(10 ** np.abs(r).mean()), 2)
# bootstrap CI for b and Tmin
rng = np.random.default_rng(1); bs = []
for _ in range(2000):
    s = fit_set.sample(len(fit_set), replace=True, random_state=int(rng.integers(1e9)))
    bb, ii = np.polyfit(s["T"], np.sqrt(s.max_rate_log10_per_h * math.log(10)), 1); bs.append((bb, -ii / bb))
bs = np.array(bs)
resid = np.log(fit_set.max_rate_log10_per_h / pred(fit_set))
out = dict(n_fit=len(fit_set), n_heldout=len(held), b_ln=round(b, 4), Tmin_C=round(Tmin, 2),
           b_ci95=[round(float(np.percentile(bs[:, 0], 2.5)), 4), round(float(np.percentile(bs[:, 0], 97.5)), 4)],
           Tmin_ci95=[round(float(np.percentile(bs[:, 1], 2.5)), 2), round(float(np.percentile(bs[:, 1], 97.5)), 2)],
           resid_log_sd=round(float(resid.std()), 3), fit_bias_accuracy=factors(fit_set), heldout_bias_accuracy=factors(held) if len(held) else None,
           rate_at_4C_log10_per_h=round(float(pred(pd.DataFrame({"T": [4.0]})).iloc[0]), 4),
           generation_time_4C_h=round(math.log10(2) / float(pred(pd.DataFrame({"T": [4.0]})).iloc[0]), 1),
           rate_ratio_13C_vs_4C=round(float(pred(pd.DataFrame({"T": [13.0]})).iloc[0] / pred(pd.DataFrame({"T": [4.0]})).iloc[0]), 2))
if __name__ == "__main__":
    print(json.dumps(out, indent=1)); json.dump(out, open("results/validation_lis.json", "w"), indent=1)

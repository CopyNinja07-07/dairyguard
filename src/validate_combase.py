"""Fit the square-root model to ComBase records (aerobic spoilage flora, pasteurised milk, Tasmanian Institute of Agriculture)
and score the Neumeyer/Lin-anchored model against them (bias and accuracy factors, Ross 1996).
Data were transcribed by OCR from a screen recording of the ComBase search results; record 21 (temperature misread as 74.0) is excluded
and record 18 (rate 0.0242 at 6.8 C, an outlier) is kept in the 'all' fit and dropped in the 'robust' fit."""
import math, json
import numpy as np, pandas as pd
d = pd.read_csv("data/combase_tasmania_pasteurised_milk.csv")
d = d[d.temp_C < 30]
def fit(t):
    s, i = np.polyfit(t.temp_C, np.sqrt(t.max_rate_log10_per_h * math.log(10)), 1); return s, -i / s
out = {"n_all": len(d)}
for lab, t in (("all", d), ("robust", d[d.result_list_position != 18])):
    b, T0 = fit(t); pred = ((b * (t.temp_C - T0)) ** 2) / math.log(10); r = np.log(t.max_rate_log10_per_h / pred)
    out[lab] = dict(n=len(t), b_ln=round(b, 4), Tmin_C=round(T0, 2), resid_log_sd=round(float(r.std()), 3))
for nm, b, T0 in (("neumeyer", 0.030, -7.7), ("lin", 0.0273, -9.15)):
    pred = ((b * (d.temp_C - T0)) ** 2) / math.log(10); r = np.log10(pred / d.max_rate_log10_per_h)
    out[nm] = dict(bias_factor=round(float(10 ** r.mean()), 2), accuracy_factor=round(float(10 ** np.abs(r).mean()), 2))
if __name__ == "__main__":
    print(json.dumps(out, indent=1)); json.dump(out, open("results/validation_combase.json", "w"), indent=1)

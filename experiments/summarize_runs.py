"""Condense every benchmark run into the headline numbers quoted in the paper, book and web page.
Usage: python3 experiments/summarize_runs.py   (writes results/summary.json)"""
import json, os
import pandas as pd
RUNS = {"base": ("results/base", "Baseline (sourced biology)"), "lag": ("results/lag", "Extra lag after temperature shifts"),
        "low": ("results/low", "Low starting load"), "comb": ("results/comb", "Fitted to milk spoilage flora (ComBase)"),
        "lis": ("results/lis", "Listeria monocytogenes (hazard case study)")}
CON = {"gain_vs_degree_hours": "CSL - degree_hours_4C", "gain_vs_time_above_5C": "CSL - time_above_5C", "gain_vs_maxT": "CSL - max_temperature",
       "biology_gap": "biology gap: oracle - ideal(1min,CSL)", "sensor_PT1000_vs_DS18B20": "sensor: PT1000 - DS18B20 (CSL,15min)",
       "sampling_60_vs_1": "sampling: 60min - 1min (DS18B20,CSL)", "sampling_15_vs_1": "sampling: 15min - 1min (DS18B20,CSL)", "adaptive_vs_1min": "adaptive - fixed1min (DS18B20,CSL)"}
out = {}
for k, (d, name) in RUNS.items():
    if not os.path.exists(f"{d}/calibration.csv"): continue
    p = pd.read_csv(f"{d}/paired_contrasts.csv"); c = pd.read_csv(f"{d}/calibration.csv")
    o = {"dir": d, "name": name, "horizons_h": sorted(int(x) for x in p.horizon_h.unique()), "settings": int(len(p[p.contrast == CON["biology_gap"]]))}
    for key, cn in CON.items():
        x = p[p.contrast == cn]
        o[key] = {"min": round(float(x["diff"].min()), 4), "max": round(float(x["diff"].max()), 4), "median": round(float(x["diff"].median()), 4),
                  "n": int(len(x)), "n_excl_zero": int(x.excludes_zero.sum()), "n_pos_excl_zero": int(((x["diff"] > 0) & x.excludes_zero).sum())}
    for var, key in (("MC matched prior", "ece_matched"), ("MC overconfident", "ece_overconf"), ("point alarm", "ece_point")):
        x = c[c.variant.str.startswith(var)]; o[key] = {"min": round(float(x.ECE.min()), 3), "max": round(float(x.ECE.max()), 3)}
    a = pd.read_csv(f"{d}/auc_results.csv"); a["sampling"] = a["sampling"].astype(str)
    sel = a[(a.method == "CSL") & (a.sensor == "ideal") & (a.sampling == "1")]; o["auc_csl_ideal_1min"] = {"min": round(float(sel.AUC.min()), 3), "max": round(float(sel.AUC.max()), 3)}
    sel = a[(a.method == "CSL_oracle")]; o["auc_oracle"] = {"min": round(float(sel.AUC.min()), 3), "max": round(float(sel.AUC.max()), 3)}
    out[k] = o
os.makedirs("results", exist_ok=True); json.dump(out, open("results/summary.json", "w"), indent=1)
print(json.dumps({k: {kk: v[kk] for kk in ("horizons_h", "biology_gap", "gain_vs_degree_hours")} for k, v in out.items()}, indent=0))

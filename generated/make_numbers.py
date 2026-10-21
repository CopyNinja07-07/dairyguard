"""Writes generated/numbers.tex: LaTeX macros for every number quoted in the technical report, read from results/summary.json and the validation JSON files."""
import json, os
S = json.load(open("results/summary.json"))
V = {k: json.load(open(f"results/validation_{k}.json")) for k in ("lin", "combase", "lis")}
names = {"base": "Base", "lag": "Lag", "low": "Low", "comb": "Comb", "lis": "Lis"}
L = []
def mac(n, v): L.append("\\newcommand{\\%s}{%s}" % (n, v))
for k, nm in names.items():
    o = S.get(k)
    for key, tag in (("biology_gap", "Gap"), ("gain_vs_degree_hours", "Gain"), ("sensor_PT1000_vs_DS18B20", "Sens"), ("sampling_60_vs_1", "Samp")):
        for st in ("min", "max"):
            mac(f"Num{nm}{tag}{st.capitalize()}", ("%.2f" % o[key][st]) if o else "--")
    if o:
        mac(f"Num{nm}GainSig", f"{o['gain_vs_degree_hours']['n_pos_excl_zero']}")
        mac(f"Num{nm}SampNull", f"{o['sampling_60_vs_1']['n'] - o['sampling_60_vs_1']['n_excl_zero']}")
        mac(f"Num{nm}HzA", f"{o['horizons_h'][0]}"); mac(f"Num{nm}HzB", f"{o['horizons_h'][1]}")
        mac(f"Num{nm}FiveSig", f"{o['gain_vs_time_above_5C']['n_pos_excl_zero']}"); mac(f"Num{nm}MaxSig", f"{o['gain_vs_maxT']['n_pos_excl_zero']}")
        for key, tag in (("ece_matched", "EceM"), ("ece_overconf", "EceO"), ("ece_point", "EceP")):
            mac(f"Num{nm}{tag}Min", "%.2f" % o[key]["min"]); mac(f"Num{nm}{tag}Max", "%.2f" % o[key]["max"])
l = V["lin"]; c = V["combase"]; s = V["lis"]
mac("NumLinConst", "%.0f" % l["h0_at_4C_const_h"]); mac("NumLinExc", "%.0f" % l["h0_at_4C_two_excursions_h"])
mac("NumLinErr", "%.0f" % (100 * (l["h0_at_4C_two_excursions_h"] - 55) / 55))
mac("NumLinErrAbs", "%.0f" % abs(100 * (l["h0_at_4C_two_excursions_h"] - 55) / 55))
mac("NumCbN", c["n_all"]); mac("NumCbNfit", c["robust"]["n"]); mac("NumCbAllB", "%.4f" % c["all"]["b_ln"]); mac("NumCbAllT", "%.1f" % c["all"]["Tmin_C"]); mac("NumCbB", "%.4f" % c["robust"]["b_ln"]); mac("NumCbT", "%.1f" % c["robust"]["Tmin_C"]); mac("NumCbSd", "%.2f" % c["robust"]["resid_log_sd"])
mac("NumCbBias", "%.2f" % c["neumeyer"]["bias_factor"])
mac("NumLisN", s["n_fit"]); mac("NumLisHeld", s["n_heldout"]); mac("NumLisB", "%.4f" % s["b_ln"]); mac("NumLisT", "%.1f" % s["Tmin_C"])
mac("NumLisBLo", "%.4f" % s["b_ci95"][0]); mac("NumLisBHi", "%.4f" % s["b_ci95"][1]); mac("NumLisTLo", "%.1f" % s["Tmin_ci95"][0]); mac("NumLisTHi", "%.1f" % s["Tmin_ci95"][1])
mac("NumLisBiasHeld", "%.2f" % s["heldout_bias_accuracy"][0]); mac("NumLisAccHeld", "%.2f" % s["heldout_bias_accuracy"][1]); mac("NumLisAccFit", "%.2f" % s["fit_bias_accuracy"][1])
mac("NumLisGen", "%.0f" % s["generation_time_4C_h"]); mac("NumLisRatio", "%.1f" % s["rate_ratio_13C_vs_4C"]); mac("NumLisSd", "%.2f" % s["resid_log_sd"])
import pandas as pd
a = pd.read_csv("results/lis/auc_results.csv"); o = a[a.method == "CSL_oracle"]
for thr, tag in (("A_3e4", "A"), ("B_1e6", "B")):
    x = o[o.thr == thr].AUC; mac(f"NumLisOrc{tag}Min", "%.2f" % x.min()); mac(f"NumLisOrc{tag}Max", "%.2f" % x.max())
cc = pd.read_csv("results/lis/calibration.csv")
for thr, tag in (("A_3e4", "A"), ("B_1e6", "B")):
    for v, vt in (("MC matched", "M"), ("point", "P")):
        x = cc[(cc.thr == thr) & cc.variant.str.startswith(v)].ECE; mac(f"NumLisEce{tag}{vt}Min", "%.2f" % x.min()); mac(f"NumLisEce{tag}{vt}Max", "%.2f" % x.max())
pv = a.prevalence; mac("NumLisPrevMin", "%.2f" % pv.min()); mac("NumLisPrevMax", "%.2f" % pv.max())
open("generated/numbers.tex", "w").write("\n".join(L) + "\n"); print(len(L), "macros")

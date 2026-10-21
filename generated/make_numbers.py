"""Writes generated/numbers.tex: LaTeX macros for every number quoted in the book and the white paper, read from results/summary.json and the validation JSON files."""
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
# ---------------------------------------------------------------- growth-law study and monitor studies
if os.path.exists("results/growth_laws/cv_scores.csv"):
    g = pd.read_csv("results/growth_laws/cv_scores.csv")
    tags = {"square-root": "Sqrt", "Arrhenius": "Arr", "Q10": "Qten", "Davey": "Davey", "neural": "Net"}
    for data, dt in (("Listeria", "Lis"), ("Spoilage", "Sp")):
        sub = g[g.data.str.startswith(data)]
        for law, lt in tags.items():
            r = sub[sub.law == law].iloc[0]
            mac(f"Gl{dt}{lt}Af", "%.2f" % r.Af); mac(f"Gl{dt}{lt}Bf", "%.2f" % r.Bf)
        mac(f"Gl{dt}N", int(sub.n.iloc[0])); mac(f"Gl{dt}Groups", int(sub.groups.iloc[0]))
    v = json.load(open("results/growth_laws/variation.json"))
    mac("GlCvB", "%.2f" % v["cv_b"]); mac("GlCvStudies", v["n_studies"]); mac("GlCvRecords", v["n_records"])
    mac("GlCvWithin", "%.2f" % v["within_study_rmse_ln"])
if os.path.exists("results/monitor_studies.json"):
    m = json.load(open("results/monitor_studies.json"))
    tb = m["trained_baseline"]
    for tau, tt in (("low_mass", "Pouch"), ("insulated", "Crate")):
        for k, kt in (("logistic regression (trained)", "Lr"), ("DairyGuard probability", "Dg"), ("single alarm", "Al")):
            mac(f"Ms{tt}{kt}Auc", "%.3f" % tb[tau][k]["AUC"]); mac(f"Ms{tt}{kt}Ece", "%.3f" % tb[tau][k]["ECE"])
    mc = m["mc_convergence"]
    for K in ("10", "20", "40", "80", "160", "320"):
        mac("MsMcEce" + {"10": "Ten", "20": "Twenty", "40": "Forty", "80": "Eighty", "160": "OneSixty", "320": "ThreeTwenty"}[K], "%.3f" % mc[K]["ECE"])
    cb = m["correlated_biology"]
    mac("MsCorNeg", "%.2f" % cb["-0.6"]["loss_to_biology"]); mac("MsCorZero", "%.2f" % cb["0.0"]["loss_to_biology"]); mac("MsCorPos", "%.2f" % cb["0.6"]["loss_to_biology"])
    h = m["hours_left"]
    mac("MsHlTrips", h["trips"]); mac("MsHlCautious", "%.1f" % (100 * h["cautious_was_safe"])); mac("MsHlTypical", "%.0f" % (100 * h["typical_was_safe"]))
    mac("MsHlErr", "%.0f" % h["median_abs_error_typical_h"]); mac("MsHlTrue", "%.0f" % h["median_true_hours_left"]); mac("MsHlRho", "%.2f" % h["spearman"])
open("generated/numbers.tex", "w").write("\n".join(L) + "\n"); print(len(L), "macros")

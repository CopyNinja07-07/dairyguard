"""Compare temperature (secondary) models on the ComBase milk records.

Models for the maximum specific growth rate mu (h-1, natural-log basis):
  sqrt      : sqrt(mu) = b (T - Tmin)                       (Ratkowsky et al. 1982), 2 parameters
  arrhenius : ln mu = ln A - Ea / (R T_K)                   (Arrhenius), 2 parameters
  q10       : ln mu = a + c T   (constant Q10 = exp(10 c))  2 parameters
  davey     : ln mu = C0 + C1 / T_K + C2 / T_K^2            (Arrhenius-Davey), 3 parameters
Checks: fit quality (RMSE of ln mu, AICc), bias and accuracy factors (Ross 1996),
leave-one-temperature-out cross-validation, cold extrapolation (fit on T >= 8 C, predict T < 8 C),
and, for Listeria monocytogenes, prediction of records held out by condition.
Run from the repository root: python src/compare_secondary.py  ->  results/secondary_models.json, .csv
"""
import json
import math
import numpy as np
import pandas as pd

R = 8.314
MODELS = ("sqrt", "arrhenius", "q10", "davey")
NPAR = {"sqrt": 2, "arrhenius": 2, "q10": 2, "davey": 3}


def fit(model, T, mu):
    T = np.asarray(T, float); mu = np.asarray(mu, float); TK = T + 273.15
    if model == "sqrt":
        b, a = np.polyfit(T, np.sqrt(mu), 1)
        return {"b": b, "Tmin": -a / b}
    if model == "arrhenius":
        c1, c0 = np.polyfit(1 / TK, np.log(mu), 1)
        return {"lnA": c0, "Ea_kJ": -c1 * R / 1000}
    if model == "q10":
        c, a = np.polyfit(T, np.log(mu), 1)
        return {"a": a, "c": c, "Q10": math.exp(10 * c)}
    if model == "davey":
        X = np.column_stack([np.ones_like(TK), 1 / TK, 1 / TK ** 2])
        C, *_ = np.linalg.lstsq(X, np.log(mu), rcond=None)
        return {"C0": C[0], "C1": C[1], "C2": C[2]}


def predict(model, p, T):
    T = np.asarray(T, float); TK = T + 273.15
    if model == "sqrt":
        return np.where(T > p["Tmin"], (p["b"] * (T - p["Tmin"])) ** 2, 1e-9)
    if model == "arrhenius":
        return np.exp(p["lnA"] - p["Ea_kJ"] * 1000 / (R * TK))
    if model == "q10":
        return np.exp(p["a"] + p["c"] * T)
    if model == "davey":
        return np.exp(p["C0"] + p["C1"] / TK + p["C2"] / TK ** 2)


def factors(pred, obs):
    r = np.log10(pred / obs)
    return float(10 ** r.mean()), float(10 ** np.abs(r).mean())


def evaluate(model, T, mu):
    p = fit(model, T, mu)
    res = np.log(predict(model, p, T)) - np.log(mu)
    n, k = len(mu), NPAR[model]
    rss = float((res ** 2).sum())
    aicc = n * math.log(rss / n) + 2 * k + 2 * k * (k + 1) / (n - k - 1)
    bf, af = factors(predict(model, p, T), mu)
    # leave-one-temperature-out
    cv = []
    for t in np.unique(T):
        m = T != t
        q = fit(model, T[m], mu[m])
        cv.append(np.log(predict(model, q, T[~m])) - np.log(mu[~m]))
    cv = np.concatenate(cv)
    # cold extrapolation
    warm, cold = T >= 8, T < 8
    ext = None
    if warm.sum() >= 5 and cold.sum() >= 3:
        q = fit(model, T[warm], mu[warm])
        eb, ea = factors(predict(model, q, T[cold]), mu[cold])
        ext = {"n_cold": int(cold.sum()), "Bf": eb, "Af": ea}
    return {"params": {k_: float(v) for k_, v in p.items()}, "rmse_ln": math.sqrt(rss / n), "AICc": aicc,
            "Bf": bf, "Af": af, "cv_rmse_ln": float(np.sqrt((cv ** 2).mean())), "cold_extrapolation": ext}


def main():
    sp = pd.read_csv("data/combase_tasmania_pasteurised_milk.csv")
    full = pd.read_csv("data/combase_milk_records.csv")
    full = full[full.rate_status == "stated"].copy()
    full["T"] = pd.to_numeric(full.temp_C, errors="coerce")
    plain = full.conditions.fillna("").str.contains("Not specified")
    lis = full[full.organism.str.startswith("Listeria") & full["T"].between(2, 16)]
    lplain = lis.conditions.fillna("").str.contains("Not specified")
    sets = {
        "Spoilage flora (pasteurised milk)": (sp.temp_C.values, sp.max_rate_log10_per_h.values * math.log(10)),
        "L. monocytogenes (fitting set)": (lis[lplain]["T"].values, lis[lplain].max_rate_log10_per_h.values * math.log(10)),
        "B. cereus": (full[full.organism.str.startswith("Bacillus") & plain]["T"].values,
                      full[full.organism.str.startswith("Bacillus") & plain].max_rate_log10_per_h.values * math.log(10)),
        "E. coli": (full[full.organism.str.startswith("Escherichia") & plain]["T"].values,
                    full[full.organism.str.startswith("Escherichia") & plain].max_rate_log10_per_h.values * math.log(10)),
    }
    out, rows = {}, []
    for name, (T, mu) in sets.items():
        T, mu = np.asarray(T, float), np.asarray(mu, float)
        ok = np.isfinite(T) & np.isfinite(mu) & (mu > 0)
        T, mu = T[ok], mu[ok]
        if len(np.unique(T)) < 4:
            print("skipped (fewer than 4 temperatures):", name, len(T), sorted(set(T)))
            continue
        out[name] = {"n": int(len(T)), "T_range": [float(T.min()), float(T.max())], "n_temperatures": int(len(np.unique(T)))}
        for m in MODELS:
            e = evaluate(m, T, mu)
            out[name][m] = e
            rows.append(dict(dataset=name, n=len(T), model=m, rmse_ln=e["rmse_ln"], AICc=e["AICc"], Bf=e["Bf"], Af=e["Af"],
                             cv_rmse_ln=e["cv_rmse_ln"],
                             cold_Af=(e["cold_extrapolation"] or {}).get("Af"), cold_Bf=(e["cold_extrapolation"] or {}).get("Bf")))
    # Listeria held-out by condition
    Tf, muf = lis[lplain]["T"].values, lis[lplain].max_rate_log10_per_h.values * math.log(10)
    Th, muh = lis[~lplain]["T"].values, lis[~lplain].max_rate_log10_per_h.values * math.log(10)
    out["L. monocytogenes held-out"] = {}
    for m in MODELS:
        p = fit(m, Tf, muf)
        bf, af = factors(predict(m, p, Th), muh)
        out["L. monocytogenes held-out"][m] = {"n": int(len(Th)), "Bf": bf, "Af": af}
        rows.append(dict(dataset="L. monocytogenes held-out", n=len(Th), model=m, Bf=bf, Af=af))
    json.dump(out, open("results/secondary_models.json", "w"), indent=1)
    pd.DataFrame(rows).to_csv("results/secondary_models.csv", index=False)
    print(pd.DataFrame(rows).round(3).to_string())


if __name__ == "__main__":
    main()

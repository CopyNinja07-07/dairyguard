"""Which temperature law predicts growth best on real data it has not seen, and how much do real studies differ?

Data
  Listeria monocytogenes/innocua in milk: ComBase records with a stated maximum growth rate, 0-15 deg C, from many
  independent studies. Studies are the natural unit of independence, so every law is tested leave-one-study-out:
  fitted on all other studies, scored on the one left out.
  Natural spoilage flora in pasteurised milk (Tasmanian Institute of Agriculture records): one source, so it is
  tested by 5-fold cross-validation over records instead.

Laws compared: square-root, Arrhenius, Q10 (exponential), Davey, and a monotone neural network (ensemble of 5).

Writes
  results/growth_laws/cv_scores.csv          held-out bias factor, accuracy factor and RMSE per law and data set
  results/growth_laws/heldout_predictions.csv  every held-out prediction
  results/growth_laws/variation.json         between-study spread of the square-root slope b (real-data cv_b)
  results/growth_laws/neural_curve.csv       the neural law and its ensemble spread across temperature
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from dairyguard import growthlaws as G

OUT = "results/growth_laws"
LAWS = {"square-root": lambda: G.SquareRoot(), "Arrhenius": lambda: G.Arrhenius(), "Q10": lambda: G.Exponential(),
        "Davey": lambda: G.Davey(), "neural": lambda: G.MonotoneNet(units=4, ensemble=5, seed=1)}


def short_source(s):
    s = str(s)
    return s.split(":")[0][:60]


def load():
    d = pd.read_csv("data/combase_milk_records.csv")
    d = d[(d.rate_status == "stated")].copy()
    d["T"] = pd.to_numeric(d.temp_C, errors="coerce")
    d["mu"] = G.to_ln_rate(pd.to_numeric(d.max_rate_log10_per_h, errors="coerce"))
    lis = d[d.organism.str.startswith("Listeria") & d["T"].between(0, 15) & (d.mu > 0)].copy()
    lis["study"] = lis.source.map(short_source)
    sp = pd.read_csv("data/combase_tasmania_pasteurised_milk.csv")
    sp = sp[sp.temp_C < 30].copy()
    sp["T"], sp["mu"] = sp.temp_C, G.to_ln_rate(sp.max_rate_log10_per_h)
    rng = np.random.default_rng(0)
    sp["study"] = rng.permutation(np.arange(len(sp)) % 5)          # 5 folds within the single source
    return {"Listeria (leave one study out)": lis, "Spoilage flora (5-fold)": sp}


def main():
    os.makedirs(OUT, exist_ok=True)
    rows, preds = [], []
    for name, df in load().items():
        T, mu, g = df["T"].to_numpy(), df["mu"].to_numpy(), df["study"].astype(str).to_numpy()
        for law, make in LAWS.items():
            p = G.leave_one_group_out(make, T, mu, g)
            perf = G.performance(p, mu)
            full = make().fit(T, mu)
            rows.append(dict(data=name, law=law, n=len(T), groups=len(np.unique(g)), **perf,
                             AICc_full=G.aicc(full, T, mu) if law != "neural" else np.nan))
            preds += [dict(data=name, law=law, study=gg, T=t, mu_obs=m, mu_pred=pp) for gg, t, m, pp in zip(g, T, mu, p)]
            print(f"{name:32s} {law:12s} Af={perf['Af']:.3f} Bf={perf['Bf']:.3f} rmse={perf['rmse_ln']:.3f}", flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/cv_scores.csv", index=False)
    pd.DataFrame(preds).to_csv(f"{OUT}/heldout_predictions.csv", index=False)

    lis = load()["Listeria (leave one study out)"]
    var = G.between_study_variation(lis["T"].to_numpy(), lis["mu"].to_numpy(), lis["study"].to_numpy(), min_records=3)
    json.dump(var, open(f"{OUT}/variation.json", "w"), indent=1)
    print(f"between-study cv of b: {var['cv_b']:.3f} over {var['n_studies']} studies ({var['n_records']} records)")

    net = G.MonotoneNet(units=4, ensemble=5, seed=1).fit(lis["T"].to_numpy(), lis["mu"].to_numpy())
    sq = G.SquareRoot().fit(lis["T"].to_numpy(), lis["mu"].to_numpy())
    grid = np.linspace(0, 15, 61)
    pd.DataFrame(dict(T=grid, mu_neural=net.predict(grid), sd_ln_neural=net.spread(grid),
                      mu_sqrt=sq.predict(grid))).to_csv(f"{OUT}/neural_curve.csv", index=False)


if __name__ == "__main__":
    main()

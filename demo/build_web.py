import json, os, pandas as pd
RUNS = [("base", "../results/base"), ("lag", "../results/lag"), ("low", "../results/low"), ("comb", "../results/comb"), ("lis", "../results/lis")]
auc, pr, cr = [], [], []
for v, d in RUNS:
    if not os.path.exists(f"{d}/calibration.csv"): continue
    a = pd.read_csv(f"{d}/auc_results.csv"); a["sampling"] = a["sampling"].astype(str)
    p = pd.read_csv(f"{d}/paired_contrasts.csv"); c = pd.read_csv(f"{d}/calibration.csv")
    A = a[((a.sensor == "DS18B20") & (a.sampling == "15")) | (a.sensor == "oracle") | ((a.sensor.isin(["PT1000", "ideal"])) & (a.sampling.isin(["15", "1"])) & (a.method == "CSL"))]
    auc += [[v, r.thr, r.tau, r.cv, r.sensor, r.sampling, r.method, round(r.AUC, 4), round(r.lo, 4), round(r.hi, 4)] for r in A.itertuples()]
    pr += [[v, r.thr, r.tau, r.cv, r.contrast, round(r.diff, 4), round(r.lo, 4), round(r.hi, 4), int(r.horizon_h)] for r in p.itertuples()]
    cr += [[v, r.thr, r.tau, r.cv, r.variant, round(r.brier, 4), round(r.ECE, 4)] for r in c.itertuples()]
lin = json.load(open("../results/validation_lin.json")); lis = json.load(open("../results/validation_lis.json"))
data = json.dumps({"auc": auc, "paired": pr, "cal": cr, "lin": lin, "lis": lis, "variants": sorted({r[0] for r in auc})}, separators=(",", ":"))
kern = open("kernel.js").read().replace("if (typeof module", "if (false && typeof module")
html = open("template.html").read().replace("/*KERNEL*/", kern).replace("/*DATA*/", data)
open("../docs/explorer.html", "w").write(html); print(len(html), sorted({r[0] for r in auc}))

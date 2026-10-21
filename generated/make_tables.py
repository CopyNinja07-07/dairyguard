"""Write LaTeX tables and analytic numbers for the manuscript from the result files and the data.
Run from the repository root: python generated/make_tables.py  ->  generated/tables.tex, generated/datatables.tex"""
import os
import math
import json
import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
R = lambda *p: os.path.join(ROOT, *p)
RUNS = [("base", "Baseline"), ("lag", "Extra lag"), ("low", "Low load"), ("comb", "Milk flora"), ("lis", r"\textit{Listeria}")]
out = []
mac = lambda k, v: out.append("\\newcommand{\\%s}{%s}" % (k, v))


def load(run):
    a = pd.read_csv(R("results", run, "auc_results.csv")); a["sampling"] = a["sampling"].astype(str)
    return a, pd.read_csv(R("results", run, "paired_contrasts.csv")), pd.read_csv(R("results", run, "calibration.csv"))


# ---------------------------------------------------------------- Table: AUC by score, baseline run
a, p, c = load("base")
rows = []
METH = ["CSL", "deg_hours_4C", "t_above_5C", "t_above_8C", "maxT"]
for thr, tl in [("A_3e4", "A"), ("B_1e6", "B")]:
    for tau, taul in [("low_mass", "Pouch"), ("insulated", "Crate")]:
        for cv in [0.0, 0.1, 0.25]:
            sel = a[(a.thr == thr) & (a.tau == tau) & (a.cv == cv)]
            g = lambda s, m, me: sel[(sel.sensor == s) & (sel.sampling == m) & (sel.method == me)].AUC.iloc[0]
            vals = [g("DS18B20", "15", m) for m in METH]
            best = max(vals)
            cells = [("\\textbf{%.3f}" % v) if v == best else "%.3f" % v for v in vals]
            rows.append(f"{tl} & {taul} & {cv:.2f} & " + " & ".join(cells) + " & %.3f & %.3f\\\\" % (g("ideal", "1", "CSL"), g("oracle", "1", "CSL_oracle")))
tab_auc = r"""\begin{table*}[!t]\centering\footnotesize
\caption{AUC of the five scores from a DS18B20 record sampled every 15\,min (baseline run, 4\,000 trips per row). The best score in each row is in bold. The last two columns give the same kinetic score with an ideal sensor sampled every minute, and the oracle that knows each trip's biology.}\label{tab:auc}
\begin{tabular}{@{}lllccccccc@{}}\toprule
Limit & Product & $cv$ & CSL & Degree-h $>4$\,\textdegree C & Time $>5$\,\textdegree C & Time $>8$\,\textdegree C & $T_{\max}$ & Ideal, 1 min & Oracle\\\midrule
""" + "\n".join(rows[:6]) + "\n\\midrule\n" + "\n".join(rows[6:]) + r"""
\bottomrule\end{tabular}\end{table*}"""

# ---------------------------------------------------------------- Table: loss budget per run
br = []
for run, name in RUNS:
    a, p, c = load(run)
    m = lambda s, sm, me: a[(a.sensor == s) & (a.sampling == sm) & (a.method == me)].AUC
    o, i1, pt, d15, d60 = m("oracle", "1", "CSL_oracle"), m("ideal", "1", "CSL"), m("PT1000", "15", "CSL"), m("DS18B20", "15", "CSL"), m("DS18B20", "60", "CSL")
    gap = p[p.contrast == "biology gap: oracle - ideal(1min,CSL)"]["diff"]
    br.append(f"{name} & {o.mean():.3f} & {i1.mean():.3f} & {pt.mean():.3f} & {d15.mean():.3f} & {d60.mean():.3f} & {gap.min():.2f}--{gap.max():.2f}\\\\")
tab_budget = r"""\begin{table}[!htbp]\centering\footnotesize
\caption{Loss budget: mean AUC over the 12 settings of each run as information is removed, and the range of the biology gap (oracle minus ideal sensor).}\label{tab:budget}
\setlength{\tabcolsep}{3.2pt}
\begin{tabular}{@{}lcccccc@{}}\toprule
Run & Oracle & Ideal & PT1000 & DS18B20 & DS18B20 & Biology gap\\
 & & 1\,min & 15\,min & 15\,min & 60\,min & \\\midrule
""" + "\n".join(br) + r"""
\bottomrule\end{tabular}\end{table}"""

# ---------------------------------------------------------------- Table: paired contrasts per run
CON = [("CSL - degree_hours_4C", "CSL $-$ degree-h"), ("CSL - time_above_5C", "CSL $-$ time $>5$\\,\\textdegree C"),
       ("sensor: PT1000 - DS18B20 (CSL,15min)", "PT1000 $-$ DS18B20"), ("sampling: 60min - 1min (DS18B20,CSL)", "60\\,min $-$ 1\\,min"),
       ("adaptive - fixed1min (DS18B20,CSL)", "Adaptive $-$ 1\\,min")]
cr = []
for cn, cl in CON:
    cells = []
    for run, _ in RUNS:
        a, p, c = load(run)
        x = p[p.contrast == cn]
        cells.append(f"{x['diff'].min():.3f}/{x['diff'].max():.3f} ({int(x.excludes_zero.sum())})")
    cr.append(cl + " & " + " & ".join(cells) + "\\\\")
tab_con = r"""\begin{table*}[!t]\centering\footnotesize
\caption{Paired AUC differences on identical trips: minimum/maximum over the 12 settings of each run, with the number of settings (of 12) whose 95\,\% paired-bootstrap interval excludes zero in brackets.}\label{tab:contrasts}
\begin{tabular}{@{}lccccc@{}}\toprule
Contrast & """ + " & ".join(n for _, n in RUNS) + r"""\\\midrule
""" + "\n".join(cr) + r"""
\bottomrule\end{tabular}\end{table*}"""

# ---------------------------------------------------------------- Table: calibration per run
VAR = [("MC matched prior", "Probability, matched prior"), ("MC overconfident b (cv_prior=0)", "Probability, overconfident"), ("point alarm (nominal params)", "Single alarm")]
calr = []
for vk, vl in VAR:
    cells = []
    for run, _ in RUNS:
        a, p, c = load(run)
        x = c[c.variant == vk]
        cells.append(f"{x.ECE.min():.2f}--{x.ECE.max():.2f} / {x.brier.mean():.3f}")
    calr.append(vl + " & " + " & ".join(cells) + "\\\\")
tab_cal = r"""\begin{table*}[!t]\centering\footnotesize
\caption{Calibration: range of expected calibration error over the 12 settings, and mean Brier score, for each run. Lower is better.}\label{tab:cal}
\begin{tabular}{@{}lccccc@{}}\toprule
Variant & """ + " & ".join(n for _, n in RUNS) + r"""\\\midrule
""" + "\n".join(calr) + r"""
\bottomrule\end{tabular}\end{table*}"""

# ---------------------------------------------------------------- analytic error budget (first-order, baseline biology)
B0, TMIN, SDT, CV = 0.030, -7.7, 1.5, 0.10
H0R, N0R, NMAX = (2.5, 5.0), (1.5, 2.0), 9.0
rng = np.random.default_rng(0)


def Kfun(h0, l0, NL):
    A, L = NMAX - l0, math.log10(NL) - l0
    return h0 + A * math.log(10) / math.e * (1 - math.log(-math.log(L / A)))


h0s = rng.uniform(*H0R, 200000); l0s = rng.uniform(*N0R, 200000)
lnK = np.log([Kfun(h, l, 3e4) for h, l in zip(h0s[:20000], l0s[:20000])])
sd_K = float(np.std(lnK))
Tbar = 4.0
sd_b = 2 * CV
sd_T = 2 * SDT / (Tbar - TMIN)
sd_bio = math.sqrt(sd_b ** 2 + sd_T ** 2 + sd_K ** 2)
sd_ds = 2 * (0.5 / math.sqrt(3)) / (Tbar - TMIN)
sd_pt = 2 * (0.15 / math.sqrt(3)) / (Tbar - TMIN)
K_nom = Kfun(3.8, 1.7, 3e4)
mu4, mu13 = (B0 * (4 - TMIN)) ** 2, (B0 * (13 - TMIN)) ** 2
riem = (mu13 - mu4) / K_nom
for k, v in dict(AnSdB="%.2f" % sd_b, AnSdT="%.2f" % sd_T, AnSdK="%.2f" % sd_K, AnSdBio="%.2f" % sd_bio, AnSdDS="%.3f" % sd_ds, AnSdPT="%.3f" % sd_pt,
                 AnRatio="%.0f" % (sd_bio / sd_ds), AnKnom="%.1f" % K_nom, AnRiem="%.3f" % riem, AnOneDeg="%.0f" % (100 * 2 / (Tbar - TMIN)),
                 AnMuFour="%.3f" % mu4, AnMuThirteen="%.3f" % mu13).items():
    mac(k, v)


# ---------------------------------------------------------------- binormal AUC model: predicted vs simulated sensor loss
def auc_of_r(r):
    return 0.5 + 2 / math.pi * math.asin(1 / math.sqrt(2 * (1 + r * r)))


def r_of_auc(A):
    x = math.sin((A - 0.5) * math.pi / 2)
    return math.sqrt(1 / (2 * x * x) - 1)


a0, _, _ = load("base")
bn = []
for thr in ["A_3e4", "B_1e6"]:
    for tau in ["low_mass", "insulated"]:
        sel = a0[(a0.thr == thr) & (a0.tau == tau) & (a0.cv == 0.1) & (a0.method == "CSL")]
        g = lambda s, m: sel[(sel.sensor == s) & (sel.sampling == m)].AUC.iloc[0]
        ai, ads, apt = g("ideal", "1"), g("DS18B20", "1"), g("PT1000", "1")
        r = r_of_auc(ai); sz = sd_bio / r
        pds = auc_of_r(math.sqrt(sd_bio ** 2 + sd_ds ** 2) / sz); ppt = auc_of_r(math.sqrt(sd_bio ** 2 + sd_pt ** 2) / sz)
        bn.append((ai, r, ai - pds, ai - ads, ai - ppt, ai - apt))
bn = np.array(bn)
mac("AnR", "%.1f" % bn[:, 1].mean())
mac("AnPredDS", "%.3f" % bn[:, 2].mean()); mac("AnObsDS", "%.3f" % bn[:, 3].mean())
mac("AnPredPT", "%.3f" % bn[:, 4].mean()); mac("AnObsPT", "%.3f" % bn[:, 5].mean())
print("binormal", bn.round(4))


# ---------------------------------------------------------------- secondary-model comparison and rival integrators
sec = json.load(open(R("results", "secondary_models.json")))
MN = [("sqrt", "Square-root"), ("arrhenius", "Arrhenius"), ("q10", "Constant $Q_{10}$"), ("davey", "Arrhenius--Davey")]
srows = []
for ds, lab in [("Spoilage flora (pasteurised milk)", "Spoilage flora"), ("L. monocytogenes (fitting set)", "\\textit{L.~monocytogenes}")]:
    best = min(sec[ds][k]["AICc"] for k, _ in MN)
    for k, nm in MN:
        e = sec[ds][k]; ce = e["cold_extrapolation"]
        aic = ("\\textbf{%.1f}" if e["AICc"] == best else "%.1f") % e["AICc"]
        srows.append(f"{lab if k == 'sqrt' else ''} & {nm} & {e['rmse_ln']:.3f} & {aic} & {e['cv_rmse_ln']:.3f} & {e['Af']:.2f} & {ce['Bf']:.2f} & {ce['Af']:.2f} & {sec['L. monocytogenes held-out'][k]['Af'] if 'monocytogenes' in ds else float('nan'):.2f}\\\\".replace("nan", "--"))
    srows.append("\\midrule")
tab_sec = r"""\begin{table*}[!t]\centering\footnotesize
\caption{Four secondary models fitted to the ComBase milk records. RMSE and cross-validated (leave one temperature out) RMSE of $\ln\mu$; AICc (best in bold); accuracy factor $A_f$ on the fitting data; bias and accuracy factors when the model is fitted at $T\ge8$\,\textdegree C and used to predict the records below 8\,\textdegree C; $A_f$ on the 53 \textit{Listeria} records held out by condition. Data from ComBase \cite{combase}}\label{tab:secondary}
\begin{tabular}{@{}llccccccc@{}}\toprule
Data & Model & RMSE & AICc & CV RMSE & $A_f$ & Cold $B_f$ & Cold $A_f$ & Held-out $A_f$\\\midrule
""" + "\n".join(srows[:-1]) + r"""
\bottomrule\end{tabular}\end{table*}"""
for k, _ in MN:
    pass
mac("SecEaSp", "%.0f" % sec["Spoilage flora (pasteurised milk)"]["arrhenius"]["params"]["Ea_kJ"])
mac("SecEaLis", "%.0f" % sec["L. monocytogenes (fitting set)"]["arrhenius"]["params"]["Ea_kJ"])
mac("SecQtenSp", "%.1f" % sec["Spoilage flora (pasteurised milk)"]["q10"]["params"]["Q10"])
mac("SecQtenLis", "%.1f" % sec["L. monocytogenes (fitting set)"]["q10"]["params"]["Q10"])
RV = [("CSL - arrhenius_fit", "CSL $-$ Arrhenius, fitted $E_a$"), ("CSL - arrhenius_120kJ", "CSL $-$ Arrhenius, 120 kJ\\,mol$^{-1}$"),
      ("CSL - q10_3", "CSL $-$ $Q_{10}=3$"), ("arrhenius_fit - degree_hours_4C", "Arrhenius, fitted $-$ degree-h")]
rv, tot = [], {}
for cn, nm in RV:
    cells = []; ahead = sig = neg = 0
    for run, _ in RUNS:
        p = pd.read_csv(R("results", run, "paired_contrasts.csv")); x = p[p.contrast == cn]
        cells.append(f"{x['diff'].min():.3f}/{x['diff'].max():.3f} ({int(x.excludes_zero.sum())})".replace("-", "$-$"))
        ahead += int((x["diff"] > 0).sum()); sig += int(((x.lo > 0)).sum()); neg += int((x.hi < 0).sum())
    tot[cn] = (ahead, sig, neg)
    rv.append(nm + " & " + " & ".join(cells) + "\\\\")
tab_rv = r"""\begin{table*}[!t]\centering\footnotesize
\caption{The CSL score against single-parameter integrators on identical trips (DS18B20, 15\,min): minimum/maximum paired AUC difference over the 12 settings of each run, with the number of settings whose 95\,\% paired-bootstrap interval excludes zero in brackets}\label{tab:rivals}
\begin{tabular}{@{}lccccc@{}}\toprule
Contrast & Baseline & Extra lag & Low load & Milk flora & \textit{Listeria}\\\midrule
""" + "\n".join(rv) + r"""
\bottomrule\end{tabular}\end{table*}"""
for cn, key in [("CSL - arrhenius_fit", "Fit"), ("CSL - arrhenius_120kJ", "Wad"), ("CSL - q10_3", "Qten")]:
    a_, s_, n_ = tot[cn]; mac("Rv%sAhead" % key, a_); mac("Rv%sSig" % key, s_); mac("Rv%sNeg" % key, n_)

# ---------------------------------------------------------------- data tables (appendix)
sp = pd.read_csv(R("data", "combase_tasmania_pasteurised_milk.csv")).sort_values("temp_C")
sp_rows = [f"{r.temp_C:.1f} & {r.max_rate_log10_per_h:.4f}" for r in sp.itertuples()]
ncol = 3; per = math.ceil(len(sp_rows) / ncol)
cols = [sp_rows[i * per:(i + 1) * per] for i in range(ncol)]
lines = []
for i in range(per):
    lines.append(" & ".join(cols[j][i] if i < len(cols[j]) else " & " for j in range(ncol)) + "\\\\")
dat_sp = r"""\begin{table}[!htbp]\centering\scriptsize
\caption{ComBase records of aerobic spoilage flora in pasteurised milk ($a_w$ 0.997, pH 6.6; Tasmanian Institute of Agriculture). $\mu_{\max}$: maximum growth rate in decimal-logarithm units (log$_{10}$\,CFU\,mL$^{-1}$ per hour). Data from ComBase \cite{combase}}\label{tab:dsp}
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}cc|cc|cc@{}}\toprule
$T$/\textdegree C & $\mu_{\max}$/h$^{-1}$ & $T$/\textdegree C & $\mu_{\max}$/h$^{-1}$ & $T$/\textdegree C & $\mu_{\max}$/h$^{-1}$\\\midrule
""" + "\n".join(lines) + r"""
\bottomrule\end{tabular}\end{table}"""

full = pd.read_csv(R("data", "combase_milk_records.csv"))
lis = full[full.organism.fillna("").str.startswith("Listeria") & full.max_rate_log10_per_h.notna()].copy()
lis["T"] = pd.to_numeric(lis.temp_C, errors="coerce"); lis = lis[lis["T"].between(2, 16)].sort_values(["T", "max_rate_log10_per_h"])
srcs = list(dict.fromkeys(lis.source.fillna("Not stated")))
skey = {s: f"S{i + 1}" for i, s in enumerate(srcs)}


def short_cond(c):
    c = str(c)
    if "Not specified" in c: return "--"
    c = c.replace("Sterilised", "steril.").replace("sterilised", "steril.").replace("Previously heated", "prev.\\ heated")
    return (c[:34] + "...") if len(c) > 37 else c


lr = [f"{r.T:.1f} & {r.max_rate_log10_per_h:.4f} & {'F' if 'Not specified' in str(r.conditions) else 'H'} & {skey[r.source if isinstance(r.source, str) else 'Not stated']}" for r in lis.itertuples()]
ncol = 3; per = math.ceil(len(lr) / ncol)
cols = [lr[i * per:(i + 1) * per] for i in range(ncol)]
lines = []
for i in range(per):
    lines.append(" & ".join(cols[j][i] if i < len(cols[j]) else " & & & " for j in range(ncol)) + "\\\\")
leg = "; ".join(f"{skey[s]}: {s.replace('&', 'and').replace('%', '')[:150]}" for s in srcs)
dat_lis = r"""\begin{table*}[p]\centering\scriptsize
\caption{ComBase records of \textit{Listeria monocytogenes} in milk at 2--16\,\textdegree C used in this study (""" + str(len(lis)) + r""" records). Set: F = fitting set (no added factors), H = held-out set (other stated conditions). $\mu_{\max}$: maximum growth rate in decimal-logarithm units (log$_{10}$\,CFU\,mL$^{-1}$ per hour); Src: source key below. Data from ComBase \cite{combase}}\label{tab:dlis}
\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{@{}cccc|cccc|cccc@{}}\toprule
$T$/\textdegree C & $\mu_{\max}$/h$^{-1}$ & Set & Src & $T$/\textdegree C & $\mu_{\max}$/h$^{-1}$ & Set & Src & $T$/\textdegree C & $\mu_{\max}$/h$^{-1}$ & Set & Src\\\midrule
""" + "\n".join(lines) + r"""
\bottomrule\end{tabular}

\vspace{4pt}\begin{minipage}{0.96\textwidth}\scriptsize\textit{Sources.} """ + leg + r""".\end{minipage}
\end{table*}"""

comp = full.copy()
comp["org"] = comp.organism.fillna("Other").str.replace("Campylobacteraceae (c.jejuni and relatives)", "Campylobacteraceae").str.replace("Shigellae (s.flexneri and relatives)", "Shigellae")
st = comp.groupby("org").agg(n=("org", "size"), rate=("rate_status", lambda s: int((s == "stated").sum())), fit=("rate_status", lambda s: int((s == "fit_data_required").sum())), ng=("rate_status", lambda s: int((s == "no_growth").sum())), nt=("rate_status", lambda s: int((s == "not_transcribed").sum()))).sort_values("n", ascending=False)
SHORT = {"Listeria monocytogenes/innocua": "\\textit{L.~monocytogenes/innocua}", "Bacillus cereus": "\\textit{Bacillus cereus}", "Escherichia coli": "\\textit{Escherichia coli}",
         "Salmonella spp": "\\textit{Salmonella} spp.", "Cronobacter species": "\\textit{Cronobacter} spp.", "Aerobic total spoilage bacteria": "Aerobic spoilage bacteria"}
cr2 = [f"{SHORT.get(o, o)} & {r.n} & {r.rate} & {r.fit} & {r.ng} & {r.nt}\\\\" for o, r in st.iterrows()]
cr2.append(f"\\midrule Total & {int(st.n.sum())} & {int(st.rate.sum())} & {int(st.fit.sum())} & {int(st.ng.sum())} & {int(st.nt.sum())}\\\\")
dat_comp = r"""\begin{table}[!htbp]\centering\footnotesize
\caption{Composition of the compiled ComBase milk database by organism. $n$: records; Rate: maximum growth rate stated; Curve: growth curve only; None: no growth reported; N/T: rate not transcribed.}\label{tab:dcomp}
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}lccccc@{}}\toprule
Organism & $n$ & Rate & Curve & None & N/T\\\midrule
""" + "\n".join(cr2) + r"""
\bottomrule\end{tabular}\end{table}"""
mac("DatNFull", str(len(full))); mac("DatNLis", str(len(lis))); mac("DatNSp", str(len(sp)))


# ---------------------------------------------------------------- value of a calorimetric measurement of the lot
def _cal(tag=""):
    d = pd.read_csv(R("results", f"calorimetry_info{tag}.csv")); q = pd.read_csv(R("results", f"calorimetry_info{tag}_paired.csv"))
    w = d.pivot_table(index=["thr", "tau", "cv"], columns="method", values="AUC")
    frac = 100 * (w.calorimetry - w.nominal) / (w.oracle - w.nominal)
    return d, q, w, frac
cd, cq, cw, cfrac = _cal()
for m, k in (("nominal", "Nom"), ("budget", "Bud"), ("ratelaw", "Rate"), ("calorimetry", "Cal"), ("oracle", "Orc")):
    mac(f"Cal{k}Min", "%.2f" % cw[m].min()); mac(f"Cal{k}Max", "%.2f" % cw[m].max()); mac(f"Cal{k}Mean", "%.2f" % cw[m].mean())
mac("CalFracMin", "%.0f" % cfrac.min()); mac("CalFracMax", "%.0f" % cfrac.max()); mac("CalFracMean", "%.0f" % cfrac.mean())
for c, k in (("budget - nominal", "GainBud"), ("ratelaw - nominal", "GainRate"), ("calorimetry - nominal", "GainCal"), ("oracle - calorimetry", "Rest")):
    x = cq[cq.contrast == c]; mac(f"Cal{k}Min", "%.2f" % x["diff"].min()); mac(f"Cal{k}Max", "%.2f" % x["diff"].max()); mac(f"Cal{k}Sig", str(int(x.excludes_zero.sum())))
d0 = cd.drop_duplicates(["thr", "tau", "cv"])
mac("CalTdetMed", "%.0f" % d0.tdet_median_h.median()); mac("CalTdetLo", "%.0f" % d0.tdet_p05_h.median()); mac("CalTdetHi", "%.0f" % d0.tdet_p95_h.median())
crow = []
for tag, lab in (("", r"$T_{\mathrm{ref}}=20$\,\textdegree C, 5\,\% error"), ("_cv15", r"$T_{\mathrm{ref}}=20$\,\textdegree C, 15\,\% error"), ("_t10", r"$T_{\mathrm{ref}}=10$\,\textdegree C, 5\,\% error")):
    _, _, w2, f2 = _cal(tag)
    k = {"": "A", "_cv15": "B", "_t10": "C"}[tag]
    mac(f"CalSens{k}Min", "%.2f" % w2.calorimetry.min()); mac(f"CalSens{k}Max", "%.2f" % w2.calorimetry.max()); mac(f"CalSens{k}Frac", "%.0f" % f2.mean())
    crow.append(f"Calorimetric detection time, {lab} & {w2.calorimetry.min():.3f}--{w2.calorimetry.max():.3f} & {w2.calorimetry.mean():.3f} & {f2.min():.0f}--{f2.max():.0f}\\\\")
def _r(m, lab):
    f = 100 * (cw[m] - cw.nominal) / (cw.oracle - cw.nominal)
    return f"{lab} & {cw[m].min():.3f}--{cw[m].max():.3f} & {cw[m].mean():.3f} & {f.min():.0f}--{f.max():.0f}\\\\"
tab_calo = r"""\begin{table}[!htbp]\centering\footnotesize
\caption{Value of a measurement of the biology (baseline run, DS18B20 record sampled every 15\,min, 12 settings of 4\,000 trips). Gap closed: share of the oracle-minus-log-only AUC difference recovered}\label{tab:calo}
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}p{3.9cm}ccc@{}}\toprule
Information added to the log & AUC range & Mean & Gap closed/\%\\\midrule
None (log only) & """ + f"{cw.nominal.min():.3f}--{cw.nominal.max():.3f} & {cw.nominal.mean():.3f} & 0" + r"""\\
""" + _r("budget", "True lag and starting load") + "\n" + _r("ratelaw", "True rate law ($b$, $T_{\\min}$)") + "\n" + "\n".join(crow) + "\n" + r"""All biology (oracle) & 1.000 & 1.000 & 100\\
\bottomrule\end{tabular}\end{table}"""

# ---------------------------------------------------------------- book appendix tables
def _tex(x):
    x = str(x)
    for a, b in (("\\", "/"), ("&", "\\&"), ("%", "\\%"), ("_", "\\_\\allowbreak{}"), ("#", "\\#"), ("^", "\\^{}"), ("~", "$\\sim$"), ("+/-", "$\\pm$")):
        x = x.replace(a, b)
    return x
par = pd.read_csv(R("data", "params.csv"))
prow = [f"{_tex(r.parameter)} & {_tex(r.value)} & {_tex(r.unit) if isinstance(r.unit, str) else ''} & {_tex(r.provenance)}\\\\" for r in par.itertuples()]
tab_params = r"""{\scriptsize\setlength{\tabcolsep}{3pt}
\begin{longtable}{@{}>{\raggedright\arraybackslash}p{2.7cm}>{\raggedright\arraybackslash}p{2.9cm}>{\raggedright\arraybackslash}p{1.6cm}>{\raggedright\arraybackslash}p{6.6cm}@{}}
\caption[Model parameters and provenance]{Model parameters, their values and their provenance, as recorded in \texttt{data/params.csv}. SOURCED: taken from a cited study; FITTED: estimated from data in this work; ASSUMED: no direct source}\label{tab:params}\\\toprule\rowcolor{dghead}
Parameter & Value & Unit & Provenance\\\midrule\endfirsthead
\toprule\rowcolor{dghead}Parameter & Value & Unit & Provenance\\\midrule\endhead
\bottomrule\endfoot
""" + "\n".join(prow) + r"""
\end{longtable}}"""
spd = pd.read_csv(R("data", "combase_tasmania_pasteurised_milk.csv")).sort_values("temp_C")
srows = [f"{r.temp_C:.1f} & {r.max_rate_log10_per_h:.4f}" for r in spd.itertuples()]
per = math.ceil(len(srows) / 3); cols3 = [srows[i * per:(i + 1) * per] for i in range(3)]
lines = [" & ".join(cols3[j][i] if i < len(cols3[j]) else " & " for j in range(3)) + "\\\\" for i in range(per)]
tab_sp = r"""\begin{table}[!htbp]\centering\footnotesize
\caption{ComBase records of aerobic spoilage bacteria in pasteurised milk (Tasmanian Institute of Agriculture; """ + str(len(spd)) + r""" records). $\mu_{\max}$: maximum growth rate in decimal-logarithm units per hour}\label{tab:dsp}
\begin{tabular}{@{}cc|cc|cc@{}}\toprule
$T$/\textdegree C & $\mu_{\max}$/h$^{-1}$ & $T$/\textdegree C & $\mu_{\max}$/h$^{-1}$ & $T$/\textdegree C & $\mu_{\max}$/h$^{-1}$\\\midrule
""" + "\n".join(lines) + r"""
\bottomrule\end{tabular}\end{table}"""


import re as _re
def _shade(x): return _re.sub(r"\\toprule(?!\\rowcolor)", r"\\toprule\\rowcolor{dghead}", x)
open(R("generated", "tables.tex"), "w").write(_shade("\n".join(out) + "\n" + "\n\n".join(["\\newcommand{\\TabAUC}{" + tab_auc + "}", "\\newcommand{\\TabParams}{" + tab_params + "}", "\\newcommand{\\TabSpRecords}{" + tab_sp + "}", "\\newcommand{\\TabCalo}{" + tab_calo + "}", "\\newcommand{\\TabBudget}{" + tab_budget + "}", "\\newcommand{\\TabContrasts}{" + tab_con + "}", "\\newcommand{\\TabCal}{" + tab_cal + "}", "\\newcommand{\\TabDataComp}{" + dat_comp + "}", "\\newcommand{\\TabSecondary}{" + tab_sec + "}", "\\newcommand{\\TabRivals}{" + tab_rv + "}"]) + "\n"))
open(R("generated", "datatables.tex"), "w").write(_shade(dat_sp) + "\n")
open(R("generated", "datatables_lis.tex"), "w").write(_shade(dat_lis) + "\n")

print("analytic:", dict(sd_b=sd_b, sd_T=round(sd_T, 3), sd_K=round(sd_K, 3), sd_bio=round(sd_bio, 3), sd_ds=round(sd_ds, 3), sd_pt=round(sd_pt, 3), K=round(K_nom, 2), riem=round(riem, 3)))
print("lis records", len(lis), "sources", len(srcs))

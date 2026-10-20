"""Write LaTeX tables and analytic numbers for the manuscript from the result files and the data.
Run from the repository root: python paper/make_tables.py  ->  paper/tables.tex"""
import os
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
tab_auc = r"""\begin{table*}[t]\centering\footnotesize
\caption{AUC of the five scores from a DS18B20 record sampled every 15\,min (baseline run, 4\,000 trips per row). The best score in each row is in bold. The last two columns give the same kinetic score with an ideal sensor sampled every minute, and the oracle that knows each trip's biology}\label{tab:auc}
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
tab_budget = r"""\begin{table}[t]\centering\footnotesize
\caption{Loss budget: mean AUC over the 12 settings of each run as information is removed, and the range of the biology gap (oracle minus ideal sensor)}\label{tab:budget}
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
tab_con = r"""\begin{table*}[t]\centering\footnotesize
\caption{Paired AUC differences on identical trips: minimum/maximum over the 12 settings of each run, with the number of settings (of 12) whose 95\,\% paired-bootstrap interval excludes zero in brackets}\label{tab:contrasts}
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
tab_cal = r"""\begin{table*}[t]\centering\footnotesize
\caption{Calibration: range of expected calibration error over the 12 settings, and mean Brier score, for each run. Lower is better}\label{tab:cal}
\begin{tabular}{@{}lccccc@{}}\toprule
Variant & """ + " & ".join(n for _, n in RUNS) + r"""\\\midrule
""" + "\n".join(calr) + r"""
\bottomrule\end{tabular}\end{table*}"""

sp = pd.read_csv(R("data", "combase_tasmania_pasteurised_milk.csv"))
full = pd.read_csv(R("data", "combase_milk_records.csv"))
lis = full[full.organism.fillna("").str.startswith("Listeria") & full.max_rate_log10_per_h.notna()]

comp = full.copy()
comp["org"] = comp.organism.fillna("Other").str.replace("Campylobacteraceae (c.jejuni and relatives)", "Campylobacteraceae").str.replace("Shigellae (s.flexneri and relatives)", "Shigellae")
st = comp.groupby("org").agg(n=("org", "size"), rate=("rate_status", lambda s: int((s == "stated").sum())), fit=("rate_status", lambda s: int((s == "fit_data_required").sum())), ng=("rate_status", lambda s: int((s == "no_growth").sum())), nt=("rate_status", lambda s: int((s == "not_transcribed").sum()))).sort_values("n", ascending=False)
SHORT = {"Listeria monocytogenes/innocua": "\\textit{L.~monocytogenes/innocua}", "Bacillus cereus": "\\textit{Bacillus cereus}", "Escherichia coli": "\\textit{Escherichia coli}",
         "Salmonella spp": "\\textit{Salmonella} spp.", "Cronobacter species": "\\textit{Cronobacter} spp.", "Aerobic total spoilage bacteria": "Aerobic spoilage bacteria"}
cr2 = [f"{SHORT.get(o, o)} & {r.n} & {r.rate} & {r.fit} & {r.ng} & {r.nt}\\\\" for o, r in st.iterrows()]
cr2.append(f"\\midrule Total & {int(st.n.sum())} & {int(st.rate.sum())} & {int(st.fit.sum())} & {int(st.ng.sum())} & {int(st.nt.sum())}\\\\")
dat_comp = r"""\begin{table}[t]\centering\footnotesize
\caption{Composition of the compiled ComBase milk database by organism. $n$: records; Rate: maximum growth rate stated; Curve: growth curve only; None: no growth reported; N/T: rate not transcribed}\label{tab:dcomp}
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}lccccc@{}}\toprule
Organism & $n$ & Rate & Curve & None & N/T\\\midrule
""" + "\n".join(cr2) + r"""
\bottomrule\end{tabular}\end{table}"""
mac("DatNFull", str(len(full))); mac("DatNLis", str(len(lis))); mac("DatNSp", str(len(sp)))

import re as _re
def _shade(x): return _re.sub(r"\\toprule(?!\\rowcolor)", r"\\toprule\\rowcolor{dghead}", x)
T = {"TabAUC": tab_auc, "TabBudget": tab_budget, "TabContrasts": tab_con, "TabCal": tab_cal, "TabDataComp": dat_comp}
open(R("paper", "tables.tex"), "w").write(_shade("\n".join(out) + "\n" + "\n\n".join("\\newcommand{\\%s}{%s}" % kv for kv in T.items()) + "\n"))

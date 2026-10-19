import os
import pandas as pd


def _load(d):
    a = pd.read_csv(f"{d}/auc_results.csv"); a["sampling"] = a["sampling"].astype(str)
    return a, pd.read_csv(f"{d}/paired_contrasts.csv"), pd.read_csv(f"{d}/calibration.csv")


def build(root, fig, ChapterHeading, P, h_sec, figure, table, note, body, W, M):
    cm = 28.35
    a, p, c = _load(f"{root}/results/base")
    a2, p2, c2 = _load(f"{root}/results/lag")
    low = os.path.exists(f"{root}/results/low/calibration.csv")
    if low:
        a3, p3, c3 = _load(f"{root}/results/low")
    lis = os.path.exists(f"{root}/results/lis/calibration.csv")
    if lis:
        a5, p5, c5 = _load(f"{root}/results/lis")
    comb = os.path.exists(f"{root}/results/comb/calibration.csv")
    if comb:
        a4, p4, c4 = _load(f"{root}/results/comb")
    cw = W - 2 * M
    hz = sorted(p.horizon_h.unique())

    def con(df, name):
        return df[df.contrast == name]
    gap = con(p, "biology gap: oracle - ideal(1min,CSL)")
    dh = con(p, "CSL - degree_hours_4C"); t5 = con(p, "CSL - time_above_5C"); mx = con(p, "CSL - max_temperature")
    se = con(p, "sensor: PT1000 - DS18B20 (CSL,15min)"); sa = con(p, "sampling: 60min - 1min (DS18B20,CSL)")
    ad = con(p, "adaptive - fixed1min (DS18B20,CSL)")
    n = len(dh)

    def aucv(df, thr, tau, cv, sen, s, m):
        return df[(df.thr == thr) & (df.tau == tau) & (df.cv == cv) & (df.sensor == sen) & (df.sampling == s) & (df.method == m)].iloc[0].AUC
    s = [ChapterHeading("ch7", "Chapter 7: What a Thermometer Can and Cannot Tell Us", P.__globals__["h_ch"])]
    s.append(P(f"All numbers in this chapter are read from the run's output files. The baseline run covers {n} combinations of two spoilage scenarios (label horizons {hz[0]} h and {hz[1]} h), two product regimes and three levels of strain variability, with 4,000 trips each. Biology is anchored to published sources (Chapter 6), but the strain spread and starting load are assumed (Appendix A). The <i>pattern</i> of the results is the finding. Absolute values are not."))
    s.append(P("1. The loss budget: biology dominates", h_sec))
    s.append(P(f"An oracle that knows each trip's true biology and true temperature separates spoiled from unspoiled trips almost perfectly (AUC about 1.00 by construction). The same kinetic score using nominal biology and an ideal sensor loses between {gap['diff'].min():.2f} and {gap['diff'].max():.2f} AUC across the {len(gap)} settings. The loss is {gap[gap.cv==0]['diff'].mean():.2f} on average when strains do not differ in growth rate, {gap[gap.cv==0.10]['diff'].mean():.2f} at variability 0.10 and {gap[gap.cv==0.25]['diff'].mean():.2f} at 0.25. Even with no strain variability the loss is large, because the minimum growth temperature, the lag state and the starting load still differ between trips. None of this is in the temperature record, so no sensor and no sampling rate can recover it."))
    s.append(figure(os.path.join(fig, "budget.png"), "Loss budget for scenario A at strain variability 0.10. Grey: oracle. Blue: the kinetic score as information is removed. Bars show 95% bootstrap intervals; they are narrow.", cw * 0.78))
    s.append(P("2. Against simple rules: small, consistent gains", h_sec))
    s.append(P(f"On identical trips, the kinetic score beats time above 5 °C in {int(t5.excludes_zero.sum())} of {n} settings and the maximum temperature in {int(mx.excludes_zero.sum())} of {n}. Against degree-hours above 4 °C, a rule that needs no growth model, the gain is positive in all {n} settings but small: {dh['diff'].min():.3f} to {dh['diff'].max():.3f} AUC, with intervals excluding zero in {int(dh.excludes_zero.sum())} of {n}. It is largest for low-mass pouches at low variability and shrinks as variability rises. Because both scores are close to the time integral of a growth rate, this is expected (Chapters 4 and 9). A practical reading is that most of the value of the kinetic score is available from a simple degree-hour count."))
    s.append(figure(os.path.join(fig, "methods.png"), "AUC of five scores from a DS18B20 record sampled every 15 minutes, scenario A. Colours are backed by the table below.", cw * 0.78))
    rows = [["Regime", "Variability", "Kinetic", "Degree-h", "Above 5 °C", "Above 8 °C", "Max temp"]]
    for tau, tl in (("low_mass", "Low-mass"), ("insulated", "Insulated")):
        for cv in (0.0, 0.10, 0.25):
            rows.append([tl, f"{cv:.2f}"] + [f"{aucv(a, 'A_3e4', tau, cv, 'DS18B20', '15', m):.3f}" for m in ("CSL", "deg_hours_4C", "t_above_5C", "t_above_8C", "maxT")])
    s.append(table(rows, [2.6 * cm, 2.2 * cm] + [2.15 * cm] * 5))
    s.append(P("Table: AUC, scenario A, DS18B20 sensor, 15-minute sampling.", P.__globals__["cap"]))
    s.append(P("3. Sensors, sampling and thermal mass", h_sec))
    s.append(P(f"The accurate PT1000 beats the DS18B20 by {se['diff'].min():.3f} to {se['diff'].max():.3f} AUC, with intervals excluding zero in {int(se.excludes_zero.sum())} of {n} settings. The effect is small everywhere. Sampling every 60 minutes instead of every minute makes no detectable difference in {n - int(sa.excludes_zero.sum())} of {n} settings, and the adaptive rule against fixed one-minute sampling shows an interval excluding zero in {int(ad.excludes_zero.sum())} of {n}. Within this trip generator, thermal mass smooths short excursions enough that the record is not sensitive to how often it is read. The practical message is that a cheap sensor read every hour loses very little, and that effort is better spent on the biology."))
    s.append(figure(os.path.join(fig, "forest.png"), "Paired differences in AUC for scenario A at strain variability 0.10. Filled markers: the interval excludes zero.", cw * 0.78))
    s.append(P("4. Does the conclusion survive a structural error?", h_sec))
    dh2 = con(p2, "CSL - degree_hours_4C"); gap2 = con(p2, "biology gap: oracle - ideal(1min,CSL)")
    orc0 = a[a.method == "CSL_oracle"].AUC.mean(); orc2 = a2[a2.method == "CSL_oracle"].AUC.mean()
    kd = [aucv(a, 'A_3e4', t_, cv_, 'DS18B20', '15', 'CSL') - aucv(a2, 'A_3e4', t_, cv_, 'DS18B20', '15', 'CSL') for t_ in ('low_mass', 'insulated') for cv_ in (0.0, 0.10, 0.25)]
    s.append(P(f"In the second run the truth re-imposes a quarter of the lag state after each temperature shift, which the estimator does not model (Chapter 5). The kinetic score still beats degree-hours in all {len(dh2)} settings ({int(dh2.excludes_zero.sum())} of {len(dh2)} intervals exclude zero), by {dh2['diff'].min():.3f} to {dh2['diff'].max():.3f}. The oracle, which also ignores the shift, falls from an average AUC of {orc0:.3f} to {orc2:.3f}, so the structural error costs about {orc0 - orc2:.2f} AUC at the ceiling. The kinetic score itself loses between {min(kd):.2f} and {max(kd):.2f} AUC in scenario A, depending on the setting, as the table shows. The biology gap remains {gap2['diff'].min():.2f} to {gap2['diff'].max():.2f}."))
    rows = [["Regime", "Variability", "Kinetic, baseline", "Kinetic, extra lag", "Degree-h, baseline", "Degree-h, extra lag"]]
    for tau, tl in (("low_mass", "Low-mass"), ("insulated", "Insulated")):
        for cv in (0.0, 0.10, 0.25):
            rows.append([tl, f"{cv:.2f}",
                         f"{aucv(a, 'A_3e4', tau, cv, 'DS18B20', '15', 'CSL'):.3f}", f"{aucv(a2, 'A_3e4', tau, cv, 'DS18B20', '15', 'CSL'):.3f}",
                         f"{aucv(a, 'A_3e4', tau, cv, 'DS18B20', '15', 'deg_hours_4C'):.3f}", f"{aucv(a2, 'A_3e4', tau, cv, 'DS18B20', '15', 'deg_hours_4C'):.3f}"])
    s.append(table(rows, [2.6 * cm, 2.2 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm]))
    s.append(P("Table: AUC, scenario A, DS18B20 sensor, 15-minute sampling, without and with extra lag after temperature shifts.", P.__globals__["cap"]))
    k = 5
    if low:
        dh3 = con(p3, "CSL - degree_hours_4C"); gap3 = con(p3, "biology gap: oracle - ideal(1min,CSL)"); se3 = con(p3, "sensor: PT1000 - DS18B20 (CSL,15min)"); sa3 = con(p3, "sampling: 60min - 1min (DS18B20,CSL)")
        hz3 = sorted(p3.horizon_h.unique())
        s.append(P(f"{k}. A realistic starting load", h_sec)); k += 1
        s.append(P(f"The baseline assumes 30 to 100 cells per millilitre at the start, which is high for pasteurised milk [13]. A third run uses 0.1 to 3 cells per millilitre, which stretches the label horizons to {hz3[0]} h and {hz3[1]} h. The pattern holds. The kinetic score beats degree-hours by {dh3['diff'].min():.3f} to {dh3['diff'].max():.3f} AUC (intervals exclude zero in {int(dh3.excludes_zero.sum())} of {len(dh3)}), the biology gap is {gap3['diff'].min():.2f} to {gap3['diff'].max():.2f}, the sensor effect is {se3['diff'].min():.3f} to {se3['diff'].max():.3f}, and sampling at 60 minutes shows no detectable loss in {len(sa3) - int(sa3.excludes_zero.sum())} of {len(sa3)} settings."))
    if comb:
        dh4 = con(p4, "CSL - degree_hours_4C"); gap4 = con(p4, "biology gap: oracle - ideal(1min,CSL)"); se4 = con(p4, "sensor: PT1000 - DS18B20 (CSL,15min)"); sa4 = con(p4, "sampling: 60min - 1min (DS18B20,CSL)")
        s.append(P(f"{k}. Parameters fitted to real spoilage flora", h_sec)); k += 1
        s.append(P(f"The ComBase check in Chapter 6 showed natural flora grow about 1.6 times slower than the inoculated-isolate parameters. A fourth run replaces the biology with the fitted values (b = 0.0256, T<sub>min</sub> = \u22126.6 \u00b0C, 16% scatter allowed for in the variability axis) and the low starting load. The pattern is unchanged. The kinetic score beats degree-hours by {dh4['diff'].min():.3f} to {dh4['diff'].max():.3f} AUC (intervals exclude zero in {int(dh4.excludes_zero.sum())} of {len(dh4)}), the biology gap is {gap4['diff'].min():.2f} to {gap4['diff'].max():.2f}, the sensor effect is {se4['diff'].min():.3f} to {se4['diff'].max():.3f}, and sampling at 60 minutes shows no detectable loss in {len(sa4) - int(sa4.excludes_zero.sum())} of {len(sa4)} settings. The conclusions do not depend on which parameter set is used."))
    if lis:
        dh5 = con(p5, "CSL - degree_hours_4C"); gap5 = con(p5, "biology gap: oracle - ideal(1min,CSL)"); se5 = con(p5, "sensor: PT1000 - DS18B20 (CSL,15min)"); sa5 = con(p5, "sampling: 60min - 1min (DS18B20,CSL)")
        hz5 = sorted(p5.horizon_h.unique())
        s.append(P(f"{k}. A hazard organism: Listeria", h_sec)); k += 1
        s.append(P(f"The fifth run replaces the spoilage flora with <i>Listeria monocytogenes</i>, using the parameters fitted to real ComBase records in Chapter 6 (b = 0.0235, T<sub>min</sub> = \u22122.3 \u00b0C). A trip is positive if the pathogen grows by half a log (scenario A, label horizon {hz5[0]} h) or by one log (scenario B, {hz5[1]} h) over its starting load. These are round-number labels, not regulatory limits, and the lag and starting load are assumed. The pattern is the same. The kinetic score beats degree-hours by {dh5['diff'].min():.3f} to {dh5['diff'].max():.3f} AUC (intervals exclude zero in {int(dh5.excludes_zero.sum())} of {len(dh5)}), the biology gap is {gap5['diff'].min():.2f} to {gap5['diff'].max():.2f}, the sensor effect is {se5['diff'].min():.3f} to {se5['diff'].max():.3f}, and sampling hourly shows no detectable loss in {len(sa5) - int(sa5.excludes_zero.sum())} of {len(sa5)} settings. One difference matters: for the half-log label (scenario A) even the oracle reaches only {a5[(a5.method=='CSL_oracle')&(a5.thr=='A_3e4')].AUC.min():.2f} to {a5[(a5.method=='CSL_oracle')&(a5.thr=='A_3e4')].AUC.max():.2f} AUC, because a limit that close to the start lies where the closed-form Gompertz shelf life is a poor approximation of the reference. Label choice interacts with the estimator's structure, and the later calibration section reports the consequence. The design rules of Chapter 8 therefore apply to a hazard organism as well as to spoilage, with the caveat that these results say nothing about illness risk."))
        s.append(figure(os.path.join(fig, "runs.png"), "The same four effects across all five runs. Each bar spans the 12 settings of a run (dot: median), as AUC differences on identical trips. The pattern does not depend on the parameter set.", cw))
    s.append(P(f"{k}. An uncertainty-aware score is better calibrated", h_sec)); k += 1
    mm = c[c.variant == "MC matched prior"]; pa = c[c.variant.str.startswith("point")]; oc = c[c.variant.str.startswith("MC over")]
    s.append(P(f"Reporting the fraction of 80 plausible parameter sets that reach the limit gives a probability. With a prior matching the truth, its calibration error is {mm.ECE.min():.2f} to {mm.ECE.max():.2f}, against {pa.ECE.min():.2f} to {pa.ECE.max():.2f} for a single alarm using nominal values, and its Brier score is lower in all {len(mm)} settings. If the prior is overconfident about the growth rate, calibration error rises to as much as {oc.ECE.max():.2f} when variability is 0.25 but stays well below the single alarm. The result needs careful reading: a single alarm is a hard 0 or 1, so it is penalised for confident errors by construction, and the comparison shows the value of expressing uncertainty, not a better model. The matched-prior case is an upper bound, because real priors will never match exactly. For the <i>Listeria</i> run the probability still beats the single alarm in every setting, but with the half-log label its calibration is poor in absolute terms, for the structural reason given above."))
    s.append(figure(os.path.join(fig, "calibration.png"), "Brier score and expected calibration error for scenario A. Lower is better. Values are printed on the bars.", cw * 0.78))
    s.append(P(f"{k}. What the results do and do not support", h_sec))
    s.append(P("Supported within the simulation: unobservable biology is the largest loss by a wide margin; a kinetic score offers a small but consistent edge over a degree-hour count, even when the estimator ignores extra lag after temperature shifts; sensor accuracy matters little; sampling interval does not matter at these settings; and a probability with stated uncertainty is better calibrated than a single alarm. Not supported: any claim about real milk, any claim that the strain spread and starting load assumed here are right, or any claim about illness risk.", note))
    return s

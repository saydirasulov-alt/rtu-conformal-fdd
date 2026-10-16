"""Write LaTeX tables for the Supplementary Material directly from results JSON."""
import json
from pathlib import Path
H=Path(__file__).resolve().parent; R=H/"results"; RR=H.parent/"results"; O=H/"figures"/"supp_tables.tex"
J=lambda p:json.load(open(p))
L=[]
def tab(cap,label,cols,head,rows,size="\\footnotesize"):
    L.append("\\begin{table}[h!]\\centering"+size+f"\\caption{{{cap}}}\\label{{{label}}}\n\\begin{{tabular}}{{{cols}}}\\toprule\n"+head+"\\\\\\midrule\n"+"\n".join(r+"\\\\" for r in rows)+"\n\\bottomrule\\end{tabular}\\end{table}\n")
NM={"S0":"Temperatures + power","S1":"+ pressures","S2":"Condition-aware residuals","S3":"Residuals + pressures"}
g=J(R/"algo_v2_dev_grid.json"); fz=J(R/"algo_v2_FROZEN.json")
rows=[f"{NM[r['S']]} & {r['D'].replace('Dmax','max').replace('Dmean','mean').replace('Ddual','max + mean')} & {'yes' if r['J'] else 'no'} & {r['baseline_test_dayFAR']} & {r['dev_mean_sens']:.1f}"+(" & selected" if (r['S'],r['D'],r['J'])==(fz['S'],fz['D'],fz['J']) else (" & inadmissible" if int(r['baseline_test_dayFAR'].split('/')[0])>3 else " & ")) for r in g]
tab("Development grid on the simulated RTU (12 development scenarios, 25 test days each). FAR: fault-free test days flagged. Candidates flagging more than 3 of 25 days were inadmissible (Amendment 1).","tab:S1","llcccl","Scores & Daily rule & Joint & FAR & Dev. sens. (\\%) & ",rows)
e3=J(R/"e3_ablation.json")["field"]; V={"A0_proposed":"v1 original (plain PIT, day max)","A0x_EXPLORATORY_tieawarePIT":"v1 tie-aware","A1_noPIT_rawmax":"No percentile transform (max of raw branch distances)","A2_noBranches_globalMahal":"No branches (single global distance)","A3_minuteCalibration":"Minute-level instead of day-level calibration"}
rows=[f"{V[k]} & {e3['Site2'][k]['test_dayFAR']} & {e3['Site2'][k]['fault_day_sens']} & {e3['Site1'][k]['test_dayFAR']} & {e3['Site1'][k]['fault_day_sens']}" for k in V]
ev=J(R/"algo_v2_EVALUATION.json"); rows.append(f"Frozen (joint branch, max + mean) & {ev['field_temporal']['Site2']['FROZEN']['test_dayFAR']} & {ev['field_temporal']['Site2']['FROZEN']['fault_day_sens']} & {ev['field_temporal']['Site1']['FROZEN']['test_dayFAR']} & {ev['field_temporal']['Site1']['FROZEN']['fault_day_sens']}")
tab("Component ablation of the original first version (v1, plain transform) under the day-level conformal rule (normal test days flagged; fault days detected).","tab:S2","lcccc","Variant & Site 2 FAR & Site 2 sens. & Site 1 FAR & Site 1 sens.",rows)
st=ev["site2_stability"]; e5=J(R/"e5_temporal_stability.json")
rows=[f"{nm} & "+" & ".join(st[k]['ncal'][n]['FAR'] for n in ('19','25','30','44'))+" & "+" & ".join(st[k]['ncal'][n][' sens'] for n in ('19','25','30','44')) for k,nm in (("FROZEN","Frozen"),("REF_v1like","v1 tie-aware"))]
tab("Site 2, calibration length (training: first 88 days; test: last 44 days; calibration: the $n_{\\mathrm{cal}}$ days before the test block).","tab:S3","lcccccccc","$n_{\\mathrm{cal}}$ & 19 & 25 & 30 & 44 & 19 & 25 & 30 & 44",["& \\multicolumn{4}{c}{normal test days flagged (of 44)} & \\multicolumn{4}{c}{fault days detected (of 27)}"]+rows)
win=e5["proposed_v1.0.1"]["rolling_origin_Site2_60_30_14"]["windows"]
rows=[f"{i+1} & {st['FROZEN']['per_window'][i]} & {st['REF_v1like']['per_window'][i]} & {'unattainable' if w['degenerate_tau'] else w['test_dayFAR']}" for i,w in enumerate(win)]
rows.append(f"Pooled & {st['FROZEN']['rolling_pooled_FAR']} & {st['REF_v1like']['rolling_pooled_FAR']} & {e5['proposed_v1.0.1']['rolling_origin_Site2_60_30_14']['pooled_dayFAR']}")
tab("Site 2 rolling-origin windows (60 training, 30 calibration, 14 test days): normal test days flagged.","tab:S3b","lccc","Window & Frozen & v1 tie-aware & v1 original",rows)
e13=J(R/"e13_physics.json"); rows=[]
for s in ("Site2","Site1"):
    for h in e13[s]["identification"]:
        c1,c2=h["circuits"]["1"],h["circuits"]["2"]
        rows.append(f"{s[-1]} & {h['refrigerant'].replace('R','R-')} & {h['pressure']} & {c1['SH_med']:.1f} / {c2['SH_med']:.1f} & {c1['SC_med']:.1f} / {c2['SC_med']:.1f} & {c1['approach_med']:.1f} / {c2['approach_med']:.1f} & {'yes' if h['plausible_both'] else 'no'}")
tab("Refrigerant and pressure-reference identification on training data (medians, circuit 1 / circuit 2, K). Selected: R-22, absolute, at both sites.","tab:S4","clcccc c","Site & Refrigerant & Pressure & Superheat & Subcooling & Approach & Plausible",rows)
alt=[]
for s in ("Site2","Site1"):
    for k,v in e13[s]["all_plausible_hypotheses"].items(): alt.append(f"{s[-1]} & {k.replace('_',', ').replace('R','R-')} & {v['conformal'][0]} & {v['conformal'][1]} & {v['rule'][0]} & {v['rule'][1]}")
tab("Physics charge indicator under every plausible hypothesis (Phase-2 amendment A1).","tab:S4b","clcccc","Site & Hypothesis & Conformal FAR & Conformal sens. & Rule FAR & Rule sens.",alt)
e10=J(R/"e10_robustness.json")
rows=[f"{k} & {v['sim_holdout']['baseline_test_dayFAR']} & {v['sim_holdout']['holdout_mean_sens_pct']:.1f} & {v['Site2']['test_dayFAR']} & {v['Site2']['fault_day_sens']} & {v['Site1']['test_dayFAR']} & {v['Site1']['fault_day_sens']}" for k,v in e10.items()]
tab("One-at-a-time robustness of the frozen configuration (pre-specified sensitivity analysis, run after freezing; no setting was selected from it).","tab:S5","lcccccc","Setting & Sim. FAR & Sim. sens. (\\%) & Site 2 FAR & Site 2 sens. & Site 1 FAR & Site 1 sens.",[r.replace("_","\\_") for r in rows])
rb=J(R/"e10b_ridge_sweep.json"); ks=[k for k in rb["Site1"] if isinstance(rb["Site1"][k],dict) and "test_dayFAR" in rb["Site1"][k]]
rows=[f"{k} & {rb['Site2'][k]['test_dayFAR']} & {rb['Site2'][k]['fault_day_sens']} & {rb['Site1'][k]['test_dayFAR']} & {rb['Site1'][k]['fault_day_sens']}" for k in ks]
tab("Ridge sweep (Phase-2 amendment A2). Smallest joint-branch covariance eigenvalues: Site 1 "+", ".join(f"{x:.2g}" for x in rb['Site1']['joint_cov_eigenvalues_smallest5'][:3])+"; Site 2 "+", ".join(f"{x:.2g}" for x in rb['Site2']['joint_cov_eigenvalues_smallest5'][:3])+".","tab:S5b","lcccc","Ridge & Site 2 FAR & Site 2 sens. & Site 1 FAR & Site 1 sens.",rows)
e4=J(R/"e4_missingness.json")
rows=[f"{r['masked']} & {r['mode'].replace('_',' ')} & {r['level']} & {r['normal_minute_FAR_pct']:.2f} & "+" & ".join(r['faults'][f]['detection_yield_all_days'] for f in ('economizer','damper','SA-bias'))+f" & {r['unsupported_assertions']}" for r in e4]
tab("ORNL: intermittent loss (fraction of minutes) and daily outages (hours) of the damper, supply-air temperature or power sensors on test and fault days. Fault days detected of 16; full sensing: 15, 13, 15.","tab:S6","llccccc c","Sensors lost & Mode & Level & Min. FAR (\\%) & Econ. & Damper & SA bias & Unsupp.",rows,"\\scriptsize")
eq=J(R/"equal_far_POSTHOC.json"); NMS={"v2_FROZEN":"Frozen","v1_tieaware":"v1 tie-aware","v1.0.1_original":"v1 original","global_Mahalanobis":"Global Mahalanobis","IsolationForest":"Isolation forest"}
rows=[]
for s in ("Site2","Site1"):
    for m,v in eq[s].items():
        ks2=[k for k in v if k.startswith("fault_days")]
        rows.append(f"{s[-1]} & {NMS[m]} & {v['day_AUC']:.3f} & "+" & ".join(str(v[k]) for k in ks2[:3]))
tab("Post-hoc day-level separability (test labels used to place thresholds; diagnostic only). Fault days detected when at most $k$ normal test days are allowed to alarm.","tab:S8","clcccc","Site & Detector & AUC & $k=0$ & $k=1$ & $k=2$",rows)
a13=J(RR/"site1_split_audit_13day.json"); a19=J(RR/"site1_split_audit_19day.json")
rows=[f"{n} training days & {b} & {d['branch'][b]['n_minutes']} & {d['branch'][b]['cov_cond_max']} & {d['branch'][b]['boot_cv_q95']} & {'pass' if d['branch'][b]['branch_pass'] else 'fail'}" for n,d in ((13,a13),(19,a19)) for b in ("refrigerant","power")]
tab("Site 1 training-adequacy audit (training days only; limit on bootstrap CV of the upper tail: 0.15).","tab:S9","llcccc","Candidate & Branch & Minutes & Max cond. & Boot CV & Result",rows)

e12b=J(R/"e12b_injection_equal_budget.json"); NM2={"v2_FROZEN":"Frozen","v1_tieaware_dual_rule":"v1 tie-aware","global_Mahalanobis":"Global Mahalanobis","PCA_T2":"PCA $T^2$","PCA_SPE":"PCA SPE","IsolationForest":"Isolation forest"}
rows=[]
for s_ in ("Site2","Site1"):
    sm=e12b[s_]["summary"]
    for k in NM2: rows.append(f"{s_[-1]} & {NM2[k]} & {sm['clean_FAR'][k]} & {sm['mean_new_alarm_rate_on_quiet_days_pct'][k]:.1f} & {sm['scenarios_alarmed_on_majority_of_days'][k]}")
tab("Injected sensor faults (37 scenarios per site) with every detector under the two-statistic rule (Phase-2 amendment A7).","tab:S12","clccc","Site & Detector & Clean FAR & New-alarm rate on quiet days (\\%) & Scenarios alarmed on most days",rows)
e10c=J(R/"e10c_ridge_spectrum.json")
rows=[f"{k.replace('c=','')} & {v['sim_holdout']['baseline_test_dayFAR']} & {v['sim_holdout']['holdout_mean_sens_pct']:.1f} & {v['Site2']['test_dayFAR']} & {v['Site2']['fault_day_sens']} & {v['Site1']['test_dayFAR']} & {v['Site1']['fault_day_sens']} & {v['Site1']['ridges']['joint0']:.2g}" for k,v in e10c.items()]
tab("Spectrum-relative ridge, $c$ times the median eigenvalue of each branch's scaled training covariance (Phase-2 amendment A8; sensitivity analysis only).","tab:S13","cccccccc","$c$ & Sim. FAR & Sim. sens. (\\%) & Site 2 FAR & Site 2 sens. & Site 1 FAR & Site 1 sens. & Site 1 joint ridge",rows)
O.write_text("\n".join(L)); print("wrote",O)

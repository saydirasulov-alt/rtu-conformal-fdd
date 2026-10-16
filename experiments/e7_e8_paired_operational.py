"""E7 paired comparison (McNemar exact, Holm, day bootstrap) and E8 operational metrics (TTFA, alarms per 30 days,
longest normal alarm run, compute cost). ANALYSIS_PLAN_PHASE2.md."""
import json,time,platform,numpy as np
from pathlib import Path
import phase2_common as P
from e13_physics import identify,Physics
OUT=Path(P.HERE)/"results"; B=5000
def runlen(a):
    best=cur=0
    for x in a: cur=cur+1 if x else 0; best=max(best,cur)
    return best
R={"bootstrap_B":B,"machine":platform.platform(),"python":platform.python_version()}
rng=np.random.default_rng(P.SEED)
for s in P.SITES:
    TR,CA,TE,U=P.site(s); det=P.build_detectors(TR,CA)
    _,sel=identify(TR)
    if sel: det["physics_CI_conformal"]=Physics(TR,CA,sel["refrigerant"],sel["pressure"])
    al={}
    for k,d in det.items():
        if isinstance(d,Physics): al[k]=(d.day_alarms_df(TE),d.day_alarms_df(U))
        else: al[k]=(P.alarms(d,TE),P.alarms(d,U))
    v_te,v_u=al["v2_FROZEN"]; rows={}; pf=[];pn=[]
    comps=[k for k in al if k!="v2_FROZEN"]
    for k in comps:
        c_te,c_u=al[k]
        f=P.mcnemar(v_u,c_u); n=P.mcnemar(v_te,c_te); pf.append(f[2]); pn.append(n[2])
        iu=rng.integers(0,len(v_u),(B,len(v_u))); it=rng.integers(0,len(v_te),(B,len(v_te)))
        ds=(v_u[iu].mean(1)-c_u[iu].mean(1))*100; dn=(v_te[it].mean(1)-c_te[it].mean(1))*100
        rows[k]={"comparator_test_FAR":P.frac(c_te),"comparator_sens":P.frac(c_u),
                 "fault_days":{"v2_only":f[0],"comp_only":f[1],"p_exact":float(f"{f[2]:.3g}"),"diff_pct":round(100*(v_u.mean()-c_u.mean()),1),"boot95":[round(float(np.percentile(ds,2.5)),1),round(float(np.percentile(ds,97.5)),1)]},
                 "normal_days":{"v2_only":n[0],"comp_only":n[1],"p_exact":float(f"{n[2]:.3g}"),"diff_pct":round(100*(v_te.mean()-c_te.mean()),1),"boot95":[round(float(np.percentile(dn,2.5)),1),round(float(np.percentile(dn,97.5)),1)]}}
    for k,hf,hn in zip(comps,P.holm(pf),P.holm(pn)): rows[k]["fault_days"]["p_holm"]=float(f"{hf:.3g}"); rows[k]["normal_days"]["p_holm"]=float(f"{hn:.3g}")
    op={}
    for k,(a_te,a_u) in al.items():
        ttfa=int(np.argmax(a_u))+1 if a_u.any() else None; far=a_te.mean(); ci=P.cp(int(a_te.sum()),len(a_te))
        op[k]={"test_FAR":P.frac(a_te),"sens":P.frac(a_u),"TTFA_days":ttfa,"alarm_days_per_30":round(30*far,2),"per_30_CI95":[round(0.3*ci[0],2),round(0.3*ci[1],2)],
               "longest_normal_alarm_run":runlen(a_te),"fault_day_alarm_sequence":"".join("1" if x else "0" for x in a_u)}
    # compute cost of v2 (fit; score one day), median of 5
    TRd,CAd=P.to_dict(TR),P.to_dict(CA); dd=TE.dt.dt.floor("D"); one=P.to_dict(TE[dd==np.unique(dd)[0]].reset_index(drop=True))
    tf=[];ts=[]
    for _ in range(5):
        t0=time.perf_counter(); d=P.Detector("S0","Ddual",True).fit(TRd,CAd); tf.append(time.perf_counter()-t0)
        t0=time.perf_counter(); d.day_alarms(one); ts.append(time.perf_counter()-t0)
    R[s]={"physics_hypothesis":sel and {"refrigerant":sel["refrigerant"],"pressure":sel["pressure"]},"paired_v2_vs":rows,"operational":op,
          "compute_s":{"fit_median":round(float(np.median(tf)),3),"score_one_day_median":round(float(np.median(ts)),4),
                       "n_train_minutes":int(len(TR)),"n_cal_minutes":int(len(CA)),"n_minutes_scored_day":int(len(one["dt"]))}}
    print("=====",s)
    for k,v in rows.items(): print(f"  v2 vs {k:22s} fault: +{v['fault_days']['v2_only']}/-{v['fault_days']['comp_only']} p={v['fault_days']['p_exact']:.4g} holm={v['fault_days']['p_holm']:.4g} d={v['fault_days']['diff_pct']} {v['fault_days']['boot95']} | normal: +{v['normal_days']['v2_only']}/-{v['normal_days']['comp_only']} p={v['normal_days']['p_exact']:.4g} holm={v['normal_days']['p_holm']:.4g} d={v['normal_days']['diff_pct']} {v['normal_days']['boot95']}")
    for k,v in op.items(): print(f"  {k:22s} FAR {v['test_FAR']:>5s} sens {v['sens']:>5s} TTFA {v['TTFA_days']} per30 {v['alarm_days_per_30']} {v['per_30_CI95']} run {v['longest_normal_alarm_run']}  {v['fault_day_alarm_sequence']}")
    print("  compute",R[s]["compute_s"])
with open(OUT/"e7_e8_paired_operational.json","w") as fh: json.dump(R,fh,indent=1)

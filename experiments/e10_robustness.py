"""E10: one-at-a-time robustness of the frozen v2 configuration (post hoc; nothing is selected). ANALYSIS_PLAN_PHASE2.md."""
import os,json,numpy as np
from pathlib import Path
import phase2_common as P
A=P.A; OUT=Path(P.HERE)/"results"; SIM=os.environ.get("RTU_SIM_DIR"); assert SIM,"set RTU_SIM_DIR"
HOLD=["evapfouling10","evapfouling20","evapfouling30","evapfouling40","evapfouling50","suctionpipe01bar","suctionpipe03bar","suctionpipe06bar","suctionpipe09bar","undercharge10","undercharge15","undercharge20"]
GRID=[("frozen",{})]+[(f"alpha={a}",{"alpha":a}) for a in (0.10,0.20)]+[(f"gate={g}W",{"gate":g}) for g in (100.0,500.0)]+[(f"ridge={r:g}",{"ridge":r}) for r in (1e-4,1e-2)]
def run(alpha=0.05,gate=200.0,ridge=1e-3):
    A.ALPHA=alpha; A.GATE=gate; res={}
    B=A.load_sim(os.path.join(SIM,"RTU_sim_baseline.csv")); (TR,CA,TE),u=A.split_days(B,50,25); td=u[75:]
    det=P.GDetector(ridge=ridge).fit(TR,CA); far=det.day_alarms(TE); sens=[]
    for k in HOLD:
        F=A.load_sim(os.path.join(SIM,f"RTU_sim_{k}.csv")); F=A.subset(F,np.isin(A.dayid(F["dt"]),td)); sens.append(det.day_alarms(F).mean())
    res["sim_holdout"]={"baseline_test_dayFAR":P.frac(far),"holdout_mean_sens_pct":round(100*float(np.mean(sens)),1)}
    for s in P.SITES:
        TRd,CAd,TEd,Ud=P.site(s); d=P.GDetector(ridge=ridge).fit(P.to_dict(TRd),P.to_dict(CAd))
        res[s]={"test_dayFAR":P.frac(d.day_alarms(P.to_dict(TEd))),"fault_day_sens":P.frac(d.day_alarms(P.to_dict(Ud)))}
    A.ALPHA=0.05; A.GATE=200.0; return res
R={}
for name,kw in GRID:
    R[name]=run(**kw); print(f"{name:12s}",R[name])
with open(OUT/"e10_robustness.json","w") as fh: json.dump(R,fh,indent=1)

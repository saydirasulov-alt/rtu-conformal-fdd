"""Frozen evaluation of algorithm v2 (run once). Compares FROZEN vs v1-like reference (S0,Dmax,noJ; tie-aware PIT)."""
import os,sys,json,numpy as np
sys.path.insert(0,os.path.dirname(__file__)); from algo_v2 import *
from pathlib import Path
from scipy.stats import beta
OUT=Path(__file__).resolve().parent/"results"
fz=json.load(open(OUT/"algo_v2_FROZEN.json")); FROZEN=(fz["S"],fz["D"],fz["J"]); REF=("S0","Dmax",False)
def cp(k,n):
    lo=0.0 if k==0 else beta.ppf(0.025,k,n-k+1); hi=1.0 if k==n else beta.ppf(0.975,k+1,n-k); return [round(100*float(lo),1),round(100*float(hi),1)]
def frac(a): return f"{int(a.sum())}/{len(a)}"
R={"frozen_config":fz}
# 1. simulated HOLDOUT
SIM=os.environ["RTU_SIM_DIR"]
HOLD=["evapfouling10","evapfouling20","evapfouling30","evapfouling40","evapfouling50","suctionpipe01bar","suctionpipe03bar","suctionpipe06bar","suctionpipe09bar","undercharge10","undercharge15","undercharge20"]
B=load_sim(os.path.join(SIM,"RTU_sim_baseline.csv")); (TR,CA,TE),u=split_days(B,50,25); td=u[75:]
FH={k:subset(v,np.isin(dayid(v["dt"]),td)) for k,v in ((k,load_sim(os.path.join(SIM,f"RTU_sim_{k}.csv"))) for k in HOLD)}
sim={}
for name,cfg in (("FROZEN",FROZEN),("REF_v1like",REF)):
    det=Detector(*cfg).fit(TR,CA); far=det.day_alarms(TE); s={k:det.day_alarms(v) for k,v in FH.items()}
    sim[name]={"baseline_test_dayFAR":frac(far),"holdout_mean_sens_pct":round(100*float(np.mean([v.mean() for v in s.values()])),1),
               "holdout_sens":{k:frac(v) for k,v in s.items()}}
R["sim_holdout"]=sim
# 2. field temporal splits
D=os.environ["RTU_DATA_DIR"]; field={}
for site,nf,uf,(a,b) in (("Site1","Site1_Unfaulted.csv","Site1_Staging_Fault.csv",(19,19)),("Site2","Site2_Unfaulted.csv","Site2_Undercharged40.csv",(88,44))):
    N=load_field(os.path.join(D,"Field RTU",nf)); U=load_field(os.path.join(D,"Field RTU",uf)); (TRf,CAf,TEf),_=split_days(N,a,b)
    field[site]={}
    for name,cfg in (("FROZEN",FROZEN),("REF_v1like",REF)):
        det=Detector(*cfg).fit(TRf,CAf); far=det.day_alarms(TEf); se=det.day_alarms(U)
        field[site][name]={"test_dayFAR":frac(far),"FAR_CI95":cp(int(far.sum()),len(far)),"fault_day_sens":frac(se),"sens_CI95":cp(int(se.sum()),len(se))}
R["field_temporal"]=field
# 3. Site 2 stability: rolling origin 60/30/14 and n_cal sensitivity
N=load_field(os.path.join(D,"Field RTU","Site2_Unfaulted.csv")); U=load_field(os.path.join(D,"Field RTU","Site2_Undercharged40.csv"))
dd=dayid(N["dt"]); u2=np.unique(dd); st={}
for name,cfg in (("FROZEN",FROZEN),("REF_v1like",REF)):
    roll=[]; o=0
    while o+104<=len(u2):
        det=Detector(*cfg).fit(subset(N,np.isin(dd,u2[o:o+60])),subset(N,np.isin(dd,u2[o+60:o+90]))); roll.append(det.day_alarms(subset(N,np.isin(dd,u2[o+90:o+104])))); o+=14
    allr=np.concatenate(roll); nc={}
    for n in (19,25,30,44):
        det=Detector(*cfg).fit(subset(N,np.isin(dd,u2[:88])),subset(N,np.isin(dd,u2[132-n:132])))
        nc[str(n)]={"FAR":frac(det.day_alarms(subset(N,np.isin(dd,u2[132:]))))," sens":frac(det.day_alarms(U))}
    st[name]={"rolling_pooled_FAR":frac(allr),"rolling_CI95":cp(int(allr.sum()),len(allr)),"per_window":[frac(r) for r in roll],"ncal":nc}
R["site2_stability"]=st
with open(OUT/"algo_v2_EVALUATION.json","w") as fh: json.dump(R,fh,indent=1)
print(json.dumps({k:v for k,v in R.items() if k!="frozen_config"},indent=1))

"""Audit: day vs minute sensitivity under (A) same threshold tau_day, (B) same threshold tau_min.
Clarifies the mathematically consistent reporting."""
from pathlib import Path
RESULTS=Path(__file__).resolve().parent.parent/"results"; RESULTS.mkdir(exist_ok=True)
import os,json,numpy as np
from _common import *
ALPHA=0.05; rng=np.random.default_rng(SEED)
def fit_score(train):
    F=[]
    for fx in [lambda z:cf(z,"_1"),lambda z:cf(z,"_2"),pf]:
        ms=rzfit(np.asarray(fx(train))); mc=mfit(rz(fx(train),ms)); F.append((fx,ms,mc))
    rref=np.maximum(md(rz(F[0][0](train),F[0][1]),F[0][2]),md(rz(F[1][0](train),F[1][1]),F[1][2]))
    pref=md(rz(F[2][0](train),F[2][1]),F[2][2]); return F,np.sort(rref),np.sort(pref)
def score(df,F,rref,pref):
    r=np.maximum(md(rz(F[0][0](df),F[0][1]),F[0][2]),md(rz(F[1][0](df),F[1][1]),F[1][2])); p=md(rz(F[2][0](df),F[2][1]),F[2][2])
    return np.maximum(np.searchsorted(rref,r,"right")/(len(rref)+1),np.searchsorted(pref,p,"right")/(len(pref)+1))
def cq(s,a): n=len(s); k=min(int(np.ceil((1-a)*(n+1))),n)-1; return np.sort(s)[max(k,0)]
def daymax(df,sc): dd=days(df); return np.array([sc[dd==d].max() for d in np.unique(dd)])

def analyze(Nfile,Ufile,sizes,name):
    N=load_field(Nfile); U=load_field(Ufile); dd=days(N); uniq=np.unique(dd)
    a,b,_=sizes; tr=set(uniq[:a]); ca=set(uniq[a:a+b])
    TR=N[np.isin(dd,list(tr))]; CA=N[np.isin(dd,list(ca))]
    F,rref,pref=fit_score(TR)
    tau_min=cq(score(CA,F,rref,pref),ALPHA)           # from calibration MINUTES
    tau_day=cq(daymax(CA,score(CA,F,rref,pref)),ALPHA) # from calibration DAY-MAXIMA
    su=score(U,F,rref,pref); dm=daymax(U,su); nd=len(dm)
    # (A) BOTH at tau_day (consistent day/minute under the SAME day-level threshold)
    day_A=(dm>tau_day).sum(); min_A=(su>tau_day).mean()
    # (B) BOTH at tau_min (consistent under the SAME minute-level threshold)
    day_B=(dm>tau_min).sum(); min_B=(su>tau_min).mean()
    return {"name":name,"n_fault_days":int(nd),"tau_min":round(float(tau_min),4),"tau_day":round(float(tau_day),4),
      "SAME_tau_day":{"day":f"{int(day_A)}/{nd}={round(100*day_A/nd,1)}%","minute":f"{round(100*min_A,1)}%"},
      "SAME_tau_min":{"day":f"{int(day_B)}/{nd}={round(100*day_B/nd,1)}%","minute":f"{round(100*min_B,1)}%"}}
r1=analyze("Site1_Unfaulted.csv","Site1_Staging_Fault.csv",(19,19,13),"Site1 staging")
r2=analyze("Site2_Unfaulted.csv","Site2_Undercharged40.csv",(88,44,44),"Site2 undercharge")

# minute-at-tau_day bootstrap CI (consistent single-threshold reporting)
def minute_ci_at(Nfile,Ufile,sizes):
    N=load_field(Nfile); U=load_field(Ufile); dd=days(N); uniq=np.unique(dd)
    a,b,_=sizes; TR=N[np.isin(dd,list(uniq[:a]))]; CA=N[np.isin(dd,list(uniq[a:a+b]))]
    F,rref,pref=fit_score(TR); tau_day=cq(daymax(CA,score(CA,F,rref,pref)),ALPHA)
    su=score(U,F,rref,pref); Ud=days(U); ud=np.unique(Ud); bz=np.random.default_rng(SEED); db=[]
    for _ in range(2000):
        s=bz.choice(ud,len(ud),True); db.append(np.concatenate([(su[Ud==d]>tau_day) for d in s]).mean())
    return round(100*float((su>tau_day).mean()),1),[round(100*float(np.percentile(db,2.5)),1),round(100*float(np.percentile(db,97.5)),1)]
print("Site2 minute@tau_day:",minute_ci_at("Site2_Unfaulted.csv","Site2_Undercharged40.csv",(88,44,44)))
print("Site1 minute@tau_day:",minute_ci_at("Site1_Unfaulted.csv","Site1_Staging_Fault.csv",(19,19,13)))

# ---- canonical outputs: PRIMARY (tau_S^day) and SUPPLEMENTARY (tau_S^min) kept in separate files ----
ci2=minute_ci_at("Site2_Unfaulted.csv","Site2_Undercharged40.csv",(88,44,44))
ci1=minute_ci_at("Site1_Unfaulted.csv","Site1_Staging_Fault.csv",(19,19,13))
prim=[]
for r,ci in [(r1,ci1),(r2,ci2)]:
    prim.append({"name":r["name"],"n_fault_days":r["n_fault_days"],"tau_day":r["tau_day"],
                 "day_sensitivity":r["SAME_tau_day"]["day"],"minute_sensitivity":r["SAME_tau_day"]["minute"],
                 "minute_sensitivity_pct":ci[0],"minute_sensitivity_95CI_dayblock_bootstrap":ci[1]})
supp=[{"name":r["name"],"tau_min":r["tau_min"],"day_sensitivity":r["SAME_tau_min"]["day"],
       "minute_sensitivity":r["SAME_tau_min"]["minute"]} for r in (r1,r2)]
json.dump(prim,open(RESULTS/"sens_consistency.json","w"),indent=1)
json.dump(supp,open(RESULTS/"supplementary_sens_tau_min.json","w"),indent=1)
print(json.dumps(prim,indent=1))

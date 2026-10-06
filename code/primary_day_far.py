"""PRIMARY day-calibrated (tau_S^day) false-alarm results for both field units.
Site 1 uses the design-based 19/19/13 split (fixed by the outcome-independent training-adequacy
audit); Site 2 uses 88/44/44. Computes: (i) temporal day-level FAR; (ii) day-level FAR over 30
randomized-day splits (mean, IQR, 95% interval, all 30 values); (iii) day-level fault sensitivity.
Minute-level exceedance under the same tau_S^day: minute_far_exact.py.
Minute-level fault sensitivity under the same tau_S^day: sens_consistency.py."""
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
def cq_day(day_scores,a):  # conformal day-level quantile
    n=len(day_scores); k=min(int(np.ceil((1-a)*(n+1))),n)-1; return np.sort(day_scores)[max(k,0)]
def daymax(df,sc):
    dd=days(df); return np.array([sc[dd==d].max() for d in np.unique(dd)])

def split_eval(N,sizes,assign):
    dd=days(N); uniq=np.unique(dd)
    pm = rng.permutation(uniq) if assign=="random" else uniq  # temporal=earliest-first
    a,b,_=sizes; tr=set(pm[:a]); ca=set(pm[a:a+b]); te=set(pm[a+b:])
    TR=N[np.isin(dd,list(tr))]; CA=N[np.isin(dd,list(ca))]; TE=N[np.isin(dd,list(te))]
    F,rref,pref=fit_score(TR)
    sc_ca=score(CA,F,rref,pref); sc_te=score(TE,F,rref,pref)
    tau_day=cq_day(daymax(CA,sc_ca),ALPHA); dayFAR=float((daymax(TE,sc_te)>tau_day).mean())
    return dayFAR,(F,rref,pref,tau_day)

out={}
# ---------- SITE 1: 19/19/13 ----------
N1=load_field("Site1_Unfaulted.csv"); U1=load_field("Site1_Staging_Fault.csv")
dt,fit1=split_eval(N1,(19,19,13),"temporal")
rand=[split_eval(N1,(19,19,13),"random")[0] for _ in range(30)]
rday=rand
out["Site1"]={"split":"19/19/13","temporal_dayLevelFAR_tauday":round(dt,3),
  "random_dayLevelFAR_mean_tauday":round(float(np.mean(rday)),3),
  "random_dayFAR_IQR":[round(float(np.percentile(rday,25)),3),round(float(np.percentile(rday,75)),3)],
  "random_dayFAR_95int":[round(float(np.percentile(rday,2.5)),3),round(float(np.percentile(rday,97.5)),3)],
  "random_dayFAR_all30":[round(float(x),3) for x in rday]}
# day-level + minute-level fault sensitivity (Site1 staging) at the frozen temporal threshold
F,rref,pref,tau_day=fit1
su=score(U1,F,rref,pref)
out["Site1"]["day_sensitivity_tauday"]=round(float((daymax(U1,su)>tau_day).mean()),3)
out["Site1"]["n_fault_days"]=int(len(np.unique(days(U1))))

# ---------- SITE 2: 88/44/44 (unchanged; recompute + day sensitivity) ----------
N2=load_field("Site2_Unfaulted.csv"); U2=load_field("Site2_Undercharged40.csv")
dt2,fit2=split_eval(N2,(88,44,44),"temporal")
rand2=[split_eval(N2,(88,44,44),"random")[0] for _ in range(30)]
r2day=rand2
out["Site2"]={"split":"88/44/44","temporal_dayLevelFAR_tauday":round(dt2,3),
  "random_dayLevelFAR_mean_tauday":round(float(np.mean(r2day)),3),
  "random_dayFAR_95int":[round(float(np.percentile(r2day,2.5)),3),round(float(np.percentile(r2day,97.5)),3)]}
F,rref,pref,tau_day2=fit2
su2=score(U2,F,rref,pref)
out["Site2"]["day_sensitivity_tauday"]=round(float((daymax(U2,su2)>tau_day2).mean()),3)
out["Site2"]["n_fault_days"]=int(len(np.unique(days(U2))))

out["_note"]="Site1 split 19/19/13 selected by outcome-independent training-adequacy audit (13-day power-branch fit unstable). n_cal=19 resolves the 5% day-level quantile."
with open(RESULTS/"primary_day_far.json","w") as fh: fh.write(json.dumps(out,indent=1))
print(json.dumps(out,indent=1))


"""SUPPLEMENTARY secondary minute-calibrated detector (tau_S^min). NOT a primary result.

tau_S^min is the (1-alpha) conformal quantile of calibration-MINUTE scores. For each field unit this
script computes, under the same train/calibration/test protocol as the primary analysis:
  * temporal (earliest-first) split: minute-level FAR on normal test minutes;
  * 30 randomized-day splits with the same split sizes: mean minute-level FAR;
  * minute-level fault sensitivity on the labeled fault episode (temporal split), with a 95%
    day-block bootstrap interval (2000 resamples of fault days);
  * Site 2 only: the sensitivity / minute-FAR operating-point tradeoff at alpha = 0.05 and 0.115
    (temporal split).
Split sizes: Site 2 = 88/44/44, Site 1 = 19/19/13 (train/cal/test days). Seed = SEED (_common.py).
Random splits draw from one generator in the order Site 1 then Site 2."""
from pathlib import Path
RESULTS=Path(__file__).resolve().parent.parent/"results"; RESULTS.mkdir(exist_ok=True)
import json,numpy as np
from _common import *
ALPHA=0.05; rng=np.random.default_rng(SEED)

def fit_score(train):
    F=[]
    for fx in [lambda z:cf(z,"_1"),lambda z:cf(z,"_2"),pf]:
        ms=rzfit(np.asarray(fx(train))); mc=mfit(rz(fx(train),ms)); F.append((fx,ms,mc))
    rref=np.sort(np.maximum(md(rz(F[0][0](train),F[0][1]),F[0][2]),md(rz(F[1][0](train),F[1][1]),F[1][2])))
    pref=np.sort(md(rz(F[2][0](train),F[2][1]),F[2][2]))
    return F,rref,pref
def score(df,F,rref,pref):
    r=np.maximum(md(rz(F[0][0](df),F[0][1]),F[0][2]),md(rz(F[1][0](df),F[1][1]),F[1][2])); p=md(rz(F[2][0](df),F[2][1]),F[2][2])
    return np.maximum(np.searchsorted(rref,r,"right")/(len(rref)+1),np.searchsorted(pref,p,"right")/(len(pref)+1))
def cq(s,a): n=len(s); k=min(int(np.ceil((1-a)*(n+1))),n)-1; return np.sort(s)[max(k,0)]

def split(N,sizes,assign):
    dd=days(N); uniq=np.unique(dd); pm=rng.permutation(uniq) if assign=="random" else uniq
    a,b,_=sizes
    return (N[np.isin(dd,list(pm[:a]))],N[np.isin(dd,list(pm[a:a+b]))],N[np.isin(dd,list(pm[a+b:]))])
def minute_far(N,sizes,assign,alpha=ALPHA):
    TR,CA,TE=split(N,sizes,assign); F,rref,pref=fit_score(TR)
    tau=cq(score(CA,F,rref,pref),alpha); return float((score(TE,F,rref,pref)>tau).mean()),(F,rref,pref,CA,TE)
def sens_ci(U,F,rref,pref,tau):
    su=score(U,F,rref,pref); Ud=days(U); ud=np.unique(Ud); bz=np.random.default_rng(SEED); db=[]
    for _ in range(2000):
        s=bz.choice(ud,len(ud),True); db.append(np.concatenate([(su[Ud==d]>tau) for d in s]).mean())
    return round(float((su>tau).mean()),3),[round(float(np.percentile(db,2.5)),3),round(float(np.percentile(db,97.5)),3)],int(len(ud))

out={"detector":"secondary minute-calibrated detector (tau_S^min); supplementary only","alpha":ALPHA}
for name,nf,uf,sz in [("Site1","Site1_Unfaulted.csv","Site1_Staging_Fault.csv",(19,19,13)),
                      ("Site2","Site2_Unfaulted.csv","Site2_Undercharged40.csv",(88,44,44))]:
    N=load_field(nf); U=load_field(uf)
    t_far,(F,rref,pref,CA,TE)=minute_far(N,sz,"temporal")
    rnd=[minute_far(N,sz,"random")[0] for _ in range(30)]
    tau=cq(score(CA,F,rref,pref),ALPHA); sens,ci,nfd=sens_ci(U,F,rref,pref,tau)
    rec={"split_train_cal_test_days":list(sz),
         "temporal_minute_FAR":round(t_far,3),
         "randomized_mean_minute_FAR":round(float(np.mean(rnd)),3),
         "randomized_minute_FAR_all30":[round(x,3) for x in rnd],
         "temporal_minute_fault_sensitivity":sens,
         "temporal_minute_fault_sensitivity_95CI_dayblock":ci,
         "n_fault_days":nfd}
    if name=="Site2":
        ops={}
        for a in (0.05,0.115):
            tau_a=cq(score(CA,F,rref,pref),a); s_a,ci_a,_=sens_ci(U,F,rref,pref,tau_a)
            ops[f"alpha_{a}"]={"held_out_minute_FAR":round(float((score(TE,F,rref,pref)>tau_a).mean()),3),
                               "minute_fault_sensitivity":s_a,"sensitivity_95CI_dayblock":ci_a}
        rec["operating_points_temporal"]=ops
    out[name]=rec
json.dump(out,open(RESULTS/"supplementary_minute_detector.json","w"),indent=1)
print(json.dumps({k:{kk:vv for kk,vv in v.items() if kk!="randomized_minute_FAR_all30"} if isinstance(v,dict) else v for k,v in out.items()},indent=1))

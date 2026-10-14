"""POST-HOC diagnostic (uses test labels to set thresholds; NOT a deployable result):
sensitivity at matched observed day-FAR and day-level ROC-AUC for v1.0.1, v1 tie-aware, v2 FROZEN,
global Mahalanobis, Isolation Forest, on identical field splits. Each detector's continuous day score:
v1/ref: day-max of minute score; v2: max of calibration-CDF ranks of day-max and day-mean (the same
two statistics v2 thresholds); baselines: day-max of raw score."""
import os,sys,json,numpy as np
sys.path.insert(0,os.path.dirname(__file__)); sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","code"))
from algo_v2 import Detector,load_field as lf2,split_days,dayid
import _common as C
from sklearn.ensemble import IsolationForest
from pathlib import Path
OUT=Path(__file__).resolve().parent/"results"; D=os.environ["RTU_DATA_DIR"]
def auc(p,n): p=np.asarray(p);n=np.asarray(n); return float(((p[:,None]>n[None,:]).sum()+0.5*(p[:,None]==n[None,:]).sum())/(len(p)*len(n)))
def sens_at(nt,ft,k):
    # smallest threshold with at most k normal-test alarms
    th=np.sort(nt)[::-1][k] if k<len(nt) else -np.inf
    return int((ft>th).sum())
def daymax(dt,s): dd=dayid(dt); return np.array([s[dd==i].max() for i in np.unique(dd)])
R={}
for site,nf,uf,(a,b) in (("Site1","Site1_Unfaulted.csv","Site1_Staging_Fault.csv",(19,19)),("Site2","Site2_Unfaulted.csv","Site2_Undercharged40.csv",(88,44))):
    N=lf2(os.path.join(D,"Field RTU",nf)); U=lf2(os.path.join(D,"Field RTU",uf)); (TR,CA,TE),_=split_days(N,a,b)
    scores={}
    # v1 tie-aware reference and v2 frozen
    for name,cfg in (("v1_tieaware",("S0","Dmax",False)),("v2_FROZEN",("S0","Ddual",True))):
        det=Detector(*cfg).fit(TR,CA)
        if name=="v1_tieaware": scores[name]=(det.day_stats(TE)[0],det.day_stats(U)[0])
        else:
            cmx,cmn,_=det.day_stats(CA); sc=lambda X:(lambda mx,mn:np.maximum(np.searchsorted(np.sort(cmx),mx,"right"),np.searchsorted(np.sort(cmn),mn,"right"))+1e-6*mn)(*det.day_stats(X)[:2])
            scores[name]=(sc(TE),sc(U))
    # v1.0.1 original (non-tie-aware PIT), via code/_common on its own loader
    N1=C.load_field(nf); U1=C.load_field(uf); d1=C.days(N1); u1=np.unique(d1)
    F,rc,pc=C.fit_on(N1[np.isin(d1,u1[:a])]); TE1=N1[np.isin(d1,u1[a+b:])]
    def dm(df): s=C.Tval(df,F,rc,pc); dd=C.days(df); return np.array([s[dd==i].max() for i in np.unique(dd)])
    scores["v1.0.1_original"]=(dm(TE1),dm(U1))
    # baselines on 11 features
    X=lambda Z: np.column_stack([np.column_stack([c["T"] for c in Z["circ"]]),Z["power"]])
    med=np.median(X(TR),0); iqr=np.percentile(X(TR),75,0)-np.percentile(X(TR),25,0)+1e-9; z=lambda Z:(X(Z)-med)/iqr
    Ci=np.linalg.pinv(np.cov(z(TR).T)+1e-3*np.eye(11)); mu=z(TR).mean(0); mh=lambda Z:np.einsum("ij,jk,ik->i",z(Z)-mu,Ci,z(Z)-mu)
    scores["global_Mahalanobis"]=(daymax(TE["dt"],mh(TE)),daymax(U["dt"],mh(U)))
    iso=IsolationForest(n_estimators=200,random_state=20260618).fit(z(TR)); isf=lambda Z:-iso.score_samples(z(Z))
    scores["IsolationForest"]=(daymax(TE["dt"],isf(TE)),daymax(U["dt"],isf(U)))
    ks=(0,1,2,4) if site=="Site2" else (0,1,2)
    R[site]={m:{"n_normal_test_days":len(nt),"n_fault_days":len(ft),"day_AUC":round(auc(ft,nt),3),
              **{f"fault_days_detected_at_testFAR<={k}/{len(nt)}":sens_at(nt,ft,k) for k in ks}} for m,(nt,ft) in scores.items()}
with open(OUT/"equal_far_POSTHOC.json","w") as fh: json.dump(R,fh,indent=1)
for s,o in R.items():
    print("=====",s)
    for m,v in o.items(): print(f"  {m:20s}",{k:v[k] for k in v if k.startswith('day_AUC') or k.startswith('fault_days')})

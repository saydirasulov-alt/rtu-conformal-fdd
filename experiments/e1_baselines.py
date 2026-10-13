"""E1: baselines on identical features/splits/calibration data. Pre-registered in ANALYSIS_PLAN_PHASE1.md."""
import sys,os,json,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","code"))
from _common import *
from pathlib import Path
from scipy.stats import chi2
from sklearn.ensemble import IsolationForest
OUT=Path(__file__).resolve().parent/"results"; OUT.mkdir(exist_ok=True)
ALPHA=0.05
def cq(s,a): n=len(s); k=min(int(np.ceil((1-a)*(n+1))),n)-1; return np.sort(s)[max(k,0)]
def daymax(df,sc): dd=days(df); return np.array([sc[dd==d].max() for d in np.unique(dd)])
def X11(df): return np.column_stack([cf(df,"_1"),cf(df,"_2"),pf(df)])
def evaluate(sTR,sCA,sTE,sU,TE,U,extra_thr=None):
    rules={"C_conformal_day":cq(daymax(CA_,sCA),ALPHA),"U_train_p99":np.percentile(sTR,99)}
    if extra_thr is not None: rules.update(extra_thr)
    res={}
    for r,t in rules.items():
        dn=daymax(TE,sTE); df_=daymax(U,sU)
        res[r]={"thr":float(t),"test_dayFAR":f"{int((dn>t).sum())}/{len(dn)}","test_dayFAR_pct":round(100*float((dn>t).mean()),1),
                "test_minute_exceed_pct":round(100*float((sTE>t).mean()),3),
                "fault_day_sens":f"{int((df_>t).sum())}/{len(df_)}","fault_day_sens_pct":round(100*float((df_>t).mean()),1),
                "fault_minute_sens_pct":round(100*float((sU>t).mean()),1)}
    return res
R={}
for Nf,Uf,sz,name in [("Site1_Unfaulted.csv","Site1_Staging_Fault.csv",(19,19,13),"Site1"),
                      ("Site2_Unfaulted.csv","Site2_Undercharged40.csv",(88,44,44),"Site2")]:
    N=load_field(Nf); U=load_field(Uf); dd=days(N); uq=np.unique(dd); a,b,_=sz
    TR=N[np.isin(dd,uq[:a])]; CA_=N[np.isin(dd,uq[a:a+b])]; TE=N[np.isin(dd,uq[a+b:])]
    ms=rzfit(X11(TR)); Z={k:rz(X11(d),ms) for k,d in [("TR",TR),("CA",CA_),("TE",TE),("U",U)]}
    out={}
    # Proposed (v1.0.1)
    F,rc,pc=fit_on(TR); s={k:Tval(d,F,rc,pc) for k,d in [("TR",TR),("CA",CA_),("TE",TE),("U",U)]}
    out["Proposed_branchPIT"]=evaluate(s["TR"],s["CA"],s["TE"],s["U"],TE,U)
    # B1 global Mahalanobis
    mc=mfit(Z["TR"]); s={k:md(Z[k],mc) for k in Z}
    out["B1_global_Mahalanobis"]=evaluate(s["TR"],s["CA"],s["TE"],s["U"],TE,U,{"U_chi2_0.99":chi2.ppf(0.99,11)})
    # B2 PCA
    mu=Z["TR"].mean(0); C=np.cov((Z["TR"]-mu).T); w,V=np.linalg.eigh(C); o=np.argsort(w)[::-1]; w,V=w[o],V[:,o]
    q=int(np.searchsorted(np.cumsum(w)/w.sum(),0.95)+1); P=V[:,:q]
    def t2(Zx): T=(Zx-mu)@P; return (T**2/w[:q]).sum(1)
    def spe(Zx): E=(Zx-mu)-((Zx-mu)@P)@P.T; return (E**2).sum(1)
    s={k:t2(Z[k]) for k in Z}; out[f"B2a_PCA_T2_q{q}"]=evaluate(s["TR"],s["CA"],s["TE"],s["U"],TE,U)
    s={k:spe(Z[k]) for k in Z}; out[f"B2b_PCA_SPE_q{q}"]=evaluate(s["TR"],s["CA"],s["TE"],s["U"],TE,U)
    # B3 Isolation Forest
    iso=IsolationForest(n_estimators=200,random_state=SEED).fit(Z["TR"])
    s={k:-iso.score_samples(Z[k]) for k in Z}; out["B3_IsolationForest"]=evaluate(s["TR"],s["CA"],s["TE"],s["U"],TE,U)
    R[name]=out
with open(OUT/"e1_baselines.json","w") as fh: json.dump(R,fh,indent=1)
for site,o in R.items():
    print("=====",site)
    for m,rr in o.items():
        for r,v in rr.items(): print(f"{m:26s} {r:16s} dayFAR {v['test_dayFAR']:>6s} ({v['test_dayFAR_pct']:5.1f}%)  minFAR {v['test_minute_exceed_pct']:7.3f}%  faultDay {v['fault_day_sens']:>6s} ({v['fault_day_sens_pct']:5.1f}%)  faultMin {v['fault_minute_sens_pct']:5.1f}%")

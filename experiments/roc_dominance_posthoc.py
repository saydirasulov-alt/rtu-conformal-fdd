"""POST-HOC: full day-level ROC curves (uses test labels; diagnostic only). Checks whether v2 FROZEN
dominates each comparator at every normal-test false-alarm count k (0..n_test), and reports crossings."""
import os,sys,json,numpy as np
sys.path.insert(0,os.path.dirname(__file__)); from equal_far_posthoc import *  # reuses the scores built there (re-runs it)
rows={}
for site,o in R.items():
    pass
# rebuild scores dict per site by re-executing the scoring part of equal_far_posthoc (it stores only summaries), so recompute:
import equal_far_posthoc as E
res={}
for site,nf,uf,(a,b) in (("Site1","Site1_Unfaulted.csv","Site1_Staging_Fault.csv",(19,19)),("Site2","Site2_Unfaulted.csv","Site2_Undercharged40.csv",(88,44))):
    N=lf2(os.path.join(D,"Field RTU",nf)); U=lf2(os.path.join(D,"Field RTU",uf)); (TR,CA,TE),_=split_days(N,a,b)
    S={}
    for name,cfg in (("v1_tieaware",("S0","Dmax",False)),("v2_FROZEN",("S0","Ddual",True))):
        det=Detector(*cfg).fit(TR,CA)
        if name=="v1_tieaware": S[name]=(det.day_stats(TE)[0],det.day_stats(U)[0])
        else:
            cmx,cmn,_=det.day_stats(CA); sc=lambda X:(lambda mx,mn:np.maximum(np.searchsorted(np.sort(cmx),mx,"right"),np.searchsorted(np.sort(cmn),mn,"right"))+1e-6*mn)(*det.day_stats(X)[:2]); S[name]=(sc(TE),sc(U))
    X=lambda Z: np.column_stack([np.column_stack([c["T"] for c in Z["circ"]]),Z["power"]])
    med=np.median(X(TR),0); iqr=np.percentile(X(TR),75,0)-np.percentile(X(TR),25,0)+1e-9; z=lambda Z:(X(Z)-med)/iqr
    Ci=np.linalg.pinv(np.cov(z(TR).T)+1e-3*np.eye(11)); mu=z(TR).mean(0); mh=lambda Z:np.einsum("ij,jk,ik->i",z(Z)-mu,Ci,z(Z)-mu)
    S["global_Mahalanobis"]=(daymax(TE["dt"],mh(TE)),daymax(U["dt"],mh(U)))
    iso=IsolationForest(n_estimators=200,random_state=20260618).fit(z(TR)); isf=lambda Z:-iso.score_samples(z(Z)); S["IsolationForest"]=(daymax(TE["dt"],isf(TE)),daymax(U["dt"],isf(U)))
    n=len(S["v2_FROZEN"][0]); curves={m:[sens_at(nt,ft,k) for k in range(n+1)] for m,(nt,ft) in S.items()}
    v2=curves["v2_FROZEN"]; comp={}
    for m,c in curves.items():
        if m=="v2_FROZEN": continue
        worse=[k for k in range(n+1) if v2[k]<c[k]]; comp[m]={"k_where_v2_below":worse,"dominates":len(worse)==0}
    res[site]={"n_normal_test_days":n,"n_fault_days":len(S["v2_FROZEN"][1]),"curves_fault_days_vs_k":curves,"v2_vs":comp}
with open(OUT/"roc_dominance_POSTHOC.json","w") as fh: json.dump(res,fh,indent=1)
for s,o in res.items():
    print("=====",s,"(fault days detected at k allowed normal-test alarms, k=0..%d)"%o["n_normal_test_days"])
    for m,c in o["curves_fault_days_vs_k"].items(): print(f"  {m:20s}",c[:8],"...")
    for m,v in o["v2_vs"].items(): print(f"  v2 vs {m:18s} dominates={v['dominates']} v2 below at k={v['k_where_v2_below']}")

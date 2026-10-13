"""E5: temporal calibration stability (pre-registered addendum)."""
import sys,os,json,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","code"))
from _common import *
from pathlib import Path
from scipy.stats import beta
OUT=Path(__file__).resolve().parent/"results"; OUT.mkdir(exist_ok=True)
ALPHA=0.05
def cq(s,a): n=len(s); k=min(int(np.ceil((1-a)*(n+1))),n)-1; return np.sort(s)[max(k,0)]
def daymax(df,sc): dd=days(df); return np.array([sc[dd==d].max() for d in np.unique(dd)])
def cp(k,n):
    lo=0.0 if k==0 else beta.ppf(0.025,k,n-k+1); hi=1.0 if k==n else beta.ppf(0.975,k+1,n-k)
    return [round(100*float(lo),1),round(100*float(hi),1)]
def Tx(df,F,rc,pc):
    """EXPLORATORY tie-aware PIT: strictly increasing extension beyond the training maximum."""
    r=np.maximum(md(rz(F[0][0](df),F[0][1]),F[0][2]),md(rz(F[1][0](df),F[1][1]),F[1][2])); p=md(rz(F[2][0](df),F[2][1]),F[2][2])
    def ext(x,ref):
        ref=np.sort(ref); n=len(ref); T=np.searchsorted(ref,x,"right")/(n+1); m=ref[-1]; b=x>m; T[b]=n/(n+1)+(1/(n+1))*(1-m/x[b]); return T
    return np.maximum(ext(r,rc),ext(p,pc))
SCORER=Tval
def window(N,tr_d,ca_d,te_d,U=None):
    dd=days(N); TR=N[np.isin(dd,tr_d)]; CA=N[np.isin(dd,ca_d)]; TE=N[np.isin(dd,te_d)]
    F,rc,pc=fit_on(TR); ceil=max(len(rc)/(len(rc)+1),len(pc)/(len(pc)+1))
    if SCORER is not Tval: ceil=1.0
    t=cq(daymax(CA,SCORER(CA,F,rc,pc)),ALPHA); dn=daymax(TE,SCORER(TE,F,rc,pc)); k=int((dn>t).sum())
    r={"n_train":len(tr_d),"n_cal":len(ca_d),"n_test":len(te_d),"tau":round(float(t),6),"degenerate_tau":bool(t>=ceil-1e-12),
       "test_dayFAR":f"{k}/{len(dn)}","test_dayFAR_CI95":cp(k,len(dn))}
    if U is not None:
        du=daymax(U,SCORER(U,F,rc,pc)); ku=int((du>t).sum()); r["fault_day_sens"]=f"{ku}/{len(du)}"; r["fault_day_sens_CI95"]=cp(ku,len(du))
    return r
def analyses():
    R={}
    # 1. exact CIs for primary temporal results
    N1=load_field("Site1_Unfaulted.csv"); U1=load_field("Site1_Staging_Fault.csv"); u1=np.unique(days(N1))
    N2=load_field("Site2_Unfaulted.csv"); U2=load_field("Site2_Undercharged40.csv"); u2=np.unique(days(N2))
    R["primary_with_exact_CI"]={"Site1":window(N1,u1[:19],u1[19:38],u1[38:],U1),"Site2":window(N2,u2[:88],u2[88:132],u2[132:],U2)}
    # 2. rolling origin, Site 2: 60/30/14, step 14
    roll=[]; o=0
    while o+60+30+14<=len(u2):
        r=window(N2,u2[o:o+60],u2[o+60:o+90],u2[o+90:o+104]); r["origin_day"]=int(o); roll.append(r); o+=14
    tot=sum(int(r["test_dayFAR"].split("/")[0]) for r in roll); den=sum(int(r["test_dayFAR"].split("/")[1]) for r in roll)
    R["rolling_origin_Site2_60_30_14"]={"windows":roll,"pooled_dayFAR":f"{tot}/{den}","pooled_CI95":cp(tot,den),
       "n_degenerate_windows":int(sum(r["degenerate_tau"] for r in roll))}
    # 3. calibration-size sensitivity, Site 2
    cs=[]
    for nc in (19,25,30,44):
        r=window(N2,u2[:88],u2[132-nc:132],u2[132:],U2); cs.append(r)
    R["ncal_sensitivity_Site2"]=cs
    
    return R
R={'proposed_v1.0.1':analyses()}
SCORER=Tx
R['EXPLORATORY_tieaware_PIT']=analyses()
with open(OUT/"e5_temporal_stability.json","w") as fh: json.dump(R,fh,indent=1)
for v,RR in R.items():
    print("#####",v); pr=RR["primary_with_exact_CI"]
    for s in pr: print(s,"FAR",pr[s]["test_dayFAR"],pr[s]["test_dayFAR_CI95"],"sens",pr[s]["fault_day_sens"],pr[s]["fault_day_sens_CI95"],"deg",pr[s]["degenerate_tau"])
    ro=RR["rolling_origin_Site2_60_30_14"]
    for r in ro["windows"]: print("  roll",r["origin_day"],r["test_dayFAR"],"deg",r["degenerate_tau"])
    print("  pooled",ro["pooled_dayFAR"],ro["pooled_CI95"],"degenerate windows",ro["n_degenerate_windows"])
    for r in RR["ncal_sensitivity_Site2"]: print("  n_cal",r["n_cal"],"FAR",r["test_dayFAR"],"sens",r["fault_day_sens"],"deg",r["degenerate_tau"])

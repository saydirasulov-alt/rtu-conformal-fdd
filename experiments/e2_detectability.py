"""E2: detectability analysis for field sites (Site 1 staging fault, Site 2 undercharge)."""
import sys,os,json,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","code"))
from _common import *
from pathlib import Path
OUT=Path(__file__).resolve().parent/"results"; OUT.mkdir(exist_ok=True)
ALPHA=0.05
def cq(s,a): n=len(s); k=min(int(np.ceil((1-a)*(n+1))),n)-1; return np.sort(s)[max(k,0)]
def daymax(df,sc): dd=days(df); return np.array([sc[dd==d].max() for d in np.unique(dd)])
def auc(pos,neg):
    pos=np.asarray(pos); neg=np.asarray(neg)
    return float(((pos[:,None]>neg[None,:]).sum()+0.5*(pos[:,None]==neg[None,:]).sum())/(len(pos)*len(neg)))
FX={"refrig_c1":lambda z:cf(z,"_1"),"refrig_c2":lambda z:cf(z,"_2"),"power":pf}
FN={"refrig_c1":["COND_1","DISC_1","SUCT_1","DISC-SUCT_1"],"refrig_c2":["COND_2","DISC_2","SUCT_2","DISC-SUCT_2"],"power":["COMP_W","TOT_W","FAN_W"]}
def run(Nf,Uf,sz,name):
    N=load_field(Nf); U=load_field(Uf); dd=days(N); uq=np.unique(dd); a,b,_=sz
    TR=N[np.isin(dd,uq[:a])]; CA=N[np.isin(dd,uq[a:a+b])]; TE=N[np.isin(dd,uq[a+b:])]
    fit={}; raw={}
    for k,fx in FX.items():
        ms=rzfit(np.asarray(fx(TR))); mc=mfit(rz(fx(TR),ms)); fit[k]=(fx,ms,mc)
    def rawsc(df,k): fx,ms,mc=fit[k]; return md(rz(fx(df),ms),mc)
    ref={k:np.sort(rawsc(TR,k)) for k in FX}
    refR=np.sort(np.maximum(rawsc(TR,"refrig_c1"),rawsc(TR,"refrig_c2")))
    def pit(df):
        r=np.maximum(rawsc(df,"refrig_c1"),rawsc(df,"refrig_c2")); p=rawsc(df,"power")
        Tr=np.searchsorted(refR,r,"right")/(len(refR)+1); Tp=np.searchsorted(ref["power"],p,"right")/(len(ref["power"])+1)
        return Tr,Tp,np.maximum(Tr,Tp),r,p
    out={"name":name,"n_train_minutes":int(len(TR)),"pit_max_attainable":round(len(refR)/(len(refR)+1),6)}
    trc,tpc,tsc,_,_=pit(CA); tau=cq(daymax(CA,tsc),ALPHA); out["tau_day"]=float(tau)
    out["cal_daymax_system"]=sorted([round(float(x),6) for x in daymax(CA,tsc)])
    res={}
    for lab,df in [("normal_test",TE),("fault",U)]:
        Tr,Tp,Ts,r,p=pit(df)
        res[lab]={"sys":daymax(df,Ts),"refrig":daymax(df,Tr),"power":daymax(df,Tp),"raw_refrig":daymax(df,r),"raw_power":daymax(df,p)}
        out[lab+"_n_days"]=int(len(res[lab]["sys"]))
        out[lab+"_frac_days_at_pit_ceiling"]=round(float((res[lab]["sys"]>=len(refR)/(len(refR)+1)-1e-12).mean()),3)
    out["AUC_daymax"]={k:round(auc(res["fault"][k],res["normal_test"][k]),3) for k in res["fault"]}
    # feature shifts in train-IQR units
    shifts={}
    for k,fx in FX.items():
        Xtr=np.asarray(fx(TR)); iqr=np.percentile(Xtr,75,0)-np.percentile(Xtr,25,0)+1e-9
        mt=np.median(np.asarray(fx(TE)),0); mf=np.median(np.asarray(fx(U)),0)
        for j,fnm in enumerate(FN[k]): shifts[fnm]=round(float((mf[j]-mt[j])/iqr[j]),3)
    out["median_shift_fault_vs_normaltest_in_trainIQR"]=shifts
    # post-hoc oracle curve on raw (un-saturated) system score: max of branch raw / train 99th pct
    s99r=np.percentile(np.maximum(rawsc(TR,"refrig_c1"),rawsc(TR,"refrig_c2")),99); s99p=np.percentile(rawsc(TR,"power"),99)
    nt=np.maximum(res["normal_test"]["raw_refrig"]/s99r,res["normal_test"]["raw_power"]/s99p)
    ft=np.maximum(res["fault"]["raw_refrig"]/s99r,res["fault"]["raw_power"]/s99p)
    curve=[]
    for th in np.unique(np.concatenate([nt,ft])):
        curve.append((float((nt>th).mean()),float((ft>th).mean())))
    best={}
    for far in (0.0,0.05,0.10,0.25):
        c=[s for f,s in curve if f<=far+1e-12]; best[f"sens_at_testFAR<={far}"]=round(max(c) if c else 0.0,3)
    out["POSTHOC_ORACLE_rawscore_daylevel"]=best
    out["AUC_daymax_raw_system"]=round(auc(ft,nt),3)
    return out
R=[run("Site1_Unfaulted.csv","Site1_Staging_Fault.csv",(19,19,13),"Site1 staging"),
   run("Site2_Unfaulted.csv","Site2_Undercharged40.csv",(88,44,44),"Site2 undercharge")]
with open(OUT/"e2_detectability.json","w") as fh: json.dump(R,fh,indent=1)
for r in R:
    print("=====",r["name"]); [print(k,":",v) for k,v in r.items() if k not in("name","cal_daymax_system")]
    print("cal day-max (lowest 5):",r["cal_daymax_system"][:5])

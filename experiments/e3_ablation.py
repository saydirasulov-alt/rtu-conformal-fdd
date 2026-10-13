"""E3: component ablation (field) + ORNL no-eligibility (imputation) comparison. Pre-registered.
One EXPLORATORY variant (A0x, tie-aware PIT extension) is added after E2 confirmed hypothesis H-sat;
it is labeled exploratory and is not a validated result."""
import sys,os,json,numpy as np,pandas as pd
CODE=os.path.join(os.path.dirname(__file__),"..","code"); sys.path.insert(0,CODE)
from _common import *
from pathlib import Path
OUT=Path(__file__).resolve().parent/"results"; OUT.mkdir(exist_ok=True)
ALPHA=0.05
def cq(s,a): n=len(s); k=min(int(np.ceil((1-a)*(n+1))),n)-1; return np.sort(s)[max(k,0)]
def daymax(df,sc): dd=days(df); return np.array([sc[dd==d].max() for d in np.unique(dd)])
def ev(sCA,sTE,sU,CA,TE,U):
    t=cq(daymax(CA,sCA),ALPHA); dn=daymax(TE,sTE); dfx=daymax(U,sU)
    return {"test_dayFAR":f"{int((dn>t).sum())}/{len(dn)}","fault_day_sens":f"{int((dfx>t).sum())}/{len(dfx)}",
            "fault_day_sens_pct":round(100*float((dfx>t).mean()),1),"fault_minute_sens_pct":round(100*float((sU>t).mean()),1),
            "threshold_reachable":bool(t< (sCA.max() if False else np.inf))}
R={"field":{}}
for Nf,Uf,sz,name in [("Site1_Unfaulted.csv","Site1_Staging_Fault.csv",(19,19,13),"Site1"),
                      ("Site2_Unfaulted.csv","Site2_Undercharged40.csv",(88,44,44),"Site2")]:
    N=load_field(Nf); U=load_field(Uf); dd=days(N); uq=np.unique(dd); a,b,_=sz
    TR=N[np.isin(dd,uq[:a])]; CA=N[np.isin(dd,uq[a:a+b])]; TE=N[np.isin(dd,uq[a+b:])]
    F,rc,pc=fit_on(TR)
    def raw(df):
        r=np.maximum(md(rz(F[0][0](df),F[0][1]),F[0][2]),md(rz(F[1][0](df),F[1][1]),F[1][2])); p=md(rz(F[2][0](df),F[2][1]),F[2][2]); return r,p
    rs,ps=np.sort(rc),np.sort(pc); n_r,n_p=len(rs),len(ps)
    o={}
    s={k:Tval(d,F,rc,pc) for k,d in [("CA",CA),("TE",TE),("U",U)]}
    t=cq(daymax(CA,s["CA"]),ALPHA)
    o["A0_proposed"]=ev(s["CA"],s["TE"],s["U"],CA,TE,U); o["A0_proposed"]["tau_day"]=float(t); o["A0_proposed"]["pit_ceiling"]=float(max(n_r/(n_r+1),n_p/(n_p+1)))
    o["A0_proposed"]["threshold_reachable"]=bool(t<max(n_r/(n_r+1),n_p/(n_p+1)))
    # A1 no PIT: max of raw branch Mahalanobis scores
    s={k:np.maximum(*raw(d)) for k,d in [("CA",CA),("TE",TE),("U",U)]}; o["A1_noPIT_rawmax"]=ev(s["CA"],s["TE"],s["U"],CA,TE,U)
    # A2 no branch structure = global Mahalanobis on 11 features (see E1 B1, rule C)
    X=lambda df: np.column_stack([cf(df,"_1"),cf(df,"_2"),pf(df)]); ms=rzfit(X(TR)); mc=mfit(rz(X(TR),ms))
    s={k:md(rz(X(d),ms),mc) for k,d in [("CA",CA),("TE",TE),("U",U)]}; o["A2_noBranches_globalMahal"]=ev(s["CA"],s["TE"],s["U"],CA,TE,U)
    # A3 minute calibration tau_min applied to proposed score
    s={k:Tval(d,F,rc,pc) for k,d in [("CA",CA),("TE",TE),("U",U)]}; tm=cq(s["CA"],ALPHA); dn=daymax(TE,s["TE"]); dfx=daymax(U,s["U"])
    o["A3_minuteCalibration"]={"test_dayFAR":f"{int((dn>tm).sum())}/{len(dn)}","test_minuteFAR_pct":round(100*float((s['TE']>tm).mean()),2),
        "fault_day_sens":f"{int((dfx>tm).sum())}/{len(dfx)}","fault_minute_sens_pct":round(100*float((s['U']>tm).mean()),1)}
    # A0x EXPLORATORY: tie-aware PIT extension beyond training max (strictly increasing, no tuning)
    def ext(x,ref):
        n=len(ref); T=np.searchsorted(ref,x,"right")/(n+1); m=ref[-1]; beyond=x>m
        T[beyond]=n/(n+1)+(1/(n+1))*(1-m/x[beyond]); return T
    def Tx(df): r,p=raw(df); return np.maximum(ext(r,rs),ext(p,ps))
    s={k:Tx(d) for k,d in [("CA",CA),("TE",TE),("U",U)]}; o["A0x_EXPLORATORY_tieawarePIT"]=ev(s["CA"],s["TE"],s["U"],CA,TE,U)
    for k in o: o[k].pop("threshold_reachable",None) if k!="A0_proposed" else None
    R["field"][name]=o
# ---------- ORNL: eligibility vs no-eligibility (median imputation) ----------
src=open(os.path.join(CODE,"ornl_sensor_unavailability.py")).read(); src=src[:src.index("rows=[]")]
ns={"__file__":os.path.join(CODE,"ornl_sensor_unavailability.py")}; exec(compile(src,"ornl_head","exec"),ns)
TR,CA,TE,BRANCH,SENS,PATTERNS,FAULTS,FA=[ns[k] for k in ("TR","CA","TE","BRANCH","SENS","PATTERNS","FAULTS","FA")]
eligible,bscore=ns["eligible"],ns["bscore"]
MED={s:float(TR[SENS[s]].median()) for s in SENS}
def impute(df,avail):
    d=df.copy()
    for s in SENS:
        if s not in avail: d[SENS[s]]=MED[s]
    return d
def fault_days(df,S,tau,elig):
    d,_=pd.factorize(df.dt.dt.floor("D")); B=np.column_stack([bscore(df,b) for b in S]); hit=0; unsup=0; n=0
    for i in np.unique(d):
        m=(d==i); TS=B[m].max(1); n+=1
        if TS.max()>tau:
            hit+=1; j=int(np.argmax(B[m].max(0)))
            if S[j] not in elig: unsup+=1
    return hit,unsup,n
rows=[]
for name,avail in PATTERNS.items():
    elig=eligible(avail); allb=list(BRANCH)
    row={"pattern":name,"eligible":elig}
    # no-eligibility variant: impute and score ALL branches
    CAi,TEi=impute(CA,avail),impute(TE,avail)
    TSca=np.column_stack([bscore(CAi,b) for b in allb]).max(1); tau=cq(TSca,ALPHA)
    TSte=np.column_stack([bscore(TEi,b) for b in allb]).max(1)
    row["noElig_minuteFAR"]=round(float((TSte>tau).mean()),3)
    det={}; tot_alarm=0; tot_unsup=0
    for fk,(pat,br) in FAULTS.items():
        h,u,n=fault_days(impute(FA[fk],avail),allb,tau,elig)
        det[fk]={"alarm_days":f"{h}/{n}","unsupported_alarm_days":u,"fault_branch_eligible":br in elig}
        tot_alarm+=h; tot_unsup+=u
    row["noElig_fault"]=det; row["noElig_unsupported_share_of_alarm_days"]=round(tot_unsup/max(tot_alarm,1),3)
    rows.append(row)
R["ornl_no_eligibility"]=rows
with open(OUT/"e3_ablation.json","w") as fh: json.dump(R,fh,indent=1)
for site,o in R["field"].items():
    print("=====",site)
    for k,v in o.items(): print(f"  {k:30s} {v}")
print("===== ORNL no-eligibility (imputation)")
for r in rows: print(" ",r["pattern"],"| elig",r["eligible"],"| minFAR",r["noElig_minuteFAR"],"| unsup share",r["noElig_unsupported_share_of_alarm_days"],"|",{k:(v["alarm_days"],v["unsupported_alarm_days"],v["fault_branch_eligible"]) for k,v in r["noElig_fault"].items()})

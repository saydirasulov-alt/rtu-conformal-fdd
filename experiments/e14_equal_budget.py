"""E14 (Amendments P2-A5, P2-A6): comparators under the frozen detector's exact two-statistic day rule,
and a condition-dependent physics charge indicator."""
import os,json,numpy as np
from pathlib import Path
import phase2_common as P
from e13_physics import identify,phys
A=P.A; OUT=Path(P.HERE)/"results"
class Dual:
    """daily max and daily mean of a minute score, each at alpha/2 on calibration days"""
    def __init__(self,f,CA):
        self.f=f; mx,mn=self._stats(CA); self.tau=(P.cq(mx,A.ALPHA/2),P.cq(mn,A.ALPHA/2))
    def _stats(self,X):
        s=self.f(X); return P.day_reduce(X["dt"],s,np.max),P.day_reduce(X["dt"],s,np.mean)
    def day_alarms(self,X):
        mx,mn=self._stats(X); return (mx>self.tau[0])|(mn>self.tau[1])
class PhysRes:
    """condition-dependent charge indicator on residuals of SH and SC"""
    def __init__(self,TR,CA,ref,pr):
        self.ref,self.pr=ref,pr; self.m={}
        for c in (1,2):
            on,SH,SC,_=phys(TR,c,ref,pr); m=on&np.isfinite(SH)&np.isfinite(SC); Xc=self._X(TR)[m]
            mu,sd=Xc.mean(0),Xc.std(0)+1e-9; Z=np.column_stack([np.ones(len(Xc)),(Xc-mu)/sd])
            W={k:np.linalg.solve(Z.T@Z+1e-3*np.eye(Z.shape[1]),Z.T@Y) for k,Y in (("SH",SH[m]),("SC",SC[m]))}
            rSH=SH[m]-Z@W["SH"]; rSC=SC[m]-Z@W["SC"]
            q=lambda v:(np.median(v),np.percentile(v,75)-np.percentile(v,25)+1e-9)
            self.m[c]=(mu,sd,W,q(rSH),q(rSC))
        mx,mn=self.day_stats(CA); self.tau=(P.cq(mx[np.isfinite(mx)],A.ALPHA/2),P.cq(mn[np.isfinite(mn)],A.ALPHA/2))
    def _X(self,df): return np.column_stack([df.RTU_OA_TEMP.values,df.RTU_RA_TEMP.values,df.RTU_COMP_WATT.values])
    def minute(self,df):
        CI=np.full(len(df),-np.inf); X=self._X(df)
        for c in (1,2):
            on,SH,SC,_=phys(df,c,self.ref,self.pr); m=on&np.isfinite(SH)&np.isfinite(SC); mu,sd,W,(ms,ss),(mc,sc)=self.m[c]
            Z=np.column_stack([np.ones(len(X)),(X-mu)/sd]); ci=((SH-Z@W["SH"])-ms)/ss-((SC-Z@W["SC"])-mc)/sc
            CI=np.maximum(CI,np.where(m,ci,-np.inf))
        return CI
    def day_stats(self,df):
        CI=self.minute(df); dd=df.dt.dt.floor("D"); mx=[];mn=[]
        for i in np.unique(dd):
            v=CI[(dd==i).values]; v=v[np.isfinite(v)]; mx.append(v.max() if len(v) else np.nan); mn.append(v.mean() if len(v) else np.nan)
        return np.array(mx),np.array(mn)
    def day_alarms_df(self,df):
        mx,mn=self.day_stats(df); return (np.nan_to_num(mx,nan=-np.inf)>self.tau[0])|(np.nan_to_num(mn,nan=-np.inf)>self.tau[1])
R={}
for s in P.SITES:
    TR,CA,TE,U=P.site(s); TRd,CAd,TEd,Ud=map(P.to_dict,(TR,CA,TE,U))
    v2=P.Detector("S0","Ddual",True).fit(TRd,CAd); vte,vu=v2.day_alarms(TEd),v2.day_alarms(Ud)
    det={k:Dual(f,CAd) for k,f in P.baseline_scores(TRd).items()}
    det["v1_tieaware_dual_rule"]=P.Detector("S0","Ddual",False).fit(TRd,CAd)
    al={k:(d.day_alarms(TEd),d.day_alarms(Ud)) for k,d in det.items()}
    _,sel=identify(TR); ph=PhysRes(TR,CA,sel["refrigerant"],sel["pressure"]); al["physics_condition_dependent_dual_rule"]=(ph.day_alarms_df(TE),ph.day_alarms_df(U))
    rows={}; pf=[]
    for k,(a,b) in al.items():
        f=P.mcnemar(vu,b); pf.append(f[2]); rows[k]={"test_dayFAR":P.frac(a),"fault_day_sens":P.frac(b),"fault_days_v2_only":f[0],"fault_days_comp_only":f[1],"p_exact":float(f"{f[2]:.3g}"),
               "normal_days_mcnemar_p":float(f"{P.mcnemar(vte,a)[2]:.3g}")}
    for k,h in zip(al,P.holm(pf)): rows[k]["p_holm"]=float(f"{h:.3g}")
    R[s]={"frozen":{"test_dayFAR":P.frac(vte),"fault_day_sens":P.frac(vu)},"comparators_dual_rule":rows}
    print("=====",s,"frozen",R[s]["frozen"])
    for k,v in rows.items(): print(f"  {k:40s} FAR {v['test_dayFAR']:>5s} sens {v['fault_day_sens']:>5s} +{v['fault_days_v2_only']}/-{v['fault_days_comp_only']} p_holm={v['p_holm']}")
# simulated holdout: v1 tie-aware with the dual rule (no joint branch) vs frozen
SIM=os.environ.get("RTU_SIM_DIR")
if SIM:
    HOLD=["evapfouling10","evapfouling20","evapfouling30","evapfouling40","evapfouling50","suctionpipe01bar","suctionpipe03bar","suctionpipe06bar","suctionpipe09bar","undercharge10","undercharge15","undercharge20"]
    B=A.load_sim(os.path.join(SIM,"RTU_sim_baseline.csv")); (TR,CA,TE),u=A.split_days(B,50,25); td=u[75:]
    out={}
    for name,cfg in (("frozen",("S0","Ddual",True)),("v1_tieaware_dual_rule",("S0","Ddual",False))):
        d=P.Detector(*cfg).fit(TR,CA); sens=[]
        for k in HOLD:
            F=A.load_sim(os.path.join(SIM,f"RTU_sim_{k}.csv")); F=A.subset(F,np.isin(A.dayid(F["dt"]),td)); sens.append(d.day_alarms(F).mean())
        out[name]={"baseline_test_dayFAR":P.frac(d.day_alarms(TE)),"holdout_mean_sens_pct":round(100*float(np.mean(sens)),1)}
    R["sim_holdout"]=out; print("sim",out)
with open(OUT/"e14_equal_budget.json","w") as fh: json.dump(R,fh,indent=1)

"""E13: physics-based charge-indicator baseline (ANALYSIS_PLAN_PHASE2.md). Refrigerant and pressure reference are
identified by the pre-specified plausibility rule on TRAINING data only; then two detectors are evaluated."""
import json,numpy as np
from pathlib import Path
import phase2_common as P
from CoolProp.CoolProp import PropsSI
OUT=Path(P.HERE)/"results"
REFS=["R22","R410A","R407C"]; PREF={"gauge":1.01325,"absolute":0.0}
def tsat_table(ref,q):
    p=np.linspace(0.5,45,4000)*1e5; t=np.array([PropsSI("T","P",x,"Q",q,ref) for x in p])-273.15; return p/1e5,t
TAB={(r,q):tsat_table(r,q) for r in REFS for q in (0,1)}
def tsat(ref,q,pbar_abs): pp,tt=TAB[(ref,q)]; return np.interp(pbar_abs,pp,tt,left=np.nan,right=np.nan)
def phys(df,c,ref,pr):
    pd_=df[f"RTU_REFG_DISC_PRES_{c}"].values+PREF[pr]; ps=df[f"RTU_REFG_SUCT_PRES_{c}"].values+PREF[pr]
    on=(df[f"RTU_REFG_DISC_PRES_{c}"].values-df[f"RTU_REFG_SUCT_PRES_{c}"].values)>3.0
    SH=df[f"RTU_REFG_SUCT_TEMP_{c}"].values-tsat(ref,1,ps); SC=tsat(ref,0,pd_)-df[f"RTU_REFG_COND_TEMP_{c}"].values
    AP=tsat(ref,0,pd_)-df.RTU_OA_TEMP.values; return on,SH,SC,AP
def identify(TR):
    rows=[]
    for ref in REFS:
        for pr in PREF:
            r={"refrigerant":ref,"pressure":pr,"circuits":{}}; ok=True; neg=0.0
            for c in (1,2):
                on,SH,SC,AP=phys(TR,c,ref,pr); m=on&np.isfinite(SH)&np.isfinite(SC)
                if m.sum()<100: r["circuits"][c]={"n_on":int(m.sum())}; ok=False; continue
                st={"n_on":int(m.sum()),"SH_med":round(float(np.median(SH[m])),2),"SC_med":round(float(np.median(SC[m])),2),
                    "approach_med":round(float(np.median(AP[m])),2),"frac_SH_neg":round(float((SH[m]<0).mean()),4),"frac_SC_neg":round(float((SC[m]<0).mean()),4)}
                st["plausible"]=bool(2<=st["SH_med"]<=25 and 0<=st["SC_med"]<=20 and 3<=st["approach_med"]<=30 and st["frac_SH_neg"]<0.05)
                ok&=st["plausible"]; neg+=st["frac_SH_neg"]+st["frac_SC_neg"]; r["circuits"][c]=st
            r["plausible_both"]=bool(ok); r["neg_sum"]=round(neg,4); rows.append(r)
    pl=[r for r in rows if r["plausible_both"]]
    sel=min(pl,key=lambda r:r["neg_sum"]) if pl else None
    return rows,sel
class Physics:
    def __init__(self,TR,CA,ref,pr):
        self.ref,self.pr=ref,pr; self.z={}
        for c in (1,2):
            on,SH,SC,_=phys(TR,c,ref,pr); m=on&np.isfinite(SH)&np.isfinite(SC)
            q=lambda v:(np.median(v[m]),np.percentile(v[m],75)-np.percentile(v[m],25)+1e-9)
            self.z[c]=(q(SH),q(SC),np.percentile(SH[m],99),np.percentile(SC[m],1))
        mx,mn=self.day_stats(CA); a=P.A.ALPHA/2; self.tau=(P.cq(mx[np.isfinite(mx)],a),P.cq(mn[np.isfinite(mn)],a))
    def minute(self,df):
        CI=np.full(len(df),-np.inf); rule=np.zeros(len(df),bool)
        for c in (1,2):
            on,SH,SC,_=phys(df,c,self.ref,self.pr); m=on&np.isfinite(SH)&np.isfinite(SC); (ms,ss),(mc,sc),p99,p1=self.z[c]
            ci=np.where(m,(SH-ms)/ss-(SC-mc)/sc,-np.inf); CI=np.maximum(CI,ci); rule|=m&(SH>p99)&(SC<p1)
        return CI,rule
    def day_stats(self,df):
        CI,_=self.minute(df); dd=df.dt.dt.floor("D"); mx=[];mn=[]
        for i in np.unique(dd):
            v=CI[(dd==i).values]; v=v[np.isfinite(v)]; mx.append(v.max() if len(v) else np.nan); mn.append(v.mean() if len(v) else np.nan)
        return np.array(mx),np.array(mn)
    def day_alarms_df(self,df):
        mx,mn=self.day_stats(df)
        return (np.nan_to_num(mx,nan=-np.inf)>self.tau[0])|(np.nan_to_num(mn,nan=-np.inf)>self.tau[1])
    def rule_alarms_df(self,df):
        _,r=self.minute(df); dd=df.dt.dt.floor("D"); return np.array([r[(dd==i).values].any() for i in np.unique(dd)])
if __name__=="__main__":
    R={}
    for s in P.SITES:
        TR,CA,TE,U=P.site(s); rows,sel=identify(TR); R[s]={"identification":rows,"selected":None if sel is None else {"refrigerant":sel["refrigerant"],"pressure":sel["pressure"]}}
        if sel is None: print(s,"physics baseline NOT identifiable"); continue
        ph=Physics(TR,CA,sel["refrigerant"],sel["pressure"])
        R[s]["conformal_CI"]={"test_dayFAR":P.frac(ph.day_alarms_df(TE)),"FAR_CI95":P.cp(int(ph.day_alarms_df(TE).sum()),len(ph.day_alarms_df(TE))),
                             "fault_day_sens":P.frac(ph.day_alarms_df(U)),"sens_CI95":P.cp(int(ph.day_alarms_df(U).sum()),len(ph.day_alarms_df(U)))}
        R[s]["conventional_rule"]={"test_dayFAR":P.frac(ph.rule_alarms_df(TE)),"fault_day_sens":P.frac(ph.rule_alarms_df(U))}
        # descriptive: median SH/SC on fault vs normal test minutes, per circuit
        desc={}
        for c in (1,2):
            for nm,df in (("normal_test",TE),("fault",U)):
                on,SH,SC,_=phys(df,c,sel["refrigerant"],sel["pressure"]); m=on&np.isfinite(SH)&np.isfinite(SC)
                desc[f"c{c}_{nm}"]={"on_minute_frac":round(float(on.mean()),3),"SH_med":round(float(np.median(SH[m])),2) if m.any() else None,"SC_med":round(float(np.median(SC[m])),2) if m.any() else None}
        R[s]["descriptive"]=desc
        # Amendment P2-A1: all plausible hypotheses
        alt={}
        for r in rows:
            if not r["plausible_both"]: continue
            pa=Physics(TR,CA,r["refrigerant"],r["pressure"]); a1=pa.day_alarms_df(TE); a2=pa.day_alarms_df(U); b1=pa.rule_alarms_df(TE); b2=pa.rule_alarms_df(U)
            alt[f'{r["refrigerant"]}_{r["pressure"]}']={"conformal":[P.frac(a1),P.frac(a2)],"rule":[P.frac(b1),P.frac(b2)]}
        R[s]["all_plausible_hypotheses"]=alt; print("  A1:",alt)
        print(s,R[s]["selected"],"conformal",R[s]["conformal_CI"],"rule",R[s]["conventional_rule"]); print("  ",desc)
    for s in R:
        for r in R[s]["identification"]: print(s,r["refrigerant"],r["pressure"],r["plausible_both"],{c:{k:v for k,v in d.items() if k!='n_on'} for c,d in r["circuits"].items()})
    with open(OUT/"e13_physics.json","w") as fh: json.dump(R,fh,indent=1)

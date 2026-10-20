"""E15 (Amendment P2-A10): audit-response sensitivity and diagnostic analyses.
Pre-specified in ANALYSIS_PLAN_PHASE2.md (A10.1-A10.8) before computation. Nothing here changes the frozen detector."""
import os,json,numpy as np
from pathlib import Path
from scipy.signal import lfilter
from scipy.stats import binomtest
import phase2_common as P
from e9_attribution import attribute
from e12_injection import scenarios,inject
from e14_equal_budget import Dual
A=P.A; OUT=Path(P.HERE)/"results"; SEED=20261020
SIM=os.environ.get("RTU_SIM_DIR"); assert SIM,"set RTU_SIM_DIR"
HOLD=["evapfouling10","evapfouling20","evapfouling30","evapfouling40","evapfouling50","suctionpipe01bar","suctionpipe03bar","suctionpipe06bar","suctionpipe09bar","undercharge10","undercharge15","undercharge20"]
def seq(a): return "".join("1" if x else "0" for x in a)
def ttype(x): return float(f"{x:.3g}")
# ---------------- A10.1 ----------------
def lag1(a):
    a=np.asarray(a,float)
    if len(a)<3 or a[:-1].std()==0 or a[1:].std()==0: return 0.0
    return float(np.corrcoef(a[:-1],a[1:])[0,1])
def runs(a):
    r=[];c=0
    for x in a:
        if x: c+=1
        elif c: r.append(c); c=0
    if c: r.append(c)
    return {"n_runs":len(r),"mean_run":round(float(np.mean(r)),2) if r else 0.0}
def neff(a):
    r=min(max(lag1(a),0.0),0.95); return round(len(a)*(1-r)/(1+r),1)
def cbb_idx(n,L,rng):
    k=int(np.ceil(n/L)); st=rng.integers(0,n,k); return np.concatenate([(s+np.arange(L))%n for s in st])[:n]
def boot(seqs,L,B=5000,rng=None):
    """seqs: list of equal-length bool arrays resampled with the same indices; returns array B x len(seqs) of means"""
    n=len(seqs[0]); S=np.array(seqs,float); out=np.empty((B,len(seqs)))
    for b in range(B): out[b]=S[:,cbb_idx(n,L,rng)].mean(1)
    return out
def pci(v): return [round(100*float(np.percentile(v,2.5)),1),round(100*float(np.percentile(v,97.5)),1)]
def a10_1(site,TRd,CAd,TEd,Ud):
    v2=P.GDetector().fit(TRd,CAd); det={"frozen":v2}
    det.update({k:Dual(f,CAd) for k,f in P.baseline_scores(TRd).items()})
    det["v1_tieaware_dual_rule"]=P.Detector("S0","Ddual",False).fit(TRd,CAd)
    al={k:(d.day_alarms(TEd),d.day_alarms(Ud)) for k,d in det.items()}
    R={}
    for k,(a,b) in al.items():
        R[k]={"test_dayFAR":P.frac(a),"fault_day_sens":P.frac(b),
              "fault":{"lag1":round(lag1(b),3),"n_eff":neff(b),**runs(b)},"normal":{"lag1":round(lag1(a),3),"n_eff":neff(a),**runs(a)}}
        for L in (3,7):
            rng=np.random.default_rng(SEED)
            R[k][f"block{L}_FAR_CI95"]=pci(boot([a],L,rng=rng)[:,0])
            rng=np.random.default_rng(SEED)
            R[k][f"block{L}_sens_CI95"]=pci(boot([b],L,rng=rng)[:,0])
            if k!="frozen":
                rng=np.random.default_rng(SEED); bb=boot([al["frozen"][1],b],L,rng=rng)
                R[k][f"block{L}_sens_diff_frozen_minus_comp_CI95"]=pci(bb[:,0]-bb[:,1])
        R[k]["cp_sens_CI95"]=P.cp(int(b.sum()),len(b)); R[k]["cp_FAR_CI95"]=P.cp(int(a.sum()),len(a))
    return R
# ---------------- A10.2 ----------------
def circ_of(rec):
    s=rec["stat"][0] if len(rec["stat"])==1 else "max"; return rec[f"circuit_{s}"]
def mirror(TR):
    out=[]
    for name,col,kind,v in scenarios(TR):
        if not col.startswith("RTU_REFG"): continue
        out.append((name,col,kind,v,1))
        c2=col[:-1]+"2"; iqr1=float(np.percentile(TR[col],75)-np.percentile(TR[col],25)); iqr2=float(np.percentile(TR[c2],75)-np.percentile(TR[c2],25))
        v2=None if v is None else v/iqr1*iqr2
        out.append((name.replace("_T1","_T2"),c2,kind,v2,2))
    return out
def a10_2(site,TR,CA,TE,U):
    det=P.GDetector().fit(P.to_dict(TR),P.to_dict(CA))
    rf=[r for r in attribute(det,P.to_dict(U)) if r]; c2=sum(circ_of(r)==2 for r in rf); n=len(rf)
    field={"fault_alarm_days":n,"attributed_circuit2":c2,"always_circuit2_agreement":f"{n}/{n}",
           "binom_vs_half_p_one_sided":ttype(binomtest(c2,n,0.5,alternative="greater").pvalue) if n else None}
    clean=det.day_alarms(P.to_dict(TE)); rows={}; tot={1:[0,0],2:[0,0]}
    for name,col,kind,v,ic in mirror(TR):
        Ti=inject(TE,col,kind,v); X=P.to_dict(Ti); a=det.day_alarms(X); recs=attribute(det,X)
        new=[recs[i] for i in range(len(a)) if a[i] and not clean[i]]; hit=sum(circ_of(r)==ic for r in new)
        rows[name]={"injected_circuit":ic,"new_alarm_days":len(new),"attributed_to_injected":hit}
        tot[ic][0]+=hit; tot[ic][1]+=len(new)
    acc={c:(round(100*tot[c][0]/tot[c][1],1) if tot[c][1] else None) for c in (1,2)}
    bal=round(float(np.mean([acc[1],acc[2]])),1) if None not in acc.values() else None
    return {"field_fault_days":field,"injected":{"pooled":{f"circuit{c}":f"{tot[c][0]}/{tot[c][1]}" for c in (1,2)},
            "pct_to_injected":acc,"balanced_accuracy_pct":bal,"always_circuit2_balanced_accuracy_pct":50.0,"scenarios":rows}}
# ---------------- A10.3 ----------------
def a10_3():
    B=A.load_sim(os.path.join(SIM,"RTU_sim_baseline.csv")); (TR30,CA20,REST),u=A.split_days(B,30,20)
    blk=A.subset(B,np.isin(A.dayid(B["dt"]),u[50:75]))
    grid=json.load(open(OUT/"algo_v2_dev_grid.json")); rows=[]
    for r in grid:
        det=A.Detector(r["S"],r["D"],r["J"]).fit(TR30,CA20); fa=det.day_alarms(blk)
        rows.append({**{k:r[k] for k in ("S","D","J","dev_mean_sens","baseline_test_dayFAR")},"admissibility_FAR_days51_75":P.frac(fa)})
    order={"S0":0,"S1":1,"S2":2,"S3":3,"Dmax":0,"Dmean":1,"Ddual":2}
    adm=[r for r in rows if int(r["admissibility_FAR_days51_75"].split("/")[0])<=3]
    best=max(r["dev_mean_sens"] for r in adm); c=[r for r in adm if r["dev_mean_sens"]>=best-1.0]
    sel=sorted(c,key=lambda r:(order[r["S"]],order[r["D"]],int(r["J"])))[0]
    fz=json.load(open(OUT/"algo_v2_FROZEN.json"))
    return {"selected":{k:sel[k] for k in ("S","D","J","dev_mean_sens")},"frozen":{k:fz[k] for k in ("S","D","J")},
            "same_as_frozen":bool((sel["S"],sel["D"],sel["J"])==(fz["S"],fz["D"],fz["J"])),"n_admissible":len(adm),"grid":rows}
# ---------------- helpers for sim ----------------
def sim_sets(trim=False):
    B=A.load_sim(os.path.join(SIM,"RTU_sim_baseline.csv")); (TR,CA,TE),u=A.split_days(B,50,25); td=u[75:]
    FH={k:A.subset(F,np.isin(A.dayid(F["dt"]),td)) for k,F in ((k,A.load_sim(os.path.join(SIM,f"RTU_sim_{k}.csv"))) for k in HOLD)}
    if trim: TR,CA,TE=map(trimD,(TR,CA,TE)); FH={k:trimD(v) for k,v in FH.items()}
    return TR,CA,TE,FH
def sim_eval(det,TE,FH):
    return {"baseline_test_dayFAR":P.frac(det.day_alarms(TE)),"holdout_mean_sens_pct":round(100*float(np.mean([det.day_alarms(v).mean() for v in FH.values()])),1)}
def field_eval(det,TE,U): return {"test_dayFAR":P.frac(det.day_alarms(TE)),"fault_day_sens":P.frac(det.day_alarms(U))}
# ---------------- A10.4 ----------------
def trimD(X):
    Y=dict(X); Y["circ"]=[{"T":c["T"][:,:3],"P":c["P"]} for c in X["circ"]]; return Y
def eig3(det,TR):
    out={}
    for key,mats in det._blocks(TR).items():
        for j,Y in enumerate(mats):
            med=np.median(Y,0); iqr=np.percentile(Y,75,0)-np.percentile(Y,25,0)+1e-9; w=np.linalg.eigvalsh(np.cov(((Y-med)/iqr).T))
            out[f"{key}{j}"]=[float(f"{x:.3g}") for x in np.sort(w)[:3]]
    return out
# ---------------- A10.5 ----------------
class Persist:
    def __init__(self,d): self.d=d
    def day_alarms(self,X):
        a=self.d.day_alarms(X); return a&np.concatenate([[False],a[:-1]])
class EWMA:
    def __init__(self,f,TR,CA,lam=0.02):
        self.f,self.lam=f,lam; self.z0=float(np.median(f(TR))); self.tau=P.cq(self._dmax(CA),A.ALPHA)
    def _dmax(self,X):
        s=self.f(X); dd=A.dayid(X["dt"]); out=[]
        for i in np.unique(dd):
            v=s[dd==i]; z,_=lfilter([self.lam],[1,-(1-self.lam)],v,zi=[(1-self.lam)*self.z0]); out.append(z.max())
        return np.array(out)
    def day_alarms(self,X): return self._dmax(X)>self.tau
# ---------------- A10.6 ----------------
def drop_mask(X,mode,level,rng):
    dt=X["dt"]; dd=A.dayid(dt); m=np.zeros(len(dt),bool)
    for i in np.unique(dd):
        idx=np.where(dd==i)[0]
        if mode=="random": m[idx]=rng.random(len(idx))<level
        else:
            st=pd_ts(i)+np.timedelta64(int(rng.uniform(0,18*3600)),"s"); t=dt.values[idx]
            m[idx]=(t>=st)&(t<st+np.timedelta64(int(level*3600),"s"))
    return m
def pd_ts(i): return np.datetime64(i)
def intermittent_day_alarms(full,red,X,miss):
    """day-pattern rule of A10.6. Returns alarms, abstentions, pattern per day."""
    dd=A.dayid(X["dt"]); u=np.unique(dd); alarm=np.zeros(len(u),bool); abst=np.zeros(len(u),bool); pat=[]
    sf=full.minute_scores(X); sr=red.minute_scores(X)
    for j,i in enumerate(u):
        m=dd==i; pres=m&~miss
        if pres.sum()>=0.5*m.sum():
            v=sf[pres]; d=full; pat.append("full")
        else:
            v=sr[m]; d=red; pat.append("reduced")
        if len(v)<60: abst[j]=True; continue
        alarm[j]=(v.max()>d.tau["max"])|(v.mean()>d.tau["mean"])
    return alarm,abst,pat
def a10_6(TRd,CAd,TEd,Ud):
    full=P.GDetector().fit(TRd,CAd)
    red={"circuit2":P.GDetector(circ=(0,),power=True).fit(TRd,CAd),"power":P.GDetector(circ=(0,1),power=False).fit(TRd,CAd)}
    R={"no_loss":field_eval(full,TEd,Ud)}
    for grp,rd in red.items():
        R[f"{grp}_permanent_loss"]=field_eval(rd,TEd,Ud)
        for mode,level in (("random",0.10),("random",0.40),("outage_h",6)):
            rng=np.random.default_rng(SEED); out={}
            for nm,X in (("test",TEd),("fault",Ud)):
                miss=drop_mask(X,mode,level,rng); a,ab,pat=intermittent_day_alarms(full,rd,X,miss)
                out[nm]={"alarm_days":f"{int(a.sum())}/{len(a)}","abstain_days":int(ab.sum()),"days_scored_full_pattern":pat.count("full")}
            out["alarms_on_missing_sensors"]=0  # by construction: full-pattern statistics use only minutes with the group present
            R[f"{grp}_{mode}_{level}"]=out
    return R
# ---------------- A10.7 ----------------
class JointStat:
    def __init__(self,base,TR,CA):
        self.b=base; mx,mn,_=base.day_stats(TR); self.c=(float(np.median(mx)),float(np.median(mn)))
        j=self._J(CA); n=len(j); self.k=min(int(np.ceil((n+1)*(1-A.ALPHA))),n); self.tau=np.sort(j)[self.k-1]; self.bound=round(100*(n+1-self.k)/(n+1),1)
    def _J(self,X): mx,mn,_=self.b.day_stats(X); return np.maximum(mx/self.c[0],mn/self.c[1])
    def day_alarms(self,X): return self._J(X)>self.tau
# ---------------- A10.8 ----------------
class ExpTail(P.GDetector):
    def _pit(self,x,ref):
        n=len(ref); T=np.searchsorted(ref,x,"right")/(n+1); m=ref[-1]; b=x>m
        T[b]=n/(n+1)+(1/(n+1))*(1-np.exp(-(x[b]-m)/m)); return T
# ---------------- main ----------------
if __name__=="__main__":
    R={"A10_1":{},"A10_2":{},"A10_4":{},"A10_5":{},"A10_6":{},"A10_7":{},"A10_8":{}}
    for s in P.SITES:
        TR,CA,TE,U=P.site(s); TRd,CAd,TEd,Ud=map(P.to_dict,(TR,CA,TE,U))
        R["A10_1"][s]=a10_1(s,TRd,CAd,TEd,Ud); print(s,"A10.1 done")
        R["A10_2"][s]=a10_2(s,TR,CA,TE,U); print(s,"A10.2",R["A10_2"][s]["field_fault_days"],R["A10_2"][s]["injected"]["pooled"],R["A10_2"][s]["injected"]["balanced_accuracy_pct"])
        t=list(map(trimD,(TRd,CAd,TEd,Ud))); r4={}
        for lam in (1e-4,1e-3,1e-2):
            d=P.GDetector(ridge=lam).fit(t[0],t[1]); r4[f"{lam:g}"]={**field_eval(d,t[2],t[3]),"smallest_eigs":eig3(d,t[0])}
        R["A10_4"][s]=r4; print(s,"A10.4",{k:(v["test_dayFAR"],v["fault_day_sens"]) for k,v in r4.items()})
        v2=P.GDetector().fit(TRd,CAd); mh=P.baseline_scores(TRd)["global_Mahalanobis"]
        r5={"frozen_dual":field_eval(v2,TEd,Ud),
            "frozen_max_only":field_eval(P.Detector("S0","Dmax",True).fit(TRd,CAd),TEd,Ud),
            "frozen_mean_only":field_eval(P.Detector("S0","Dmean",True).fit(TRd,CAd),TEd,Ud),
            "frozen_persistence2":field_eval(Persist(v2),TEd,Ud),
            "mahalanobis_dual":field_eval(Dual(mh,CAd),TEd,Ud),
            "mahalanobis_persistence2":field_eval(Persist(Dual(mh,CAd)),TEd,Ud),
            "frozen_EWMA_dailymax":field_eval(EWMA(v2.minute_scores,TRd,CAd),TEd,Ud),
            "mahalanobis_EWMA_dailymax":field_eval(EWMA(mh,TRd,CAd),TEd,Ud)}
        R["A10_5"][s]=r5; print(s,"A10.5",r5)
        R["A10_6"][s]=a10_6(TRd,CAd,TEd,Ud); print(s,"A10.6",R["A10_6"][s])
        js=JointStat(v2,TRd,CAd); R["A10_7"][s]={**field_eval(js,TEd,Ud),"k":js.k,"n_cal":len(np.unique(A.dayid(CAd["dt"]))),"effective_bound_pct":js.bound,"c":[round(x,4) for x in js.c]}
        print(s,"A10.7",R["A10_7"][s])
        R["A10_8"][s]=field_eval(ExpTail().fit(TRd,CAd),TEd,Ud); print(s,"A10.8",R["A10_8"][s])
    R["A10_3"]=a10_3(); print("A10.3",R["A10_3"]["selected"],R["A10_3"]["same_as_frozen"],R["A10_3"]["n_admissible"])
    TR,CA,TE,FH=sim_sets(); v2=P.GDetector().fit(TR,CA)
    R["A10_7"]["sim_holdout"]=sim_eval(JointStat(v2,TR,CA),TE,FH); R["A10_8"]["sim_holdout"]=sim_eval(ExpTail().fit(TR,CA),TE,FH)
    R["A10_7"]["sim_holdout_frozen_reference"]=sim_eval(v2,TE,FH)
    TRt,CAt,TEt,FHt=sim_sets(trim=True); R["A10_4"]["sim_holdout"]={f"{lam:g}":sim_eval(P.GDetector(ridge=lam).fit(TRt,CAt),TEt,FHt) for lam in (1e-4,1e-3,1e-2)}
    print("sim",R["A10_7"]["sim_holdout"],R["A10_8"]["sim_holdout"],R["A10_4"]["sim_holdout"])
    with open(OUT/"e15_audit_response.json","w") as fh: json.dump(R,fh,indent=1)

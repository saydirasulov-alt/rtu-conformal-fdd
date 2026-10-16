"""Shared helpers for Phase 2 (ANALYSIS_PLAN_PHASE2.md). The frozen v2 detector is imported unchanged
from algo_v2.py; GDetector only generalises branch availability and ridge, and with defaults it is
numerically identical to Detector("S0","Ddual",True) (checked in self_check())."""
import os,sys,numpy as np,pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,"..","code"))
import algo_v2 as A
from algo_v2 import Detector,dayid,cq
from sklearn.ensemble import IsolationForest
from scipy.stats import beta,binomtest
SEED=20260618
D=os.environ.get("RTU_DATA_DIR"); assert D,"set RTU_DATA_DIR"
SITES={"Site1":("Site1_Unfaulted.csv","Site1_Staging_Fault.csv",(19,19)),
       "Site2":("Site2_Unfaulted.csv","Site2_Undercharged40.csv",(88,44))}
COLS=["Datetime","RTU_COMP_WATT","RTU_TOT_WATT","RTU_SA_FAN_WATT","RTU_OA_TEMP","RTU_RA_TEMP"]+\
     [f"RTU_REFG_{a}_{c}" for a in ("COND_TEMP","DISC_TEMP","SUCT_TEMP","DISC_PRES","SUCT_PRES") for c in (1,2)]
def load_df(fname):
    """Same rows as algo_v2.load_field (gate on uncorrupted compressor power), returned as a DataFrame."""
    d=pd.read_csv(os.path.join(D,"Field RTU",fname),usecols=COLS); d["dt"]=pd.to_datetime(d.Datetime)
    return d[d.RTU_COMP_WATT>A.GATE].dropna().sort_values("dt").reset_index(drop=True)
def to_dict(d):
    circ=[]
    for c in (1,2):
        T=np.column_stack([d[f"RTU_REFG_COND_TEMP_{c}"],d[f"RTU_REFG_DISC_TEMP_{c}"],d[f"RTU_REFG_SUCT_TEMP_{c}"],d[f"RTU_REFG_DISC_TEMP_{c}"]-d[f"RTU_REFG_SUCT_TEMP_{c}"]])
        circ.append({"T":T,"P":np.column_stack([d[f"RTU_REFG_DISC_PRES_{c}"],d[f"RTU_REFG_SUCT_PRES_{c}"]])})
    return {"dt":d["dt"].reset_index(drop=True),"OA":d.RTU_OA_TEMP.values,"RA":d.RTU_RA_TEMP.values,"circ":circ,
            "power":np.column_stack([d.RTU_COMP_WATT,d.RTU_TOT_WATT,d.RTU_SA_FAN_WATT])}
def split_df(d,a,b):
    dd=d.dt.dt.floor("D"); u=np.unique(dd)
    return d[dd.isin(u[:a])].reset_index(drop=True),d[dd.isin(u[a:a+b])].reset_index(drop=True),d[dd.isin(u[a+b:])].reset_index(drop=True)
def site(name):
    nf,uf,(a,b)=SITES[name]; N=load_df(nf); U=load_df(uf); TR,CA,TE=split_df(N,a,b); return TR,CA,TE,U
class GDetector(Detector):
    """S0 feature set; circ = available refrigerant circuits (0-based), power = power sensors available,
    joint branch eligible only when both circuits and power are available."""
    def __init__(self,D="Ddual",J=True,ridge=1e-3,circ=None,power=True):
        super().__init__("S0",D,J); self.ridge=ridge; self.circ_req=None if circ is None else tuple(circ); self.pw=power
    def _cset(self,X): return tuple(range(len(X["circ"]))) if self.circ_req is None else self.circ_req
    def _blocks(self,X):
        B={}; cs=self._cset(X); self.circ=cs; allc=cs==tuple(range(len(X["circ"])))
        if cs: B["refrig"]=[X["circ"][c]["T"] for c in cs]
        if self.pw: B["power"]=[X["power"]]
        if self.J and allc and self.pw: B["joint"]=[np.column_stack([X["circ"][c]["T"] for c in cs]+[X["power"]])]
        return B
    def _raw(self,X,fit=False):
        out={}
        for key,mats in self._blocks(X).items():
            sc=[]
            for j,Y in enumerate(mats):
                if fit:
                    med=np.median(Y,0); iqr=np.percentile(Y,75,0)-np.percentile(Y,25,0)+1e-9; Z=(Y-med)/iqr
                    C=np.cov(Z.T)+self.ridge*np.eye(Z.shape[1]); self.m[(key,j)]=(med,iqr,Z.mean(0),np.linalg.pinv(C))
                med,iqr,mu,Ci=self.m[(key,j)]; E=(Y-med)/iqr-mu; sc.append(np.einsum("ij,jk,ik->i",E,Ci,E))
            out[key]=np.max(np.column_stack(sc),1)
        return out
    def fit(self,TR,CA):
        super().fit(TR,CA); self.circ=self._cset(TR)
        # per-circuit training references for attribution (E9); not used for alarms
        self.cref={j:np.sort(self._circ_raw(TR,j)) for j in range(len(self.circ))}
        return self
    def _circ_raw(self,X,j):
        Y=X["circ"][self.circ[j]]["T"]; med,iqr,mu,Ci=self.m[("refrig",j)]; E=(Y-med)/iqr-mu; return np.einsum("ij,jk,ik->i",E,Ci,E)
    def branch_T(self,X):
        raw=self._raw(X); return {k:self._pit(raw[k],self.ref[k]) for k in raw}
    def circuit_T(self,X):
        return {self.circ[j]+1:self._pit(self._circ_raw(X,j),self.cref[j]) for j in range(len(self.circ))}
def day_reduce(dt,s,f):
    dd=dayid(dt); return np.array([f(s[dd==i]) for i in np.unique(dd)])
# ---- comparators (all rule C: day-max conformal threshold, alpha) ----
def X11(X): return np.column_stack([np.column_stack([c["T"] for c in X["circ"]]),X["power"]])
def baseline_scores(TR):
    Z0=X11(TR); med=np.median(Z0,0); iqr=np.percentile(Z0,75,0)-np.percentile(Z0,25,0)+1e-9; z=lambda X:(X11(X)-med)/iqr
    ZT=z(TR); mu=ZT.mean(0); Ci=np.linalg.pinv(np.cov(ZT.T)+1e-3*np.eye(11))
    C=np.cov((ZT-mu).T); w,V=np.linalg.eigh(C); o=np.argsort(w)[::-1]; w,V=w[o],V[:,o]
    q=int(np.searchsorted(np.cumsum(w)/w.sum(),0.95)+1); P=V[:,:q]
    iso=IsolationForest(n_estimators=200,random_state=SEED).fit(ZT)
    def mh(X): E=z(X)-mu; return np.einsum("ij,jk,ik->i",E,Ci,E)
    def t2(X): T=(z(X)-mu)@P; return (T**2/w[:q]).sum(1)
    def spe(X): E=(z(X)-mu)-((z(X)-mu)@P)@P.T; return (E**2).sum(1)
    def isf(X): return -iso.score_samples(z(X))
    return {"global_Mahalanobis":mh,"PCA_T2":t2,"PCA_SPE":spe,"IsolationForest":isf}
class RuleC:
    """day-max conformal threshold on a minute score function"""
    def __init__(self,f,CA,alpha=None): self.f=f; self.tau=cq(day_reduce(CA["dt"],f(CA),np.max),A.ALPHA if alpha is None else alpha)
    def day_alarms(self,X): return day_reduce(X["dt"],self.f(X),np.max)>self.tau
class V101:
    """original v1.0.1 detector (plain PIT) via code/_common, rule C"""
    def __init__(self,TRdf,CAdf):
        import _common as C; self.C=C; self.F,self.rc,self.pc=C.fit_on(TRdf)
        self.tau=cq(self._dm(CAdf),A.ALPHA)
    def _dm(self,df):
        s=self.C.Tval(df,self.F,self.rc,self.pc); dd=df.dt.dt.floor("D"); return np.array([s[(dd==i).values].max() for i in np.unique(dd)])
    def day_alarms_df(self,df): return self._dm(df)>self.tau
def build_detectors(TRdf,CAdf,include_v101=True):
    TR,CA=to_dict(TRdf),to_dict(CAdf); det={}
    det["v2_FROZEN"]=Detector("S0","Ddual",True).fit(TR,CA)
    det["v1_tieaware"]=Detector("S0","Dmax",False).fit(TR,CA)
    for k,f in baseline_scores(TR).items(): det[k]=RuleC(f,CA)
    if include_v101: det["v1.0.1_original"]=V101(TRdf,CAdf)
    return det
def alarms(det,df):
    return det.day_alarms_df(df) if isinstance(det,V101) else det.day_alarms(to_dict(df))
def cp(k,n):
    lo=0.0 if k==0 else beta.ppf(0.025,k,n-k+1); hi=1.0 if k==n else beta.ppf(0.975,k+1,n-k); return [round(100*float(lo),1),round(100*float(hi),1)]
def frac(a): a=np.asarray(a); return f"{int(a.sum())}/{len(a)}"
def mcnemar(a,b):
    a=np.asarray(a,bool); b=np.asarray(b,bool); n10=int((a&~b).sum()); n01=int((~a&b).sum())
    p=1.0 if n10+n01==0 else float(binomtest(n10,n10+n01,0.5).pvalue); return n10,n01,p
def holm(ps):
    ps=np.asarray(ps,float); o=np.argsort(ps); m=len(ps); adj=np.empty(m); run=0
    for r,i in enumerate(o): run=max(run,min(1,(m-r)*ps[i])); adj[i]=run
    return adj
def self_check():
    TRdf,CAdf,TEdf,_=site("Site2"); TR,CA,TE=map(to_dict,(TRdf,CAdf,TEdf))
    a=Detector("S0","Ddual",True).fit(TR,CA).day_stats(TE); b=GDetector().fit(TR,CA).day_stats(TE)
    assert np.allclose(a[0],b[0]) and np.allclose(a[1],b[1]),"GDetector default != frozen Detector"
    return True

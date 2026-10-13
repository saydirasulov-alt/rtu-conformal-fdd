"""Algorithm v2 framework (see ALGO_PLAN_V2.md). Detector = eligibility-aware branches,
optional condition-aware residuals, tie-aware PIT, max over branches per minute, day statistic,
day-level conformal threshold from calibration normal days."""
import numpy as np,pandas as pd
GATE=200.0; ALPHA=0.05
def cq(s,a):
    s=np.sort(np.asarray(s)); n=len(s); k=min(int(np.ceil((1-a)*(n+1))),n)-1; return s[max(k,0)]
def dayid(dt): return dt.dt.floor("D").values
# ---------------- data adapters ----------------
def load_sim(path):
    d=pd.read_csv(path); d["dt"]=pd.to_datetime(d["Datetime"]); d=d[d.RTU_COMP_WATT>GATE].copy()
    out={"dt":d["dt"].reset_index(drop=True),"OA":d.RTU_OA_TEMP.values,"RA":d.RTU_RA_TEMP.values,
         "circ":[{"T":np.column_stack([d.RTU_REFG_COND_TEMP,d.RTU_REFG_DISC_TEMP,d.RTU_REFG_SUCT_TEMP,d.RTU_REFG_DISC_TEMP-d.RTU_REFG_SUCT_TEMP]),
                  "P":np.column_stack([d.RTU_REFG_DISC_PRES,d.RTU_REFG_SUCT_PRES])}],
         "power":np.column_stack([d.RTU_COMP_WATT,d.RTU_TOT_WATT,d.RTU_SA_FAN_WATT])}
    return out
def load_field(path):
    cols=["Datetime","RTU_COMP_WATT","RTU_TOT_WATT","RTU_SA_FAN_WATT","RTU_OA_TEMP","RTU_RA_TEMP"]+[f"RTU_REFG_{a}_{c}" for a in ("COND_TEMP","DISC_TEMP","SUCT_TEMP","DISC_PRES","SUCT_PRES") for c in (1,2)]
    d=pd.read_csv(path,usecols=cols); d["dt"]=pd.to_datetime(d.Datetime); d=d[d.RTU_COMP_WATT>GATE].dropna().sort_values("dt").reset_index(drop=True)
    circ=[]
    for c in (1,2):
        T=np.column_stack([d[f"RTU_REFG_COND_TEMP_{c}"],d[f"RTU_REFG_DISC_TEMP_{c}"],d[f"RTU_REFG_SUCT_TEMP_{c}"],d[f"RTU_REFG_DISC_TEMP_{c}"]-d[f"RTU_REFG_SUCT_TEMP_{c}"]])
        circ.append({"T":T,"P":np.column_stack([d[f"RTU_REFG_DISC_PRES_{c}"],d[f"RTU_REFG_SUCT_PRES_{c}"]])})
    return {"dt":d["dt"],"OA":d.RTU_OA_TEMP.values,"RA":d.RTU_RA_TEMP.values,"circ":circ,
            "power":np.column_stack([d.RTU_COMP_WATT,d.RTU_TOT_WATT,d.RTU_SA_FAN_WATT])}
def subset(D,mask):
    return {"dt":D["dt"][mask].reset_index(drop=True),"OA":D["OA"][mask],"RA":D["RA"][mask],
            "circ":[{k:v[mask] for k,v in c.items()} for c in D["circ"]],"power":D["power"][mask]}
def split_days(D,a,b):
    dd=dayid(D["dt"]); u=np.unique(dd)
    return [subset(D,np.isin(dd,s)) for s in (u[:a],u[a:a+b],u[a+b:])],u
# ---------------- detector ----------------
class Detector:
    def __init__(self,S="S0",D="Dmax",J=False): self.S,self.Dstat,self.J=S,D,J
    def _cond(self,X):
        z=np.column_stack([(X["OA"]-self.cm[0])/self.cs[0],(X["RA"]-self.cm[1])/self.cs[1]])
        return np.column_stack([np.ones(len(z)),z[:,0],z[:,1],z[:,0]**2,z[:,0]*z[:,1]])
    def _blocks(self,X):
        P=self.S in("S1","S3"); B={}
        B["refrig"]=[np.column_stack([c["T"],c["P"]]) if P else c["T"] for c in X["circ"]]
        B["power"]=[X["power"]]
        if self.J: B["joint"]=[np.column_stack([np.column_stack([c["T"],c["P"]]) if P else c["T"] for c in X["circ"]]+[X["power"]])]
        return B
    def _resid(self,key,j,Y,X,fit=False):
        if self.S not in("S2","S3"): return Y
        Phi=self._cond(X)
        if fit: self.beta[(key,j)]=np.linalg.solve(Phi.T@Phi+1e-3*np.eye(Phi.shape[1]),Phi.T@Y)
        return Y-Phi@self.beta[(key,j)]
    def _raw(self,X,fit=False):
        out={}
        for key,mats in self._blocks(X).items():
            sc=[]
            for j,Y in enumerate(mats):
                R=self._resid(key,j,Y,X,fit)
                if fit:
                    med=np.median(R,0); iqr=np.percentile(R,75,0)-np.percentile(R,25,0)+1e-9; Z=(R-med)/iqr
                    C=np.cov(Z.T)+1e-3*np.eye(Z.shape[1]); self.m[(key,j)]=(med,iqr,Z.mean(0),np.linalg.pinv(C))
                med,iqr,mu,Ci=self.m[(key,j)]; E=(R-med)/iqr-mu; sc.append(np.einsum("ij,jk,ik->i",E,Ci,E))
            out[key]=np.max(np.column_stack(sc),1)
        return out
    def _pit(self,x,ref):
        n=len(ref); T=np.searchsorted(ref,x,"right")/(n+1); m=ref[-1]; b=x>m
        T[b]=n/(n+1)+(1/(n+1))*(1-m/np.maximum(x[b],1e-300)); return T
    def minute_scores(self,X):
        raw=self._raw(X); return np.max(np.column_stack([self._pit(raw[k],self.ref[k]) for k in raw]),1)
    def day_stats(self,X):
        s=self.minute_scores(X); dd=dayid(X["dt"]); u=np.unique(dd)
        mx=np.array([s[dd==i].max() for i in u]); mn=np.array([s[dd==i].mean() for i in u]); return mx,mn,s
    def fit(self,TR,CA):
        self.cm=(TR["OA"].mean(),TR["RA"].mean()); self.cs=(TR["OA"].std()+1e-9,TR["RA"].std()+1e-9)
        self.beta={}; self.m={}; raw=self._raw(TR,fit=True); self.ref={k:np.sort(v) for k,v in raw.items()}
        mx,mn,_=self.day_stats(CA)
        if self.Dstat=="Dmax": self.tau={"max":cq(mx,ALPHA)}
        elif self.Dstat=="Dmean": self.tau={"mean":cq(mn,ALPHA)}
        else: self.tau={"max":cq(mx,ALPHA/2),"mean":cq(mn,ALPHA/2)}
        return self
    def day_alarms(self,X):
        mx,mn,_=self.day_stats(X); a=np.zeros(len(mx),bool)
        if "max" in self.tau: a|=mx>self.tau["max"]
        if "mean" in self.tau: a|=mn>self.tau["mean"]
        return a
GRID=[(S,D,J) for S in ("S0","S1","S2","S3") for D in ("Dmax","Dmean","Ddual") for J in (False,True)]

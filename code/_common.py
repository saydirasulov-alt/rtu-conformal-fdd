"""Common pinned helpers for all Claim-3 scripts. seed=20260618, gate=200W, day-level splits."""
import os,numpy as np,pandas as pd
SEED=20260618; GATE=200.0
DATA=os.environ.get("RTU_DATA_DIR")
if not DATA:
    raise SystemExit("Set RTU_DATA_DIR to the LBNL data directory (see README). "
                     "Expected subfolders: 'Field RTU/' and 'ORNL_RTU/'.")
FLD=os.path.join(DATA,"Field RTU"); ORN=os.path.join(DATA,"ORNL_RTU")
Tn=["COND_TEMP","DISC_TEMP","SUCT_TEMP"]
FCOLS=["Datetime","RTU_COMP_WATT","RTU_TOT_WATT","RTU_SA_FAN_WATT"]+["RTU_REFG_"+b+s for b in Tn for s in("_1","_2")]
def load_field(fn):
    d=pd.read_csv(os.path.join(FLD,fn),usecols=FCOLS); d["dt"]=pd.to_datetime(d.Datetime)
    return d[d.RTU_COMP_WATT>GATE].dropna().sort_values("dt").reset_index(drop=True)
def cf(x,c): return np.column_stack([x["RTU_REFG_COND_TEMP"+c],x["RTU_REFG_DISC_TEMP"+c],x["RTU_REFG_SUCT_TEMP"+c],(x["RTU_REFG_DISC_TEMP"+c]-x["RTU_REFG_SUCT_TEMP"+c])])
def pf(x): return np.column_stack([x.RTU_COMP_WATT,x.RTU_TOT_WATT,x.RTU_SA_FAN_WATT])
def rzfit(X): return np.median(X,0),(np.percentile(X,75,0)-np.percentile(X,25,0))+1e-9
def rz(X,ms): return (np.asarray(X)-ms[0])/ms[1]
def mfit(X): return X.mean(0),np.linalg.pinv(np.cov(X.T)+1e-3*np.eye(X.shape[1]))
def md(X,mc): e=X-mc[0]; return np.einsum("ij,jk,ik->i",e,mc[1],e)
def pit(x,r): r=np.sort(r); return np.searchsorted(r,x,"right")/(len(r)+1)
def fit_on(cal):
    F=[]
    for fx in [lambda z:cf(z,"_1"),lambda z:cf(z,"_2"),pf]:
        ms=rzfit(np.asarray(fx(cal))); mc=mfit(rz(fx(cal),ms)); F.append((fx,ms,mc))
    rc=np.maximum(md(rz(F[0][0](cal),F[0][1]),F[0][2]),md(rz(F[1][0](cal),F[1][1]),F[1][2])); pc=md(rz(F[2][0](cal),F[2][1]),F[2][2])
    return F,rc,pc
def Tval(df,F,rc,pc):
    r=np.maximum(md(rz(F[0][0](df),F[0][1]),F[0][2]),md(rz(F[1][0](df),F[1][1]),F[1][2])); p=md(rz(F[2][0](df),F[2][1]),F[2][2])
    return np.maximum(pit(r,rc),pit(p,pc))
def conf_tau(Tc,a=0.05): n=len(Tc); return np.sort(Tc)[min(int(np.ceil((1-a)*(n+1))),n)-1]
def days(d): 
    import pandas as pd; c,_=pd.factorize(d.dt.dt.floor("D")); return c

"""E10c (Amendment P2-A8): spectrum-relative ridge (c x median eigenvalue per branch), sensitivity only."""
import os,json,numpy as np
from pathlib import Path
import phase2_common as P
A=P.A; OUT=Path(P.HERE)/"results"; SIM=os.environ.get("RTU_SIM_DIR")
HOLD=["evapfouling10","evapfouling20","evapfouling30","evapfouling40","evapfouling50","suctionpipe01bar","suctionpipe03bar","suctionpipe06bar","suctionpipe09bar","undercharge10","undercharge15","undercharge20"]
class SDet(P.GDetector):
    def __init__(self,c): super().__init__(); self.c=c; self.lam={}
    def _raw(self,X,fit=False):
        out={}
        for key,mats in self._blocks(X).items():
            sc=[]
            for j,Y in enumerate(mats):
                if fit:
                    med=np.median(Y,0); iqr=np.percentile(Y,75,0)-np.percentile(Y,25,0)+1e-9; Z=(Y-med)/iqr; C=np.cov(Z.T)
                    lam=self.c*float(np.median(np.linalg.eigvalsh(C))); self.m[(key,j)]=(med,iqr,Z.mean(0),np.linalg.pinv(C+lam*np.eye(Z.shape[1]))); self.lam[(key,j)]=lam
                med,iqr,mu,Ci=self.m[(key,j)]; E=(Y-med)/iqr-mu; sc.append(np.einsum("ij,jk,ik->i",E,Ci,E))
            out[key]=np.max(np.column_stack(sc),1)
        return out
R={}
for c in (1e-4,1e-3,1e-2):
    r={}
    for s in P.SITES:
        TR,CA,TE,U=map(P.to_dict,P.site(s)); d=SDet(c).fit(TR,CA)
        r[s]={"test_dayFAR":P.frac(d.day_alarms(TE)),"fault_day_sens":P.frac(d.day_alarms(U)),"ridges":{f"{k[0]}{k[1]}":float(f"{v:.3g}") for k,v in d.lam.items()}}
    if SIM:
        B=A.load_sim(os.path.join(SIM,"RTU_sim_baseline.csv")); (TR,CA,TE),u=A.split_days(B,50,25); td=u[75:]; d=SDet(c).fit(TR,CA); sens=[]
        for k in HOLD:
            F=A.load_sim(os.path.join(SIM,f"RTU_sim_{k}.csv")); F=A.subset(F,np.isin(A.dayid(F["dt"]),td)); sens.append(d.day_alarms(F).mean())
        r["sim_holdout"]={"baseline_test_dayFAR":P.frac(d.day_alarms(TE)),"holdout_mean_sens_pct":round(100*float(np.mean(sens)),1)}
    R[f"c={c:g}"]=r; print(c,{k:(v.get('test_dayFAR',v.get('baseline_test_dayFAR')),v.get('fault_day_sens',v.get('holdout_mean_sens_pct'))) for k,v in r.items()})
with open(OUT/"e10c_ridge_spectrum.json","w") as fh: json.dump(R,fh,indent=1)

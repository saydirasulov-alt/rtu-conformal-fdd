"""E10b (Amendment P2-A2): descriptive ridge sweep on the field sites and joint-branch covariance spectrum."""
import json,numpy as np
from pathlib import Path
import phase2_common as P
OUT=Path(P.HERE)/"results"; R={}
for s in P.SITES:
    TR,CA,TE,U=P.site(s); TRd,CAd,TEd,Ud=map(P.to_dict,(TR,CA,TE,U)); R[s]={}
    for r in (1e-5,1e-4,3e-4,1e-3,2e-3,3e-3,5e-3,1e-2,3e-2):
        d=P.GDetector(ridge=r).fit(TRd,CAd); R[s][f"{r:g}"]={"test_dayFAR":P.frac(d.day_alarms(TEd)),"fault_day_sens":P.frac(d.day_alarms(Ud))}
    d=P.GDetector().fit(TRd,CAd); Y=np.column_stack([TRd["circ"][0]["T"],TRd["circ"][1]["T"],TRd["power"]])
    med=np.median(Y,0); iqr=np.percentile(Y,75,0)-np.percentile(Y,25,0)+1e-9; w=np.linalg.eigvalsh(np.cov(((Y-med)/iqr).T))
    R[s]["joint_cov_eigenvalues_smallest5"]=[float(f"{x:.3g}") for x in w[:5]]
    W,V=np.linalg.eigh(np.cov(((Y-med)/iqr).T)); v=V[:,2]; v=v*np.sign(v[np.argmax(abs(v))])
    names=[f"c{c}_{n}" for c in (1,2) for n in ("liquid","discharge","suction","disc_minus_suct")]+["comp_W","tot_W","fan_W"]
    Z=(Y-med)/iqr; mu=Z.mean(0); Yu=np.column_stack([Ud["circ"][0]["T"],Ud["circ"][1]["T"],Ud["power"]]); Zu=(Yu-med)/iqr
    R[s]["third_eigvec_loadings_abs_gt_0.1"]={n:round(float(x),2) for n,x in zip(names,v) if abs(x)>0.1}
    R[s]["train_projection_sd"]=round(float(((Z-mu)@v).std()),4); R[s]["fault_median_abs_projection"]=round(float(np.median(abs((Zu-mu)@v))),4)
    print(s,R[s])
with open(OUT/"e10b_ridge_sweep.json","w") as fh: json.dump(R,fh,indent=1)

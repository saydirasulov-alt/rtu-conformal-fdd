"""E15c (NOT pre-specified; added 2026-10-20 after the second audit). Main field results recomputed with the
60-compressor-on-minute minimum of the day-pattern rule applied to every day (short days abstain), for the
frozen detector and the generic comparators under the two-statistic rule. Thresholds are unchanged because no
calibration day is short. Descriptive only."""
import json,numpy as np
from pathlib import Path
import phase2_common as P
from e14_equal_budget import Dual
OUT=Path(P.HERE)/"results"; R={}
def n_min(df): return df.groupby(df.dt.dt.floor("D")).size().values
for s in P.SITES:
    TR,CA,TE,U=P.site(s); TRd,CAd,TEd,Ud=map(P.to_dict,(TR,CA,TE,U))
    det={"frozen":P.GDetector().fit(TRd,CAd)}; det.update({k:Dual(f,CAd) for k,f in P.baseline_scores(TRd).items()})
    kT,kU=n_min(TE)>=60,n_min(U)>=60; R[s]={"short_calibration_days":int((n_min(CA)<60).sum()),"short_test_days":int((~kT).sum()),"short_fault_days":int((~kU).sum())}
    for k,d in det.items():
        a,b=d.day_alarms(TEd),d.day_alarms(Ud)
        R[s][k]={"test_dayFAR_scored":f"{int(a[kT].sum())}/{int(kT.sum())}","fault_day_sens_scored":f"{int(b[kU].sum())}/{int(kU.sum())}",
                 "short_days_alarmed":{"test":int(a[~kT].sum()),"fault":int(b[~kU].sum())}}
print(json.dumps(R,indent=1)); json.dump(R,open(OUT/"e15c_minimum_minutes.json","w"),indent=1)

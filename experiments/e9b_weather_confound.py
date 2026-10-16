"""E9b (Amendment P2-A3): alarm rate stratified by whether daily-mean OA lies within the training-day range."""
import json,numpy as np
from pathlib import Path
import phase2_common as P
OUT=Path(P.HERE)/"results"; R={}
for s in P.SITES:
    TR,CA,TE,U=P.site(s); d=P.Detector("S0","Ddual",True).fit(P.to_dict(TR),P.to_dict(CA))
    oa=lambda df:df.groupby(df.dt.dt.floor("D")).RTU_OA_TEMP.mean().values
    lo,hi=oa(TR).min(),oa(TR).max(); R[s]={"train_dayOA_range":[round(float(lo),1),round(float(hi),1)]}
    for nm,df in (("fault",U),("normal_test",TE)):
        a=P.alarms(d,df); o=oa(df); inn=(o>=lo)&(o<=hi)
        R[s][nm]={"inside":P.frac(a[inn]),"outside":P.frac(a[~inn]),"dayOA_range":[round(float(o.min()),1),round(float(o.max()),1)]}
    print(s,R[s])
with open(OUT/"e9b_weather_confound.json","w") as fh: json.dump(R,fh,indent=1)

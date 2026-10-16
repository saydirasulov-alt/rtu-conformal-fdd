"""E12b (Amendment P2-A7): injected sensor faults with every comparator under the frozen detector's two-statistic rule."""
import json,numpy as np
from pathlib import Path
import phase2_common as P
from e12_injection import scenarios,inject
from e14_equal_budget import Dual
OUT=Path(P.HERE)/"results"; R={}
for s in P.SITES:
    TR,CA,TE,U=P.site(s); TRd,CAd=P.to_dict(TR),P.to_dict(CA)
    det={"v2_FROZEN":P.Detector("S0","Ddual",True).fit(TRd,CAd),"v1_tieaware_dual_rule":P.Detector("S0","Ddual",False).fit(TRd,CAd)}
    det.update({k:Dual(f,CAd) for k,f in P.baseline_scores(TRd).items()})
    clean={k:d.day_alarms(P.to_dict(TE)) for k,d in det.items()}; rows={}
    for name,col,kind,v in scenarios(TR):
        Ti=P.to_dict(inject(TE,col,kind,v)); rows[name]={}
        for k,d in det.items():
            a=d.day_alarms(Ti); rows[name][k]={"alarm_days":P.frac(a),"new_alarm_days_on_clean_quiet_days":int((a&~clean[k]).sum())}
    nq={k:int((~clean[k]).sum()) for k in det}; nt=len(clean["v2_FROZEN"])
    summ={"clean_FAR":{k:P.frac(clean[k]) for k in det},
          "mean_new_alarm_rate_on_quiet_days_pct":{k:round(100*float(np.mean([rows[n][k]["new_alarm_days_on_clean_quiet_days"]/max(nq[k],1) for n in rows])),1) for k in det},
          "scenarios_alarmed_on_majority_of_days":{k:int(sum(int(rows[n][k]["alarm_days"].split("/")[0])>0.5*nt for n in rows)) for k in det}}
    R[s]={"summary":summ,"scenarios":rows}; print("=====",s); [print("  ",k,v) for k,v in summ.items()]
with open(OUT/"e12b_injection_equal_budget.json","w") as fh: json.dump(R,fh,indent=1)

"""E12: semi-synthetic sensor faults injected into real normal TEST days (ANALYSIS_PLAN_PHASE2.md).
Training and calibration days are untouched; the compressor-on gate is evaluated on the uncorrupted power signal."""
import json,numpy as np
from pathlib import Path
import phase2_common as P
OUT=Path(P.HERE)/"results"
TEMPS={"suction_T1":"RTU_REFG_SUCT_TEMP_1","discharge_T1":"RTU_REFG_DISC_TEMP_1","liquid_T1":"RTU_REFG_COND_TEMP_1"}
def scenarios(TR):
    S=[]
    for nm,col in TEMPS.items():
        iqr=float(np.percentile(TR[col],75)-np.percentile(TR[col],25))
        for k in (-2,-1,-0.5,0.5,1,2): S.append((f"{nm}|bias|{k:+g}IQR",col,"bias",k*iqr))
        for k in (1,2,4): S.append((f"{nm}|drift|{k:g}IQR",col,"drift",k*iqr))
        S.append((f"{nm}|stuck",col,"stuck",None))
    for s in (-0.2,-0.1,-0.05,0.05,0.1,0.2): S.append((f"comp_power|scale|{s:+g}","RTU_COMP_WATT","scale",s))
    S.append(("comp_power|stuck","RTU_COMP_WATT","stuck",None))
    return S
def inject(TE,col,kind,v):
    d=TE.copy(); x=d[col].astype(float).values
    if kind=="bias": x=x+v
    elif kind=="drift": t=(d.dt-d.dt.iloc[0]).dt.total_seconds().values; x=x+v*t/t[-1]
    elif kind=="stuck": x=np.full_like(x,x[0])
    elif kind=="scale": x=x*(1+v)
    d[col]=x; return d
if __name__=="__main__":
 R={}
 for s in P.SITES:
     TR,CA,TE,U=P.site(s); det=P.build_detectors(TR,CA,include_v101=False)
     clean={k:P.alarms(d,TE) for k,d in det.items()}; rows={}
     for name,col,kind,v in scenarios(TR):
         Ti=inject(TE,col,kind,v); rows[name]={"magnitude":v}
         for k,d in det.items():
             a=P.alarms(d,Ti); c=clean[k]
             rows[name][k]={"alarm_days":P.frac(a),"clean_alarm_days":P.frac(c),"new_alarm_days_on_clean_quiet_days":int((a&~c).sum()),
                            "first_alarm_day":int(np.argmax(a))+1 if a.any() else None}
     # family summaries: mean alarm rate per detector over scenario families
     fam={}
     for name in rows:
         f=name.split("|")[1]; fam.setdefault(f,[]).append(name)
     summ={}
     for f,names in fam.items():
         summ[f]={k:round(100*float(np.mean([int(rows[n][k]["alarm_days"].split("/")[0])/int(rows[n][k]["alarm_days"].split("/")[1]) for n in names])),1) for k in det}
     summ["all"]={k:round(100*float(np.mean([int(rows[n][k]["alarm_days"].split("/")[0])/int(rows[n][k]["alarm_days"].split("/")[1]) for n in rows])),1) for k in det}
     nq={k:int((~clean[k]).sum()) for k in det}
     summ["all_new_alarm_rate_on_clean_quiet_days_pct"]={k:round(100*float(np.mean([rows[n][k]["new_alarm_days_on_clean_quiet_days"]/max(nq[k],1) for n in rows])),1) for k in det}
     summ["clean_FAR_pct"]={k:round(100*float(clean[k].mean()),1) for k in det}
     summ["scenarios_detected_on_majority_of_days"]={k:int(sum(int(rows[n][k]["alarm_days"].split("/")[0])>0.5*len(TE.dt.dt.floor("D").unique()) for n in rows)) for k in det}
     R[s]={"n_test_days":int(TE.dt.dt.floor("D").nunique()),"n_scenarios":len(rows),"summary_mean_alarm_rate_pct":summ,"scenarios":rows}
     print("=====",s,len(rows),"scenarios");
     for f,v in summ.items(): print(f"  {f:40s}",v)
 with open(OUT/"e12_injection.json","w") as fh: json.dump(R,fh,indent=1)

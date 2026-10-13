"""Develop on simulated DEV faults only; select per ALGO_PLAN_V2.md; write frozen config."""
import os,sys,json,glob,numpy as np
sys.path.insert(0,os.path.dirname(__file__)); from algo_v2 import *
from pathlib import Path
OUT=Path(__file__).resolve().parent/"results"; OUT.mkdir(exist_ok=True)
SIM=os.environ.get("RTU_SIM_DIR"); assert SIM, "set RTU_SIM_DIR to the 'Simulated RTU' folder"
DEV=["condfouling10","condfouling20","condfouling30","condfouling40","condfouling50","liquidpipe01bar","liquidpipe04bar","liquidpipe08bar","liquidpipe10bar","overcharge10","overcharge15","overcharge20"]
B=load_sim(os.path.join(SIM,"RTU_sim_baseline.csv")); (TR,CA,TE),u=split_days(B,50,25); test_days=u[75:]
F={k:load_sim(os.path.join(SIM,f"RTU_sim_{k}.csv")) for k in DEV}
F={k:subset(v,np.isin(dayid(v["dt"]),test_days)) for k,v in F.items()}
rows=[]
for S,D,J in GRID:
    det=Detector(S,D,J).fit(TR,CA); far=det.day_alarms(TE)
    sens={k:float(det.day_alarms(v).mean()) for k,v in F.items()}
    rows.append({"S":S,"D":D,"J":J,"baseline_test_dayFAR":f"{int(far.sum())}/{len(far)}","dev_mean_sens":round(100*float(np.mean(list(sens.values()))),1),
                 "dev_sens":{k:round(100*v,1) for k,v in sens.items()}})
    print(f"{S} {D:5s} J={int(J)}  FAR {rows[-1]['baseline_test_dayFAR']:>5s}  DEV mean sens {rows[-1]['dev_mean_sens']:5.1f}%")
order={"S0":0,"S1":1,"S2":2,"S3":3,"Dmax":0,"Dmean":1,"Ddual":2}
best=max(r["dev_mean_sens"] for r in rows)
cands=[r for r in rows if r["dev_mean_sens"]>=best-1.0]
sel=sorted(cands,key=lambda r:(order[r["S"]],order[r["D"]],int(r["J"])))[0]
frozen={"S":sel["S"],"D":sel["D"],"J":sel["J"],"selected_on":"simulated DEV faults only","dev_mean_sens":sel["dev_mean_sens"],"best_dev_mean_sens":best}
with open(OUT/"algo_v2_dev_grid.json","w") as fh: json.dump(rows,fh,indent=1)
with open(OUT/"algo_v2_FROZEN.json","w") as fh: json.dump(frozen,fh,indent=1)
print("FROZEN:",frozen)

"""Run all Phase experiments E1-E6 in order and write experiments/results/SUMMARY.json.
Usage:  RTU_DATA_DIR=/path/to/data python experiments/run_phase_all.py
Windows PowerShell:  $env:RTU_DATA_DIR="D:\\path\\to\\data"; python experiments\\run_phase_all.py"""
import os,sys,json,time,runpy,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent; RES=HERE/"results"
if not os.environ.get("RTU_DATA_DIR"): sys.exit("Set RTU_DATA_DIR first (see README).")
STEPS=[("E1 baselines","e1_baselines.py","e1_baselines.json"),
       ("E2 detectability","e2_detectability.py","e2_detectability.json"),
       ("E3 ablation","e3_ablation.py","e3_ablation.json"),
       ("E4 missingness","e4_missingness.py","e4_missingness.json"),
       ("E5 temporal stability","e5_temporal_stability.py","e5_temporal_stability.json"),
       ("E6 independent","e6_independent.py","e6_independent.json")]
summary={"steps":[]}
for name,script,out in STEPS:
    print(f"\n========== {name} ({script}) =========="); t=time.time()
    runpy.run_path(str(HERE/script),run_name="__main__")
    f=RES/out; summary["steps"].append({"step":name,"seconds":round(time.time()-t,1),"output":out,
        "sha256":hashlib.sha256(f.read_bytes()).hexdigest()})
with open(RES/"SUMMARY.json","w") as fh: json.dump({k:v for k,v in summary.items()},fh,indent=1)
print("\nDone. Outputs in",RES)
for s in summary["steps"]: print(f"  {s['step']:24s} {s['seconds']:6.1f}s  {s['sha256'][:12]}  {s['output']}")

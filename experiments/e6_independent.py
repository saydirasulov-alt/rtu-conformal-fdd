"""E6: independent-dataset validation hook (pre-registered addendum).
Runs only when $RTU_DATA_DIR/Independent/manifest.json exists. The manifest must be written before
scoring and must specify: normal_file, fault_file, column mapping to the field feature names
(COND/DISC/SUCT temps per circuit, compressor/total/fan power), split days {train,cal,test}.
No result is produced without real data."""
import os,json,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent/"results"; OUT.mkdir(exist_ok=True)
D=os.environ.get("RTU_DATA_DIR",""); man=Path(D)/"Independent"/"manifest.json"
if not man.exists():
    res={"status":"NOT RUN","reason":"no independent dataset provided (expected $RTU_DATA_DIR/Independent/manifest.json)"}
else:
    m=json.load(open(man))
    res={"status":"NOT IMPLEMENTED FOR THIS MANIFEST","manifest":m,
         "note":"Map columns per manifest, then reuse experiments/e5_temporal_stability.window(); kept explicit so that no untested mapping is run silently."}
with open(OUT/"e6_independent.json","w") as fh: json.dump(res,fh,indent=1)
print(res["status"],"-",res.get("reason",res.get("note")))

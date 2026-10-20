"""Input-data provenance: SHA-256 of every LBNL input file the analyses read.
  python experiments/data_manifest.py check   # compare local data with experiments/DATA_SHA256.txt (default)
  python experiments/data_manifest.py write   # regenerate the manifest (maintainers only)
Needs RTU_DATA_DIR (with 'Field RTU' and 'ORNL_RTU') and RTU_SIM_DIR ('Simulated RTU')."""
import os,sys,glob,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent; MAN=HERE/"DATA_SHA256.txt"
D=os.environ.get("RTU_DATA_DIR"); S=os.environ.get("RTU_SIM_DIR")
if not (D and S): sys.exit("set RTU_DATA_DIR and RTU_SIM_DIR")
GROUPS=[(D,"Field RTU",["Site1_Unfaulted.csv","Site1_Staging_Fault.csv","Site2_Unfaulted.csv","Site2_Undercharged40.csv"]),
        (D,"ORNL_RTU",["ERTU_*.csv","Inc_Eco_SP_*.csv","OA_damper_stuck_*.csv","SA_temp_bias_*.csv"]),
        (S,"",["RTU_sim_*.csv"])]
def files():
    out=[]
    for root,sub,pats in GROUPS:
        base=Path(root)/sub
        for p in pats: out+=sorted(base.glob(p))
    return out
def rel(f): 
    f=Path(f); return ("Simulated RTU/" if f.parent==Path(S) else f.parent.name+"/")+f.name
def h(f):
    m=hashlib.sha256()
    with open(f,"rb") as fh:
        for b in iter(lambda:fh.read(1<<20),b""): m.update(b)
    return m.hexdigest()
mode=sys.argv[1] if len(sys.argv)>1 else "check"
cur={rel(f):h(f) for f in files()}
if mode=="write":
    MAN.write_text("".join(f"{v}  {k}\n" for k,v in sorted(cur.items()))); print(f"wrote {len(cur)} entries to {MAN}")
else:
    ref={l[66:].strip():l[:64] for l in MAN.read_text().splitlines() if l.strip()}
    miss=sorted(set(ref)-set(cur)); extra=sorted(set(cur)-set(ref)); bad=sorted(k for k in ref if k in cur and cur[k]!=ref[k])
    print(f"{len(ref)} files in manifest; {len(ref)-len(miss)-len(bad)} match; {len(bad)} differ; {len(miss)} missing; {len(extra)} extra")
    for k in bad: print("DIFFERS:",k)
    for k in miss: print("MISSING:",k)
    sys.exit(1 if (bad or miss) else 0)

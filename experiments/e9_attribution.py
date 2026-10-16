"""E9: branch and circuit attribution of v2 alarm days (post-hoc diagnostic; does not alter alarms). ANALYSIS_PLAN_PHASE2.md."""
import json,numpy as np
from collections import Counter
from pathlib import Path
import phase2_common as P
OUT=Path(P.HERE)/"results"
def attribute(det,X):
    mx,mn,_=det.day_stats(X); trig_max=mx>det.tau["max"]; trig_mean=mn>det.tau["mean"]
    BT=det.branch_T(X); CT=det.circuit_T(X); dd=P.dayid(X["dt"]); u=np.unique(dd); out=[]
    for i,d in enumerate(u):
        if not (trig_max[i] or trig_mean[i]): out.append(None); continue
        m=dd==d; rec={"stat":[s for s,t in (("max",trig_max[i]),("mean",trig_mean[i])) if t]}
        for s in rec["stat"]:
            f=np.max if s=="max" else np.mean
            bs={b:float(f(v[m])) for b,v in BT.items()}; cs={c:float(f(v[m])) for c,v in CT.items()}
            rec[f"branch_{s}"]=max(bs,key=bs.get); rec[f"circuit_{s}"]=int(max(cs,key=cs.get)); rec[f"branch_vals_{s}"]={k:round(v,4) for k,v in bs.items()}; rec[f"circuit_vals_{s}"]={str(k):round(v,4) for k,v in cs.items()}
        out.append(rec)
    return out
def summarise(recs):
    r=[x for x in recs if x]; c=Counter(); cc=Counter(); st=Counter()
    for x in r:
        st["+".join(x["stat"])]+=1
        s=x["stat"][0] if len(x["stat"])==1 else "max"   # if both trigger, the max statistic is used for the headline count
        c[x[f"branch_{s}"]]+=1; cc[x[f"circuit_{s}"]]+=1
    return {"alarm_days":len(r),"trigger":dict(st),"branch":dict(c),"circuit":dict(cc)}
if __name__=="__main__":
  R={}
  for s in P.SITES:
      TR,CA,TE,U=P.site(s); det=P.GDetector().fit(P.to_dict(TR),P.to_dict(CA))
      rf=attribute(det,P.to_dict(U)); rn=attribute(det,P.to_dict(TE))
      R[s]={"fault_days":summarise(rf),"normal_test_days":summarise(rn),"fault_day_records":rf,"normal_day_records":rn}
      print(s,"FAULT",R[s]["fault_days"]); print(s,"NORMAL",R[s]["normal_test_days"])
  with open(OUT/"e9_attribution.json","w") as fh: json.dump(R,fh,indent=1)

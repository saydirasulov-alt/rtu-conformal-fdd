"""E4: missing-sensor robustness on ORNL (pre-registered addendum)."""
import sys,os,json,itertools,numpy as np,pandas as pd
CODE=os.path.join(os.path.dirname(__file__),"..","code"); sys.path.insert(0,CODE)
from pathlib import Path
OUT=Path(__file__).resolve().parent/"results"; OUT.mkdir(exist_ok=True)
src=open(os.path.join(CODE,"ornl_sensor_unavailability.py")).read(); src=src[:src.index("rows=[]")]
ns={"__file__":os.path.join(CODE,"ornl_sensor_unavailability.py")}; exec(compile(src,"ornl_head","exec"),ns)
CA,TE,BRANCH,SENS,FAULTS,FA,bscore,eligible,SEED,ALPHA=[ns[k] for k in ("CA","TE","BRANCH","SENS","FAULTS","FA","bscore","eligible","SEED","ALPHA")]
def cq(s,a): s=np.sort(s); n=len(s); k=min(int(np.ceil((1-a)*(n+1))),n)-1; return s[max(k,0)]
BR=list(BRANCH)
SCA={b:bscore(CA,b) for b in BR}
TAU={}
for r in range(1,4):
    for S in itertools.combinations(BR,r): TAU[S]=cq(np.column_stack([SCA[b] for b in S]).max(1),ALPHA)
MASKS={"DMPR":["DMPR"],"SAT":["SAT"],"power family":["COMP","TOT","FAN"]}
def missing_matrix(df,sensors,mode,level,rng):
    n=len(df); miss=np.zeros(n,bool)
    if mode=="intermittent": miss=rng.random(n)<level
    else:
        d,_=pd.factorize(df.dt.dt.floor("D")); t=df.dt.values
        for i in np.unique(d):
            idx=np.where(d==i)[0]
            if level>=24: miss[idx]=True; continue
            day0=pd.Timestamp(t[idx[0]]).floor("D"); st=day0+pd.Timedelta(minutes=float(rng.uniform(0,24*60-level*60)))
            en=st+pd.Timedelta(hours=level); tt=pd.to_datetime(t[idx]); miss[idx[(tt>=st)&(tt<en)]]=True
    return {s:miss for s in sensors}
def evaluate(df,miss):
    present=lambda s: ~miss[s] if s in miss else np.ones(len(df),bool)
    elig={b:np.all(np.column_stack([present(s) for s in BRANCH[b]]),1) for b in BR}
    B={b:bscore(df,b) for b in BR}
    alarm=np.zeros(len(df),bool); unsup=0
    for key in set(map(tuple,np.column_stack([elig[b] for b in BR]))):
        S=tuple(b for b,e in zip(BR,key) if e)
        if not S: continue
        m=np.all(np.column_stack([elig[b]==e for b,e in zip(BR,key)]),1)
        TS=np.column_stack([B[b][m] for b in S]).max(1); alarm[m]=TS>TAU[S]
        # attribution check: argmax branch is always within S by construction
        unsup+=int(np.sum([S[j] not in S for j in np.argmax(np.column_stack([B[b][m] for b in S]),1)]))
    return elig,alarm,unsup
rng=np.random.default_rng(SEED); rows=[]
for mname,sensors in MASKS.items():
    for mode,levels in [("intermittent",[0.05,0.10,0.20,0.40]),("outage_hours",[1,6,24])]:
        for lv in levels:
            r={"masked":mname,"mode":mode,"level":lv}
            mte=missing_matrix(TE,sensors,mode,lv,rng); el,al,u=evaluate(TE,mte)
            d,_=pd.factorize(TE.dt.dt.floor("D")); r["normal_false_alarm_days"]=f"{int(sum(al[d==i].any() for i in np.unique(d)))}/{len(np.unique(d))}"
            r["normal_minute_FAR_pct"]=round(100*float(al.mean()),2); unsup_total=u; fr={}
            for fk,(pat,br) in FAULTS.items():
                df=FA[fk]; mf=missing_matrix(df,sensors,mode,lv,rng); el,al,u=evaluate(df,mf); unsup_total+=u
                d,_=pd.factorize(df.dt.dt.floor("D")); U=np.unique(d)
                elig_days=[i for i in U if el[br][d==i].any()]
                det=[i for i in elig_days if (al[d==i]&el[br][d==i]).any()]
                fr[fk]={"branch":br,"eligible_minute_frac":round(float(el[br].mean()),3),"abstain_minute_frac":round(1-float(el[br].mean()),3),
                        "eligible_fault_days":f"{len(elig_days)}/{len(U)}","eligible_day_sens":f"{len(det)}/{len(elig_days)}" if elig_days else "n/a",
                        "detection_yield_all_days":f"{len(det)}/{len(U)}"}
            r["faults"]=fr; r["unsupported_assertions"]=unsup_total; rows.append(r)
with open(OUT/"e4_missingness.json","w") as fh: json.dump(rows,fh,indent=1)
for r in rows:
    print(f"{r['masked']:13s} {r['mode']:12s} {str(r['level']):5s} FAdays {r['normal_false_alarm_days']:>5s} minFAR {r['normal_minute_FAR_pct']:5.2f}% unsup {r['unsupported_assertions']} | "+
          " ; ".join(f"{k}: elig {v['eligible_minute_frac']:.2f} yield {v['detection_yield_all_days']} sensElig {v['eligible_day_sens']}" for k,v in r["faults"].items()))

"""ORNL controlled sensor-unavailability evaluation with a real eligibility mask S(x).
Frozen train/cal/test day split; transforms fit on TRAIN only. Thresholds are empirical
minute-calibrated (tau_S^min) because only 14 eligible normal days are available, so day-level
calibration is infeasible. A branch emits NO score unless all its required sensors R_b are present
(structural abstention). Detection endpoint: fault-day sensitivity.
Branches: eco{MA,OA,DMPR}, SA{MA,OA,SAT,SAF}, power{COMP,TOT,FAN}. seed=20260618."""
from pathlib import Path
RESULTS=Path(__file__).resolve().parent.parent/"results"; RESULTS.mkdir(exist_ok=True)
import os,glob,json,numpy as np,pandas as pd,warnings; warnings.filterwarnings("ignore")
from _common import SEED,GATE,ORN
rng=np.random.default_rng(SEED); ALPHA=0.05
SENS={"MA":"RTU_MA_TEMP","OA":"RTU_OA_TEMP","DMPR":"RTU_OA_DMPR_DM","SAT":"RTU_SA_TEMP","SAF":"RTU_SA_FLOW","COMP":"COMP","TOT":"RTU_TOT_WATT","FAN":"RTU_SA_FAN_WATT"}
BRANCH={"eco":["MA","OA","DMPR"],"SA":["MA","OA","SAT","SAF"],"power":["COMP","TOT","FAN"]}
def load(fp):
    d=pd.read_csv(fp)
    for c in ["RTU_COMP_WATT_1","RTU_COMP_WATT_2","RTU_MA_TEMP","RTU_OA_TEMP","RTU_OA_DMPR_DM","RTU_SA_TEMP","RTU_SA_FLOW","RTU_TOT_WATT","RTU_SA_FAN_WATT"]:
        d[c]=pd.to_numeric(d[c],errors="coerce")
    d["COMP"]=d["RTU_COMP_WATT_1"]+d["RTU_COMP_WATT_2"]; d=d[d.COMP>GATE]
    d["dt"]=pd.to_datetime(d["Datetime"]) if "Datetime" in d.columns else pd.to_datetime(d.iloc[:,0])
    keep=["dt"]+list(dict.fromkeys(SENS.values()))
    return d[keep].dropna().sort_values("dt").reset_index(drop=True)
def feats(df,b):
    cols=[SENS[s] for s in BRANCH[b]]; X=df[cols].values
    if b in("eco","SA"): X=np.column_stack([X,(df[SENS["MA"]]-df[SENS["OA"]]).values])
    return np.nan_to_num(X,nan=0.0,posinf=0.0,neginf=0.0)
def rzfit(X): return np.median(X,0),(np.percentile(X,75,0)-np.percentile(X,25,0))+1e-9
def rz(X,ms): return (X-ms[0])/ms[1]
def mfit(X):
    X=np.nan_to_num(X,nan=0.0,posinf=0.0,neginf=0.0); C=np.cov(X.T)
    C=np.nan_to_num(C,nan=0.0)+1e-2*np.eye(X.shape[1]); return X.mean(0),np.linalg.pinv(C)
def md(X,mc): e=X-mc[0]; return np.einsum("ij,jk,ik->i",e,mc[1],e)
# normal ERTU
N=pd.concat([load(f) for f in glob.glob(os.path.join(ORN,"ERTU_*.csv"))],ignore_index=True).sort_values("dt").reset_index(drop=True)
dd,_=pd.factorize(N.dt.dt.floor("D")); uniq=np.unique(dd); pm=rng.permutation(uniq); n=len(pm)
tr=set(pm[:n//2]); ca=set(pm[n//2:3*n//4]); te=set(pm[3*n//4:])
TR=N[np.isin(dd,list(tr))]; CA=N[np.isin(dd,list(ca))]; TE=N[np.isin(dd,list(te))]
# fit branch score models on TRAIN only; PIT reference from TRAIN
M={}; REF={}
for b in BRANCH:
    ms=rzfit(feats(TR,b)); mc=mfit(rz(feats(TR,b),ms)); M[b]=(ms,mc)
    REF[b]=np.sort(md(rz(feats(TR,b),ms),mc))
def bscore(df,b):
    ms,mc=M[b]; s=md(rz(feats(df,b),ms),mc); return np.searchsorted(REF[b],s,"right")/(len(REF[b])+1)
def daymax_TS(df,S):
    if not S: return None
    d,_=pd.factorize(df.dt.dt.floor("D")); per=[]
    U=bscore  # branch PIT
    B={b:U(df,b) for b in S}
    for i in np.unique(d):
        m=(d==i); TS=np.max(np.column_stack([B[b][m] for b in S]),axis=1); per.append(TS.max())
    return np.array(per)
def minuteFAR(df,S,tau):
    if not S: return None
    B=np.column_stack([bscore(df,b) for b in S]); TS=B.max(1); return float((TS>tau).mean())
# eligibility patterns (which sensors AVAILABLE -> which branches eligible)
def eligible(avail):
    return [b for b in BRANCH if set(BRANCH[b]).issubset(avail)]
PATTERNS={
 "full (all sensors)":set(SENS),
 "no DMPR":set(SENS)-{"DMPR"},
 "no SA_TEMP":set(SENS)-{"SAT"},
 "no air-side family":set(SENS)-{"MA","OA","DMPR","SAT","SAF"},
 "no power":set(SENS)-{"COMP","TOT","FAN"},
 "none (all air+power gone)":set()}
# fault files -> which branch should detect
FAULTS={"economizer":("Inc_Eco_SP_*.csv","eco"),"damper":("OA_damper_stuck_*.csv","eco"),"SA-bias":("SA_temp_bias_*.csv","SA")}
FA={k:pd.concat([load(f) for f in glob.glob(os.path.join(ORN,pat))],ignore_index=True) for k,(pat,br) in FAULTS.items()}
def cq(a,al): a=np.sort(a); m=len(a); k=min(int(np.ceil((1-al)*(m+1))),m)-1; return a[max(k,0)]
rows=[]
for name,avail in PATTERNS.items():
    S=eligible(avail)
    row={"pattern":name,"eligible_branches":S,"|S|":len(S)}
    if not S:
        row.update({"minute_FAR":None,"abstain":"ALL (S=empty)","unsupported_assert_rate":0.0}); rows.append(row); continue
    # pattern-specific MINUTE-level conformal threshold on CAL minutes (ORNL has too few days for day-level)
    TSca=np.column_stack([bscore(CA,b) for b in S]).max(1); tau=cq(TSca,ALPHA)
    row["minute_FAR"]=round(minuteFAR(TE,S,tau),3)
    row["unsupported_assert_rate"]=0.0  # by construction: branches not in S are never scored
    # fault detection: fault-day TPR (fraction of fault-days with >=1 alarm); ABSTAIN if branch not eligible
    det={}
    for fk,(pat,br) in FAULTS.items():
        if br in S:
            df=FA[fk]; d,_=pd.factorize(df.dt.dt.floor("D")); B={b:bscore(df,b) for b in S}
            hit=[]
            for i in np.unique(d):
                m=(d==i); TS=np.max(np.column_stack([B[b][m] for b in S]),axis=1); hit.append(TS.max()>tau)
            det[fk]=round(float(np.mean(hit)),3)
        else:
            det[fk]="ABSTAIN(unsupported)"
    row["fault_day_TPR"]=det; rows.append(row)
out={"protocol":"controlled sensor-unavailability on the ORNL experimental RTU; frozen train/cal/test day split; pattern-specific empirical minute-calibrated threshold (tau_S^min; only 14 eligible normal days, so day-level calibration is infeasible); detection reported as fault-day sensitivity; a branch is scored only if all its required sensors R_b are present (SA requires MA, OA, SAT, SAF because its feature set includes MA-OA)",
     "split_train_cal_test":[len(tr),len(ca),len(te)],"alpha":ALPHA,"sensor-unavailability":rows}
json.dump(out,open(RESULTS/"ornl_sensor_unavailability.json","w"),indent=2)
for r in rows: print(r["pattern"],"| S=",r["eligible_branches"],"| minuteFAR=",r.get("minute_FAR"),"| TPR=",r.get("fault_day_TPR","-"))

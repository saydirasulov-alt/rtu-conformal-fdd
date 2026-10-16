"""E11: field eligibility under static sensor-group unavailability vs median imputation (ANALYSIS_PLAN_PHASE2.md)."""
import json,numpy as np
from pathlib import Path
import phase2_common as P
from e9_attribution import attribute
OUT=Path(P.HERE)/"results"
PAT={"P0_full":((0,1),True),"P1_no_circuit2":((0,),True),"P2_no_circuit1":((1,),True),"P3_no_power":((0,1),False),"P4_power_only":((),True)}
def absent(pat):
    c,pw=PAT[pat]; return {"circuits":[x+1 for x in (0,1) if x not in c],"power":not pw}
def impute(X,ab,TR):
    X={k:(v.copy() if hasattr(v,"copy") else v) for k,v in X.items()}; X["circ"]=[{k:v.copy() for k,v in c.items()} for c in X["circ"]]
    for c in ab["circuits"]:
        for k in ("T","P"): X["circ"][c-1][k][:]=np.median(TR["circ"][c-1][k],0)
    if ab["power"]: X["power"][:]=np.median(TR["power"],0)
    return X
def _inputs(X,ab):
    cols=[X["circ"][c-1]["T"] for c in (1,2) if c not in ab["circuits"]]
    if not ab["power"]: cols.append(X["power"])
    cols+= [X["OA"][:,None],X["RA"][:,None]]; return np.column_stack(cols)
def reg_imputer(TR,ab):
    Xi=_inputs(TR,ab); mu,sd=Xi.mean(0),Xi.std(0)+1e-9; Z=np.column_stack([np.ones(len(Xi)),(Xi-mu)/sd])
    tg={}
    for c in ab["circuits"]: tg[("c",c)]=TR["circ"][c-1]["T"]
    if ab["power"]: tg[("p",0)]=TR["power"]
    W={k:np.linalg.solve(Z.T@Z+1e-3*np.eye(Z.shape[1]),Z.T@Y) for k,Y in tg.items()}
    def apply(X):
        X={k:(v.copy() if hasattr(v,"copy") else v) for k,v in X.items()}; X["circ"]=[{k:v.copy() for k,v in c.items()} for c in X["circ"]]
        Zx=np.column_stack([np.ones(len(X["OA"])),(_inputs(X,ab)-mu)/sd])
        for (t,c),w in W.items():
            if t=="c": X["circ"][c-1]["T"]=Zx@w
            else: X["power"]=Zx@w
        return X
    return apply
def unsupported(rec,ab):
    if rec is None: return False
    s=rec["stat"][0] if len(rec["stat"])==1 else "max"; b=rec[f"branch_{s}"]
    if b=="joint": return bool(ab["circuits"] or ab["power"])
    if b=="power": return ab["power"]
    return rec[f"circuit_{s}"] in ab["circuits"]
R={}
for s in P.SITES:
    TRd,CAd,TEd,Ud=P.site(s); TR,CA,TE,U=map(P.to_dict,(TRd,CAd,TEd,Ud)); full=P.GDetector().fit(TR,CA); R[s]={}
    for pat,(c,pw) in PAT.items():
        ab=absent(pat); r={}
        d=P.GDetector(circ=c,power=pw).fit(TR,CA)
        r["eligibility"]={"eligible_branches":sorted(d.ref),"test_dayFAR":P.frac(d.day_alarms(TE)),"fault_day_sens":P.frac(d.day_alarms(U)),"unsupported_attributions":0}
        if pat!="P0_full":
            TEi,Ui=impute(TE,ab,TR),impute(U,ab,TR)
            at,au=full.day_alarms(TEi),full.day_alarms(Ui)
            ua=sum(unsupported(x,ab) for x in attribute(full,TEi))+sum(unsupported(x,ab) for x in attribute(full,Ui))
            r["median_imputation"]={"test_dayFAR":P.frac(at),"fault_day_sens":P.frac(au),"unsupported_attributions":int(ua),"alarm_days_total":int(at.sum()+au.sum())}
            ap=reg_imputer(TR,ab); TEr,Ur=ap(TE),ap(U); at,au=full.day_alarms(TEr),full.day_alarms(Ur)
            ua=sum(unsupported(x,ab) for x in attribute(full,TEr))+sum(unsupported(x,ab) for x in attribute(full,Ur))
            r["regression_imputation"]={"test_dayFAR":P.frac(at),"fault_day_sens":P.frac(au),"unsupported_attributions":int(ua),"alarm_days_total":int(at.sum()+au.sum())}
        R[s][pat]=r; print(s,pat,r)
with open(OUT/"e11_field_eligibility.json","w") as fh: json.dump(R,fh,indent=1)

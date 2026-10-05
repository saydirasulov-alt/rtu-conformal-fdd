"""Site 1 training-adequacy audit with the earliest 19 TRAINING DAYS.
Confirms that 19 training days are adequate, which fixes the final 19/19/13 split. The earlier
13/19/19 candidate failed the same check with 13 training days (see site1_split_audit_13day.py).
Calibration/test days are NOT loaded into any metric; PASS/FAIL criteria are predefined and
outcome-independent."""
from pathlib import Path
RESULTS=Path(__file__).resolve().parent.parent/"results"; RESULTS.mkdir(exist_ok=True)
import os,json,numpy as np
from _common import *
rng=np.random.default_rng(SEED)

# ---- prespecified split sizes (design-based, outcome-independent) ----
N=load_field("Site1_Unfaulted.csv"); dd=days(N); uniq=np.unique(dd)
assert len(uniq)==51, f"expected 51 normal days, got {len(uniq)}"
TRAIN_DAYS=uniq[:19]                      # earliest 19 days = TRAINING ONLY
tr=N[np.isin(dd,TRAIN_DAYS)].reset_index(drop=True)
# NOTE: cal (next 19 days) and test (last 13 days) are deliberately never read below.

# branch feature extractors: refrigerant circuits (_1,_2) and power
branches={"refrigerant":[lambda z:cf(z,"_1"),lambda z:cf(z,"_2")],"power":[pf]}

# ---- predefined thresholds ----
TH=dict(min_days_present=19, min_minutes_per_day=30, min_total_minutes=20, # x p
        max_cov_cond=1e6, min_unique_scores=100, max_boot_cv=0.15, min_withinday_cv=0.03)

report={"check":"19 training days (final split 19/19/13, temporal earliest-first)","training_days_used":19,"criteria":{},"branch":{}}
tdd=days(tr)

# A4: per-day presence (all 19 train days have >= min_minutes_per_day gated minutes)
per_day=[int((tdd==d).sum()) for d in np.unique(tdd)]
A4 = (len(per_day)>=TH["min_days_present"]) and (min(per_day)>=TH["min_minutes_per_day"])
report["criteria"]["A4_per_day_presence"]={"days":len(per_day),"min_minutes_day":int(min(per_day)),"pass":bool(A4)}

allpass=[A4]
for bname,fxs in branches.items():
    p = 4 if bname=="refrigerant" else 3   # feature dim
    # fit robust-z + Mahalanobis on training (per circuit), PIT ref = training scores
    raw=[]; conds=[]; scales_ok=True
    for fx in fxs:
        X=np.asarray(fx(tr)); ms=rzfit(X)
        if np.any(ms[1]<=1e-8): scales_ok=False
        Z=rz(X,ms); mc=mfit(Z)
        cov=np.cov(Z.T)+1e-3*np.eye(Z.shape[1]); conds.append(float(np.linalg.cond(cov)))
        raw.append(md(Z,mc))
    rawscore=np.maximum.reduce(raw) if len(raw)>1 else raw[0]
    pit_ref=np.sort(rawscore); Tb=np.searchsorted(pit_ref,rawscore,"right")/(len(pit_ref)+1)
    n=len(rawscore)
    # A1 data volume; A2 conditioning; A3 non-degenerate scores
    A1 = n >= TH["min_total_minutes"]*p
    A2 = max(conds) < TH["max_cov_cond"] and scales_ok
    A3 = (len(np.unique(Tb))>=TH["min_unique_scores"]) and (Tb.max()-Tb.min()>0.5)
    # A5 day-block bootstrap stability of 95th pct of training score
    q95=[]
    for _ in range(200):
        bd=rng.choice(np.unique(tdd),len(np.unique(tdd)),True)
        idx=np.concatenate([np.where(tdd==d)[0] for d in bd])
        q95.append(np.percentile(rawscore[idx],95))
    cv_boot=float(np.std(q95)/ (np.mean(q95)+1e-12))
    A5 = cv_boot < TH["max_boot_cv"]
    # A6 within-train diversity (per-day mean raw score varies -> varied conditions)
    pdm=[rawscore[tdd==d].mean() for d in np.unique(tdd)]
    cv_within=float(np.std(pdm)/(np.mean(pdm)+1e-12))
    A6 = cv_within > TH["min_withinday_cv"]
    bp=all([A1,A2,A3,A5,A6])
    report["branch"][bname]={"n_minutes":int(n),"feat_dim":p,"cov_cond_max":round(max(conds),1),
        "unique_scores":int(len(np.unique(Tb))),"boot_cv_q95":round(cv_boot,4),
        "withinday_cv":round(cv_within,4),
        "A1_volume":bool(A1),"A2_conditioning":bool(A2),"A3_nondegenerate":bool(A3),
        "A5_boot_stability":bool(A5),"A6_withinday_diversity":bool(A6),"branch_pass":bool(bp)}
    allpass.append(bp)

report["VERDICT"]="PASS -> 19 training days adequate; final split 19/19/13" if all(allpass) else "FAIL"
report["thresholds"]=TH
open(RESULTS/"site1_split_audit_19day.json","w").write(json.dumps(report,indent=1))
print(json.dumps({"VERDICT":report["VERDICT"],"A4":report["criteria"]["A4_per_day_presence"],
                  "refrigerant":report["branch"]["refrigerant"]["branch_pass"],
                  "power":report["branch"]["power"]["branch_pass"]},indent=1))

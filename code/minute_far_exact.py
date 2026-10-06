"""Exact minute-level false-alarm under the primary day-calibrated threshold tau_day.
Report numerator/denominator and UNROUNDED rate (no premature rounding to 0.0%)."""
from pathlib import Path
RESULTS=Path(__file__).resolve().parent.parent/"results"; RESULTS.mkdir(exist_ok=True)
import os,json,numpy as np
from _common import *
ALPHA=0.05; rng=np.random.default_rng(SEED)
def fit_score(train):
    F=[]
    for fx in [lambda z:cf(z,"_1"),lambda z:cf(z,"_2"),pf]:
        ms=rzfit(np.asarray(fx(train))); mc=mfit(rz(fx(train),ms)); F.append((fx,ms,mc))
    rref=np.maximum(md(rz(F[0][0](train),F[0][1]),F[0][2]),md(rz(F[1][0](train),F[1][1]),F[1][2]))
    pref=md(rz(F[2][0](train),F[2][1]),F[2][2]); return F,np.sort(rref),np.sort(pref)
def score(df,F,rref,pref):
    r=np.maximum(md(rz(F[0][0](df),F[0][1]),F[0][2]),md(rz(F[1][0](df),F[1][1]),F[1][2])); p=md(rz(F[2][0](df),F[2][1]),F[2][2])
    return np.maximum(np.searchsorted(rref,r,"right")/(len(rref)+1),np.searchsorted(pref,p,"right")/(len(pref)+1))
def cq(s,a): n=len(s); k=min(int(np.ceil((1-a)*(n+1))),n)-1; return np.sort(s)[max(k,0)]
def daymax(df,sc): dd=days(df); return np.array([sc[dd==d].max() for d in np.unique(dd)])
def run(N,sizes,assign):
    dd=days(N); uniq=np.unique(dd); pm=rng.permutation(uniq) if assign=="random" else uniq
    a,b,_=sizes; TR=N[np.isin(dd,list(pm[:a]))]; CA=N[np.isin(dd,list(pm[a:a+b]))]; TE=N[np.isin(dd,list(pm[a+b:]))]
    F,rref,pref=fit_score(TR); tau=cq(daymax(CA,score(CA,F,rref,pref)),ALPHA)
    s=score(TE,F,rref,pref); num=int((s>tau).sum()); den=int(len(s))
    dmx=daymax(TE,s); dnum=int((dmx>tau).sum()); dden=int(len(dmx))
    return num,den,dnum,dden
out={}
for Nf,nm,sz in [("Site1_Unfaulted.csv","Site1",(19,19,13)),("Site2_Unfaulted.csv","Site2",(88,44,44))]:  # Site1 -> Site2, same order as the other scripts (one shared RNG)
    N=load_field(Nf)
    tn,td,tdn,tdd=run(N,sz,"temporal")
    out[nm+"_temporal"]={"min_num":tn,"min_den":td,"min_rate_pct":round(100*tn/td,4),
                         "day_num":tdn,"day_den":tdd,"day_rate_pct":round(100*tdn/tdd,2)}
    # randomized: aggregate exact minute counts across 30 splits
    rn=[]; rd=[]; rdf=[]
    for _ in range(30):
        n_,d_,dn_,dd_=run(N,sz,"random"); rn.append(n_); rd.append(d_); rdf.append(dn_/dd_)
    tot_n=sum(rn); tot_d=sum(rd)
    out[nm+"_random"]={"min_num_tot":tot_n,"min_den_tot":tot_d,"min_rate_pooled_pct":round(100*tot_n/tot_d,4),
                       "min_rate_meanof30_pct":round(float(np.mean([100*a/b for a,b in zip(rn,rd)])),4),
                       "day_rate_meanof30_pct":round(100*float(np.mean(rdf)),2)}  # cross-check vs primary_day_far.json
print(json.dumps(out,indent=1))
with open(RESULTS/"minute_exceedance_tau_day.json","w") as fh: json.dump(out,fh,indent=1)

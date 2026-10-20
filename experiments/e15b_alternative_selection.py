"""E15b (NOT pre-specified; added 2026-10-20 after A10.3 showed that a selection without the simulated
test days picks a different candidate). Reports, descriptively and whatever the outcome, how that
candidate (S3, daily mean, no joint branch) performs on the simulated holdout and the field units.
The frozen detector is unchanged."""
import os,json,numpy as np
from pathlib import Path
import phase2_common as P
from e15_audit_response import sim_sets,sim_eval,field_eval
A=P.A; OUT=Path(P.HERE)/"results"; R={}
TR,CA,TE,FH=sim_sets(); R["sim_holdout"]=sim_eval(A.Detector("S3","Dmean",False).fit(TR,CA),TE,FH)
for s in P.SITES:
    TRd,CAd,TEd,Ud=map(P.to_dict,P.site(s)); R[s]=field_eval(A.Detector("S3","Dmean",False).fit(TRd,CAd),TEd,Ud)
print(R); json.dump(R,open(OUT/"e15b_alternative_selection.json","w"),indent=1)

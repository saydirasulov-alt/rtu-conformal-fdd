# Conformal Fault Detection for Rooftop Units with Incomplete Sensing — Analysis Code

Reproduces the numerical results in the manuscript *"Conformal Fault Detection for Rooftop Units
with Incomplete Sensing."* NumPy + pandas only. Fixed seed `SEED = 20260618`.

## 1. Data
Publicly available **LBNL Fault Detection and Diagnostics Datasets** (DOI: **10.25984/1881324**).
Data are not redistributed here. Download them and arrange as:
```
<DATA_DIR>/
  Field RTU/   Site1_Unfaulted.csv  Site1_Staging_Fault.csv  Site2_Unfaulted.csv  Site2_Undercharged40.csv
  ORNL_RTU/    <ORNL experimental CSV files>
```
Then: `export RTU_DATA_DIR="/path/to/<DATA_DIR>"` (scripts exit with an error if it is unset).
Only compressor-on observations are used (gate = 200 W).

## 2. Environment
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt   # or, for the exact tested versions:
pip install -r requirements-lock.txt
```

## 3. Threshold convention (IMPORTANT)
All **primary** field results use the single day-calibrated threshold **tau_S^{day}** (the
(1-alpha) quantile of calibration-day maxima). A separate **minute-calibrated** threshold
**tau_S^{min}** defines a **secondary** detector reported only in the Supplementary Material.
The two are never mixed. Scripts and outputs are grouped accordingly below.

## 4. PRIMARY scripts (tau_S^{day}) and the manuscript numbers they reproduce

| Script | Reproduces (manuscript) | Output |
|---|---|---|
| `_common.py` | Shared helpers (loading, robust-z, Mahalanobis, PIT, splits) | — |
| `site1_split_audit_13day.py` | Site 1 training-adequacy audit, 13 training days -> **FAIL** (power-branch instability) | `site1_split_audit_13day.json` |
| `site1_split_audit_19day.py` | Same audit, 19 training days -> **PASS**; confirms the final **19/19/13** split | `site1_split_audit_19day.json` |
| `primary_day_far.py` | Day-level FAR under tau_S^{day}: Site 2 = 2.3% (temporal), Site 1 = 0/13; randomized means 3.0%/2.3% with 95% intervals [0,14.3]%/[0,21.7]% | `primary_day_far.json` |
| `minute_far_exact.py` | Exact minute-level exceedance ER_min^{day} under the **same** tau_S^{day}: Site 2 temporal 1/22,898 = 0.004%; Site 1 0/12,362 | `minute_exceedance_tau_day.json` |
| `sens_consistency.py` | Day- and minute-level fault sensitivity under the **same** tau_S^{day}: Site 2 = 48% (13/27) / 21% [9,34] (95% day-block bootstrap); Site 1 = 0% (0/62) / 0% | `sens_consistency.json` (primary); `supplementary_sens_tau_min.json` (tau_S^{min}, supplementary only) |
| `ornl_sensor_unavailability.py` | ORNL controlled sensor-unavailability: eligibility, abstention, zero unsupported assertions, fault-day sensitivity (94%/81%/94% = 15/16, 13/16, 15/16, ...), empirical minute-FAR 0.9-1.8% | `ornl_sensor_unavailability.json` |

## 5. SUPPLEMENTARY scripts (tau_S^{min}, secondary detector)

| Script | Reproduces (Supplementary Information) | Output |
|---|---|---|
| `supplementary_minute_detector.py` | Supplementary Note and Fig. S2, all on the same train/cal/test protocol: temporal minute-FAR Site 2 = 5.6%, Site 1 = 6.1%; randomized-day mean minute-FAR (30 splits) 4.7% / 5.2%; temporal minute fault sensitivity 34% [22,46] / 9% [5,13]; Site 2 temporal operating points 34% [22,46] at 5.6% FAR (alpha=0.05) and 43% [31,55] at 11.3% FAR (alpha=0.115) | `supplementary_minute_detector.json` |
| `sens_consistency.py` (second output) | Day- and minute-level sensitivity under tau_S^{min} (cross-check) | `supplementary_sens_tau_min.json` |

The `results/*.json` files are the canonical expected outputs; re-running with the LBNL data and the
fixed seed reproduces them.

## 6. Running
```bash
export RTU_DATA_DIR="/path/to/<DATA_DIR>"
bash run_all.sh
```

## 7. Notes
- Percentile transform: T_b = rank of g_b among the n_b training-normal scores divided by (n_b+1),
  as defined in the manuscript Methods; all branches of a unit share the same training rows, so this
  is a common rescaling that leaves alarm decisions unchanged.
- Scripts resolve `results/` relative to the repository, so they can be run from any directory.
- Seed `20260618`; compressor-on gate 200 W.
- Field branches: refrigerant (two circuits) + power. ORNL branches: economizer `{MA,OA,DMPR}`,
  supply-air `{MA,OA,SAT,SAF}` (OA is required because the supply-air features include MA-OA), power `{COMP,TOT,FAN}`; economizer branch covers the economizer and
  damper fault classes, supply-air branch covers the supply-air temperature-bias fault.
- ORNL has only 14 eligible normal days, so its thresholds are **minute-calibrated** (day-level
  calibration is infeasible there); ORNL detection is reported as fault-day sensitivity.

## License and citation
MIT License (see `LICENSE`). Citation metadata: `CITATION.cff`.
A Zenodo DOI will be added here after the first GitHub release is archived.

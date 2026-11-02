# Historical scripts and results (v1.0.x, single-statistic first version)

The numbers in this file belong to the first version of the method and are **not** the numbers of the current manuscript (see README.md).

The sections below document the first, single-statistic version (v1.0.0/v1.0.1). Its numbers are
*not* the numbers of the current manuscript.

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
| `minute_far_exact.py` | Exact minute-level exceedance ER_min^{day} under the **same** tau_S^{day}: Site 2 temporal 1/22,898 = 0.004%; Site 1 0/12,362. Randomized-day reference (same 30 splits as `primary_day_far.py`): Site 2 199/761,313 = 0.026%, Site 1 19/339,484 = 0.006% (pooled) | `minute_exceedance_tau_day.json` |
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
Linux / macOS:
```bash
export RTU_DATA_DIR="/path/to/<DATA_DIR>"
bash run_all.sh
```
Windows PowerShell:
```powershell
$env:RTU_DATA_DIR = "D:\path\to\<DATA_DIR>"
.\run_all.ps1
```
After a run, `git status` should show no changes under `results/` (byte-identical reproduction).

## 7. Notes
- Percentile transform: T_b = rank of g_b among the n_b training-normal scores divided by (n_b+1),
  as defined in the manuscript Methods; all branches of a unit share the same training rows, so this
  is a common rescaling that leaves alarm decisions unchanged.
- Scripts resolve `results/` relative to the repository, so they can be run from any directory.
- Seed `20260618`; compressor-on gate 200 W (applied before any sensor masking).
- Randomized-day splits: `primary_day_far.py`, `minute_far_exact.py` and `supplementary_minute_detector.py`
  each use one RNG seeded with `SEED`, process Site 1 before Site 2, and draw 30 splits per site, so
  they evaluate the same 30 random splits per site (`minute_exceedance_tau_day.json` also stores the randomized day-FAR
  mean as a cross-check: 2.31% / 2.95%).
- Field branches: refrigerant (two circuits) + power. ORNL branches: economizer `{MA,OA,DMPR}`,
  supply-air `{MA,OA,SAT,SAF}` (OA is required because the supply-air features include MA-OA), power `{COMP,TOT,FAN}`; economizer branch covers the economizer and
  damper fault classes, supply-air branch covers the supply-air temperature-bias fault.
- ORNL has only 14 eligible normal days, so its thresholds are **minute-calibrated** (day-level
  calibration is infeasible there); ORNL detection is reported as fault-day sensitivity.


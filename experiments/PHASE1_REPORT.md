# Phase-1 results (E1-E3), run 2026-10-13 on branch exp/phase1 (base v1.0.1)
All numbers: temporal splits (Site 2 88/44/44, Site 1 19/19/13), alpha = 0.05, thresholds from
calibration normal data only. Raw outputs: experiments/results/e1_baselines.json,
e2_detectability.json, e3_ablation.json.

## Finding 1 - Site 1 threshold is degenerate (hypothesis H-sat confirmed)
tau_day(Site 1) = 0.999928 = n/(n+1), the largest attainable PIT value (n = 13,838 training minutes).
An alarm requires T > tau, which is impossible. The reported Site 1 results (0/13 day-FAR,
0/62 fault days) are therefore structural, not evidence of calibration or of non-detectability.
Site 2 is not affected (tau 0.999920 < ceiling 0.999980).

## Finding 2 - Site 1 fault is weakly observable for the branch scores
Day-max AUC (fault vs normal test days): system 0.31, refrigerant 0.50, power 0.21.
Post-hoc oracle (diagnostic only, uses labels): at most 23% of fault days separable at 0 test FAR.
EXPLORATORY tie-aware PIT (no tuning) recovers only 1/62 days -> the tie is not the only cause.

## Finding 3 - Equal false-alarm budget comparison (rule C, same calibration rule)
| Method | Site 2 day-FAR | Site 2 fault days | Site 1 day-FAR | Site 1 fault days |
|---|---|---|---|---|
| Proposed (branch PIT) | 1/44 | 13/27 (48.1%) | 0/13* | 0/62* |
| Global Mahalanobis (11 features) | 2/44 | 1/27 (3.7%) | 0/13 | 13/62 (21.0%) |
| PCA T2 | 2/44 | 1/27 (3.7%) | 6/13 | 5/62 (8.1%) |
| PCA SPE | 0/44 | 5/27 (18.5%) | 0/13 | 0/62 |
| Isolation Forest | 1/44 | 10/27 (37.0%) | 0/13 | 0/62 |
*degenerate threshold (Finding 1).

## Finding 4 - Conventional thresholds do not control day-level false alarms
Train-99th-percentile (and chi2_0.99) thresholds: normal-test day-FAR 70-100% for every method at
both sites. Minute-calibrated threshold on the proposed score: 11/13 and 44/44 normal test days alarm.

## Finding 5 - Component ablation (field)
No PIT (max of raw branch scores): Site 2 0/27. No branch structure (global Mahalanobis): Site 2 1/27.
=> branch-wise PIT normalization is what gives the Site 2 sensitivity; day-level calibration is what
gives day-level false-alarm control. Global (cross-branch) covariance is what detects the Site 1 fault.

## Finding 6 - ORNL without eligibility (median imputation of missing sensors)
Imputation keeps minute-FAR similar (0.3-1.2%). Alarms attributed to a branch whose sensors are missing:
0% of alarm days in 4 patterns, 9.5% (4/42) in "no SA_TEMP". Note: with imputation the system still
raises alarms on fault days of classes whose own branch is ineligible (e.g. no DMPR: 12/16 economizer,
8/16 damper days) via other branches - these are anomaly alarms, not supported diagnoses.

## Decision per pre-registered rules
- Site 2: proposed is best at equal budget -> competitive.
- Site 1: a baseline detects (13/62 at 0/13) where the proposed cannot; cause = degenerate threshold
  plus loss of cross-branch signal. Any method change designed from this must be validated on data
  not used to design it; Site 1 has no such data. Report honestly; do not tune on Site 1.

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

---
# E4-E6 (run 2026-10-13, pre-registered addendum)

## E4 - Missing-sensor robustness (ORNL)
- Intermittent loss of DMPR, SAT or the power family at 5-40% of minutes changes fault-day detection
  by at most ~3 of 16 days; the affected branch's eligible-minute fraction falls as expected.
- Contiguous outages: 1 h and 6 h cost 0-2 fault days; a 24 h outage of DMPR or SAT makes the
  responsible branch ineligible all day -> those fault days are abstained (yield 0/16), others unaffected.
- Unsupported assertions: 0 in every condition. NOTE: this holds by construction (only eligible
  branches are scored); the check confirms the implementation, it is not an empirical finding.
- New fact to report: under the minute-calibrated ORNL threshold, 3 of 4 normal test days contain at
  least one false-alarm minute (minute-FAR ~1.2%). Day-level false alarms at ORNL are therefore high.

## E5 - Temporal stability (field) - MAJOR
- Exact 95% CIs: Site 2 day-FAR 1/44 [0.1, 12.0]%, sensitivity 13/27 [28.7, 68.1]%;
  Site 1 0/13 [0, 24.7]%, 0/62 [0, 5.8]% (degenerate threshold).
- The PIT-ceiling degeneracy is NOT specific to Site 1. Site 2 rolling-origin (60/30/14, 6 windows):
  5/6 windows have an unreachable threshold. Calibration-size sensitivity: n_cal = 19, 25, 30 are all
  degenerate (0/27 fault days); only the reported n_cal = 44 is not. The headline Site 2 result
  therefore depends on the calibration window.
- EXPLORATORY tie-aware PIT (fixed formula, defined in E3 before E5, no labels used): 0/6 degenerate
  windows; pooled rolling day-FAR 1/84 [0, 6.5]%; Site 2 sensitivity 11/27 for n_cal = 19-30 and
  13/27 for n_cal = 44 at 1/44 FAR; Site 1 1/62 at 0/13.

## E6 - Independent validation: NOT RUN (no independent dataset provided).

## Overall implication
The v1.0.1 primary detector has a structural flaw (PIT ties at the training maximum make the
day-level conformal threshold unreachable in most calibration windows). A tie-aware PIT removes the
flaw without changing Site 2's headline numbers. Adopting it is a method correction that should be
disclosed as such, released as a new code version, and ideally confirmed on independent data (E6).

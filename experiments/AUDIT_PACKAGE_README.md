# Audit package: Phase-1 (E1-E6) + Algorithm v2 - what to check and where

Branch exp/phase1 on top of v1.0.1 (commit f124c46). v1.0.1 code/results are untouched.
Reproduce everything: `RTU_DATA_DIR=<LBNL data> RTU_SIM_DIR="<Simulated RTU folder>" python experiments/run_phase_all.py`
then `python experiments/algo_v2_develop.py`, `python experiments/algo_v2_evaluate.py`, `python experiments/equal_far_posthoc.py`.
Dependencies beyond v1.0.1: scipy, scikit-learn. All runs are deterministic (seed 20260618).

## Commit history (chronological; plans precede results)
- 2749dc3 Phase-1 pre-registered plan (E1-E3)          -> 6350a53 E1-E3 results + report
- b17f97c addendum E4-E6 (pre-registered)               -> d394360 E4-E6 results, runner
- 7bff8bf ALGO_PLAN_V2 (pre-registered)                 -> 1e37604 Amendment 1 (FAR admissibility; disclosed)
- 4f9287e v2 FROZEN                                     -> 5e1bded one-time evaluation + ALGO_V2_REPORT

## Answers to the auditor's four Site-1 questions
1. Tie-aware PIT: defined in e3_ablation.py (A0x) BEFORE E5 was run, with a fixed formula and no tunable
   parameter: T = n/(n+1) + (1/(n+1))*(1 - m/x) for x > m (m = training max). It is labeled EXPLORATORY in
   E3/E5. It was adopted as a design choice for v2 and the v2 selection was on simulated data only.
   Its Site 1 effect alone is 1/62 (E3, E5), i.e. it does not explain the 84%.
2. v2 components were selected on the simulated DEV scenarios (ALGO_PLAN_V2, algo_v2_develop.py);
   field labels were not used in selection. Caveat (stated in ALGO_V2_REPORT): the field outcomes under v1
   were known to the designers beforehand; the 4-way grid was fixed in the plan before scoring.
3. Site 1: 52/62 at 1/13 test day-FAR (exact 95% CI for FAR [0.2, 36.0]%). Site 2: 19/27 at 4/44.
4. No new independent fault sequence exists (E6 not run). Simulated HOLDOUT fault types (never used in
   selection) are the only confirmatory data: 70.0% vs 36.7% (v1-like), same baseline FAR 2/25.

## Equal-FAR comparison (post-hoc diagnostic; uses test labels; not deployable) - results/equal_far_POSTHOC.json
Fault days detected when the threshold is set to allow at most k normal test-day alarms:
| Detector | Site 2 AUC | S2 @0/44 | S2 @1/44 | S2 @2/44 | S2 @4/44 | Site 1 AUC | S1 @0/13 | S1 @1/13 |
|---|---|---|---|---|---|---|---|---|
| v1.0.1 original | 0.746 | 0 | 13 | 13 | 13 | 0.310 | 0 | 0 |
| v1 tie-aware | 0.750 | 11 | 13 | 13 | 13 | 0.318 | 7 | 7 |
| v2 FROZEN | 0.838 | 7 | 10 | 18 | 20 | 0.892 | 43 | 56 |
| global Mahalanobis | 0.692 | 0 | 0 | 4 | 9 | 0.553 | 17 | 18 |
| Isolation Forest | 0.785 | 9 | 10 | 10 | 11 | 0.216 | 1 | 1 |
Reading: at Site 2 v2 dominates from 2/44 upward and has the best AUC, but at the strictest budgets
(0-1 false days) v1 tie-aware is better; v2's gain is partly a shift along the ROC curve. At Site 1 v2 is above every comparator at every k in 0..13 except k = 11 vs global Mahalanobis
(results/roc_dominance_POSTHOC.json); so 'dominates at every budget' is NOT strictly true - say 'at all
budgets up to 10/13 false days'.

## Known limitations to carry into the manuscript
- v2 day-mean statistic is drift-sensitive: Site 2 FAR 4/44, 7/44 with n_cal 19-25 (E5-style, ALGO_V2_REPORT).
- Guarantee is conditional on exchangeability of calibration/test days; state it that way.
- ORNL eligibility benefit vs imputation is small (0-9.5% unsupported attributions, E3); abstention concerns
  attribution, not alarm suppression.
- No second independent field RTU.

## ROC dominance check (post-hoc, full curves k = 0..n_test) - results/roc_dominance_POSTHOC.json
- Site 1: v2 >= v1 tie-aware and >= Isolation Forest at every k; v2 < global Mahalanobis only at k = 11.
- Site 2: v2 is NOT dominant. v2 < v1 tie-aware at k = 0, 1 (and k = 31-35); v2 < Isolation Forest at
  k = 0 and k = 21-35. v2 >= global Mahalanobis everywhere. v2's advantage at Site 2 is confined to
  k = 2..20 false days out of 44 - i.e. it is operating-point dependent and must be stated as such.
## Two numbers that must stay separate in the manuscript
- 52/62 (83.9%) at 1/13: real calibrated protocol (deployable result).
- 56/62 (90.3%) at k = 1: post-hoc threshold from test labels (diagnostic only; never a headline).

# Algorithm v2 - development and one-time frozen evaluation (2026-10-13)
Plan: ALGO_PLAN_V2.md (+ Amendment 1, disclosed). Raw: results/algo_v2_dev_grid.json,
algo_v2_FROZEN.json, algo_v2_EVALUATION.json.

FROZEN (selected on simulated DEV faults only): S0 features (v1.0.1 refrigerant-T + power) +
joint cross-branch branch + dual day statistic (max and mean, Bonferroni alpha/2 each), tie-aware PIT,
day-level conformal thresholds. Reference = v1-like (S0, day-max, no joint, tie-aware PIT).

| Evaluation | v1-like reference | FROZEN v2 |
|---|---|---|
| Sim DEV (12 scenarios, selection) mean sensitivity | 10.0% | 30.3% |
| Sim HOLDOUT (12 scenarios, never used) mean sensitivity | 36.7% | 70.0% |
| Sim baseline normal test day-FAR | 2/25 | 2/25 |
| Site 1 test day-FAR | 0/13 | 1/13 [0.2, 36.0] |
| Site 1 fault days (staging) | 1/62 | 52/62 [72.3, 92.0] |
| Site 2 test day-FAR | 1/44 | 4/44 [2.5, 21.7] |
| Site 2 fault days (undercharge) | 13/27 | 19/27 [49.8, 86.2] |
| Site 2 rolling-origin pooled day-FAR (6 x 14 d) | 1/84 | 3/84 [0.7, 10.1] |
| Site 2 n_cal = 19 / 25 / 30 / 44: FAR | 1/44 each | 7/44, 7/44, 4/44, 4/44 |
| Site 2 n_cal = 19 / 25 / 30 / 44: fault days | 11,11,11,13 /27 | 20,20,19,19 /27 |

Findings
1. Large, consistent sensitivity gains on held-out simulated faults (36.7% -> 70.0%) and on both field
   sites, at the same simulated FAR. Site 1 changes from undetectable to 84% of fault days.
2. Cost: the day-mean statistic is more sensitive to non-stationarity. Site 2 FAR rises to 4/44 and to
   7/44 with short calibration (19-25 days); 7/44 is significantly above alpha = 5% (one-sided exact
   binomial p ~ 0.004). The false-alarm guarantee holds only under exchangeable calibration/test days.
3. Weakness shared by both: simulated undercharge (10-20%) stays at ~4-16% of days; liquid/suction
   restriction at the smallest severity is undetected.
4. Confound check (field): fault days whose outdoor temperature lies inside the training 5-95% range
   alarm at least as often as other fault days (Site 1 0.88 vs 0.76; Site 2 0.71 vs 0.67), so detections
   are not explained by weather extrapolation. Fault episodes are in different calendar periods than
   the normal data; slower drift (e.g. equipment state) cannot be fully excluded.
5. Integrity notes: field fault outcomes were seen under v1.0.1 before this work; v2 was chosen on
   simulated data only. Amendment 1 used simulated baseline normal test days (no fault labels).

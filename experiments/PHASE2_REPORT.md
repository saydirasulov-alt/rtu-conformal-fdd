# Phase 2 report — supporting analyses for the frozen v2 detector

Plan: ANALYSIS_PLAN_PHASE2.md (committed ff8be45 before any Phase 2 outcome), amendments P2-A1..A4
listed there. Runner: `run_phase2_all.py`. All numbers below are copied from `results/e7..e13*.json`.
Consistency check passed: every detector count reproduces E1 / algo_v2_EVALUATION exactly.

## E13 Physics-based charge indicator
Identification (training data only): R-410A implausible at both sites (negative subcooling and
approach); R-22 and R-407C (gauge and absolute) plausible; rule selected R-22 / absolute pressure.
| | Site 1 FAR | Site 1 sens | Site 2 FAR | Site 2 sens |
|---|---|---|---|---|
| CI, day-level conformal | 4/13 | 19/62 | 0/44 | 5/27 |
| conventional SH/SC rule | 10/13 | 32/62 | 0/44 | 9/27 |
Across all plausible hypotheses (A1): conformal CI 3–4/13 & 19–41/62 (Site 1); 0/44 & 4–5/27 (Site 2).
Descriptive (Site 2): on fault days circuit 2 superheat median 55.9 K vs 29.1 K on normal test days,
subcooling 1.5 K vs 8.6 K — the classical undercharge signature on circuit 2.

## E7 Paired comparison (v2 vs comparator, McNemar exact, Holm)
Site 1, fault days: v2 better than every comparator, Holm p ≤ 3.6e-8. Normal days: no significant
difference (Holm p ≥ 0.875).
Site 2, fault days: v2 better than global Mahalanobis, PCA T², PCA SPE, physics CI (Holm p ≤ 6.1e-4)
and isolation forest (Holm p = 0.035); **not significant against v1 tie-aware / v1.0.1
(7 vs 1 discordant days, p = 0.070, Holm 0.141)**. Normal days: no significant difference.
Bootstrap 95% CI of the sensitivity gain vs v1 tie-aware at Site 2: +3.7 to +40.7 points.

## E8 Operational
TTFA (days into the fault record): Site 1 v2 day 1 (v1 tie-aware day 56; physics day 2);
Site 2 v2 day 1 (v1 day 9; IF day 6; physics day 15).
Expected false-alarm days per 30: v2 2.3 (Site 1, CI 0.06–10.8), 2.7 (Site 2, CI 0.75–6.5).
Longest normal alarm run: 1 day at both sites. Compute: fit 0.05–0.13 s, scoring one day ≈ 2 ms.
Site 1 alarm sequence ends with 6 quiet fault days (record days 57–62).

## E9 Attribution
Site 1 fault alarm days (52): joint branch 47, refrigerant 5; circuit 2 on 46 (88%) — documented
fault "Stage 2 will not engage". 51/52 alarm days involve the day-mean statistic.
Site 2 fault alarm days (19): refrigerant 11, joint 6, power 2; circuit 2 on 12 (63%) — documented
"Low Charge On Circuit B" (B ↔ suffix _2 assumed; E13 SH/SC supports it). The 4 normal-day false
alarms are all attributed to circuit 1.
E9b weather check: Site 1 fault days inside the training-day OA range 34/36 alarmed, outside 18/26.
Site 2 normal test days: inside range 2/42, **outside range 2/2** (both colder than any training day).

## E10 Robustness (one at a time) and E10b ridge sweep
alpha 0.10 / 0.20: FAR and sensitivity rise monotonically (Site 2 6/44 & 21/27; 10/44 & 21/27).
Gate 100 / 500 W: essentially unchanged. Ridge 1e-4: unchanged.
**Ridge 1e-2: Site 1 sensitivity falls to 9/62.** Sweep: 53/62 for ridge ≤ 3e-4, 52 at 1e-3, 46 at
2e-3, 41 at 3e-3, 30 at 5e-3, 9 at 1e-2, 5 at 3e-2; Site 2 stable (19–20/27). The joint training
covariance has two exact null directions (derived DISC−SUCT features) and a third eigenvalue of
8.7e-4 (Site 1) loading on total power and circuit-2 discharge temperature/lift; the staging fault
moves the data along this near-invariant direction, so a ridge larger than that eigenvalue removes it.
The frozen ridge 1e-3 was inherited from v1.0.1, not tuned.

## E11 Field eligibility (static sensor-group loss)
| pattern | eligibility FAR / sens | median imputation FAR / sens / unsupported | regression imputation FAR / sens / unsupported |
|---|---|---|---|
| S1 no circuit 2 | 0/13, 3/62 | 13/13, 62/62, 75 | 0/13, 4/62, 2 |
| S1 no circuit 1 | 2/13, 12/62 | 11/13, 52/62, 62 | 1/13, 5/62, 0 |
| S1 no power | 1/13, 11/62 | 13/13, 62/62, 75 | 1/13, 43/62, 34 |
| S1 power only | 4/13, 10/62 | 13/13, 62/62, 75 | 0/13, 3/62, 2 |
| S2 no circuit 2 | 3/44, 9/27 | 14/44, 19/27, 31 | 2/44, 7/27, 3 |
| S2 no circuit 1 | 4/44, 15/27 | 13/44, 21/27, 22 | 2/44, 15/27, 0 |
| S2 no power | 3/44, 17/27 | 9/44, 19/27, 16 | 2/44, 14/27, 3 |
| S2 power only | 5/44, 7/27 | 8/44, 15/27, 20 | 0/44, 5/27, 0 |
Median imputation inflates false alarms (up to 13/13); regression imputation does not and sometimes
detects more (Site 1 no-power 43/62) but then attributes 34 of 44 alarm days to a branch whose sensors
are absent. Losing circuit 2 at Site 2 costs more sensitivity (9/27) than losing circuit 1 (15/27).

## E12 Sensor faults injected into real normal test days (37 scenarios per site)
Mean new-alarm rate on days that were quiet without injection: Site 2 v2 62.3% vs v1 19.1%,
SPE 14.0%, IF 8.0%, Mahalanobis 2.4%, T² 0.0%; Site 1 v2 25.5% vs ≤ 4.8% for all others.
Scenarios alarmed on a majority of test days: Site 2 v2 24/37 (v1 6, SPE 4, others 0);
Site 1 v2 9/37 (T² 4 — with clean FAR 6/13 —, v1 1, Mahalanobis 1). Small biases (±0.5 IQR) and
stuck suction sensors are mostly missed at both sites.

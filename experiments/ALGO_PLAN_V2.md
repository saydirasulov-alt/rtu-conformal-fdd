# Algorithm development plan v2 (pre-registered 2026-10-13, before any candidate is scored)

Goal: a stronger detector that keeps eligibility + day-level conformal calibration.
Integrity rule: field Site 1/Site 2 fault outcomes were already seen under v1.0.1, so the
algorithm is chosen ONLY on simulated development data, frozen, then evaluated once on
(a) held-out simulated fault types and (b) the field sites. All results reported as obtained.

## Data
Development: LBNL simulated RTU (EnergyPlus-Modelica; single circuit; 1-min; 2018-07-20..10-28;
baseline + 24 fault simulations sharing the baseline weather). Compressor-on gate 200 W.
Baseline days split temporally: train = days 1-50, calibration = days 51-75 (25 days), test = days 76-end.
Fault scenarios are scored only on the test-date window.
- DEV faults (selection): condenser fouling 10-50%, liquid-line restriction 1-10 bar, overcharge 10-20%.
- HOLDOUT faults (never used for selection): evaporator fouling 10-50%, suction-line restriction
  1-9 bar, undercharge 10-20%.
The legacy LBNL RTU.csv (ORNL lab, condenser fouling) has no fault-free days and cannot be calibrated;
it is not used.

## Feature groups (names mapped per dataset)
refrigerant temperatures: condensing, discharge, suction, discharge-minus-suction (per circuit)
refrigerant pressures: discharge, suction (per circuit)
power: compressor, total, supply-fan
operating conditions (regressors only): outdoor-air temperature, return-air temperature

## Candidate grid (24 candidates)
Scoring S:
- S0 v1.0.1 branches {refrigerant-T, power}, static robust-z Mahalanobis, tie-aware PIT
- S1 S0 with pressures added to the refrigerant branch
- S2 condition-aware residuals: each feature regressed (ridge, lambda = 1e-3, train only) on
     [1, OA, RA, OA^2, OA*RA]; Mahalanobis on robust-z residuals; tie-aware PIT
- S3 S2 with pressures
Day statistic D (same statistic on calibration and test days):
- Dmax  max of minute system scores
- Dmean mean of minute system scores
- Ddual alarm if Dmax > tau_max(alpha/2) OR Dmean > tau_mean(alpha/2)  (Bonferroni)
Joint branch J: {no, yes = additional all-feature Mahalanobis branch, eligible only when all present}
alpha = 0.05; day-level conformal threshold = ceil((n+1)(1-alpha))-th order statistic.

## Selection rule (on DEV only)
Maximize mean fault-day sensitivity over the 12 DEV scenarios. Report baseline test day-FAR for all.
Ties (within 1 percentage point) broken by simplicity: S0<S1<S2<S3, Dmax<Dmean<Ddual, no J<J.

## Frozen evaluation (once)
1. Simulated HOLDOUT scenarios: fault-day sensitivity; baseline test day-FAR.
2. Field Site 2 and Site 1 (two circuits; refrigerant branch = max over circuits as in v1.0.1),
   same temporal splits as v1.0.1, plus E5-style rolling-origin and n_cal sensitivity (Site 2).
3. Comparison against v1.0.1 and the E1 baselines on the same data.

## Amendment 1 (2026-10-13, after the DEV grid was scored - disclosed, not hidden)
The original selection rule maximized DEV sensitivity without a false-alarm validity constraint.
The DEV grid showed that condition-aware residual candidates with a day-mean statistic (S2/S3 with
Dmean/Ddual) reach ~91% DEV sensitivity but alarm on 12-13 of 25 normal baseline test days, i.e.
their calibration is invalid under the seasonal drift between calibration and test windows; their
"sensitivity" is therefore not attributable to the faults. Amended rule: a candidate is admissible
only if its baseline normal test day-FAR count is not significantly above alpha (exact one-sided
binomial test at 5%, n = 25: count <= 3). Among admissible candidates, the original rule applies.
Caveat: the admissibility check uses simulated baseline normal test days (no fault labels); the
holdout FAR reported later is therefore not fully independent of selection. Field evaluation is.

# Phase-1 analysis plan (pre-registered before any Phase-1 result is computed)

Date: 2026-10-13. Base: release v1.0.1 (commit f124c46). Branch: exp/phase1.
Nothing in v1.0.1 code/results is modified; new scripts live in experiments/.

## Fixed protocol (identical to v1.0.1)
- Data: LBNL FDD datasets; compressor-on gate 200 W; same feature definitions.
- Field splits (temporal, earliest-first): Site 2 88/44/44 days, Site 1 19/19/13 days.
- ORNL split: same fixed-seed 7/3/4 day split as v1.0.1.
- alpha = 0.05. All models fit on TRAIN normal data only; all thresholds from CAL normal data only.
- Fault labels are never used to fit models or select thresholds. Any analysis that uses fault
  labels to choose a threshold is labeled "post-hoc oracle (diagnostic only)" and is never
  reported as a deployable result.

## E2 - Site 1 detectability (and Site 2 for contrast)
1. Day-max score distributions (normal test days vs fault days) for system and each branch.
2. AUC of day-max scores, fault days vs normal test days (threshold-free separability).
3. Feature-level shift: (median_fault - median_normal_test) / IQR_train for each feature.
4. Post-hoc oracle curve: day-level sensitivity vs normal-test day-FAR (diagnostic only).
Pre-stated hypothesis H-sat: the PIT transform saturates day-max scores near n/(n+1), so tau_day
is close to "exceeds every training score"; this may make the detector conservative.

## E1 - Baselines on identical features, splits and calibration data (field sites)
Features: refrigerant circuits 1 and 2 (4 features each) + power (3) = 11 features.
- B1 Global Mahalanobis on all 11 features (robust-z on train, ridge 1e-3) - no branches, no PIT.
- B2 PCA (components explaining 95% train variance): B2a Hotelling T2, B2b SPE (Q).
- B3 Isolation Forest (200 trees, random_state = SEED); score = -score_samples.
Threshold rules for every baseline:
- (C) conformal day-level: same order-statistic rule on CAL day-max scores (same budget as proposed).
- (U) conventional: 99th percentile of TRAIN minute scores (B1 additionally chi2_0.99, df=11).
Metrics: temporal normal-test day-FAR (count), fault-day sensitivity (count), minute-level
sensitivity, minute-level normal exceedance. Proposed detector numbers recomputed from v1.0.1 code.

## E3 - Component ablation
Field: A0 proposed; A1 no PIT (max of raw branch scores); A2 no branch structure (= B1 under rule C);
A3 minute calibration tau_min instead of tau_day.
ORNL eligibility: for each sensor-unavailability pattern, a "no-eligibility" variant imputes missing
sensors with TRAIN medians and scores all branches. Report normal-test minute FAR, fault-day alarm
rate, and unsupported assertions = fault-day alarms whose triggering branch lacks required sensors.

## Decision rules (stated before results)
- If a baseline under rule (C) achieves equal-or-lower day-FAR with clearly higher sensitivity at
  both sites, the proposed scoring is not competitive; report this and reconsider the method.
- If all methods fail at Site 1 and E2 shows near-zero separability (AUC ~ 0.5, small shifts),
  report Site 1 as an observability limit of the available sensing.
- If baselines detect Site 1 but the proposed detector does not, investigate (H-sat) before any
  change; any change found this way must be validated on data not used to design it.
- Results are reported whichever way they come out.

---
# Addendum (2026-10-13, written before E4/E5/E6 are computed)

## E4 - Missing-sensor robustness (ORNL; frozen 7/3/4 split, alpha = 0.05)
Masks are applied to TEST normal and FAULT data only (calibration uses complete data).
Per minute, eligibility S(x_t) is recomputed from the sensors present at that minute; the minute is
compared with the threshold tau_S^min calibrated on CAL minutes for that exact set S; if S is empty
the minute abstains. Sensors masked (one at a time): DMPR, SAT, and the power family {COMP,TOT,FAN}.
- Intermittent missingness: each minute masked independently with probability 5, 10, 20, 40%.
- Temporary outage: one contiguous outage per day of 1 h, 6 h or 24 h, start uniformly random
  within the day (24 h = whole day).
Random masks use numpy default_rng(SEED). Metrics: eligible-minute fraction of the fault's branch,
abstention rate on fault minutes, eligible fault-day sensitivity (fault days with >= 1 eligible minute
for the responsible branch), detection yield over all fault days, false-alarm days per monitored
normal test day, and unsupported assertions (alarm minutes attributed to an ineligible branch; 0 by
construction - verified, not assumed).

## E5 - Temporal calibration stability (field, primary detector)
1. Exact Clopper-Pearson 95% CIs for every day-level FAR and fault-day sensitivity reported.
2. Rolling-origin evaluation, Site 2: train 60 / cal 30 / test 14 consecutive days, origin shifted
   by 14 days until data run out; report per-window day-FAR, tau, and threshold-degeneracy flag
   (tau equal to the PIT ceiling).
3. Calibration-size sensitivity, Site 2: train = first 88 days, test = last 44 days, calibration =
   the n_cal days immediately before the test block, n_cal in {19, 25, 30, 44}.
4. Site 1 (51 days) admits only the single 19/19/13 design; its degeneracy is reported, no rolling.

## E6 - Independent validation hook
Runs only if an additional dataset is placed under $RTU_DATA_DIR/Independent/ with a manifest
(manifest.json: normal file, fault file, column mapping) that is written BEFORE the data are scored.
Otherwise the runner records "not run: no independent dataset provided". No result is fabricated.

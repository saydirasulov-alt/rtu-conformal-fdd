# Analysis plan — Phase 2 (supporting analyses for the frozen v2 detector)

Written and committed **before** any Phase 2 outcome was computed. Phase 1 (E1–E6) and the
v2 development/evaluation (ALGO_PLAN_V2.md, Amendment 1) were already known when this plan
was written; every analysis below is therefore *secondary/supporting*. None of them may change
the frozen detector (S0 / Ddual / J=True, alpha=0.05, gate 200 W, ridge 1e-3). The detector
reported as primary in the manuscript stays the frozen one whatever these analyses show.

Common settings: seed 20260618; field splits Site 1 19/19/13 days, Site 2 88/44/44 days
(train/cal/test, temporal); loader `algo_v2.load_field` (verified to give rows identical to
`code/_common.load_field`, so E1 numbers must be reproduced exactly — consistency check).
Exact (Clopper–Pearson) 95% intervals for all proportions.

## E7 Paired statistical comparison (field)
Detectors, all under the day-level conformal rule C on identical train/cal/test days:
v2 FROZEN; v1 tie-aware (REF); v1.0.1 original; global Mahalanobis; PCA T²; PCA SPE;
isolation forest (as E1); physics charge indicator (E13, only if identifiable).
- Consistency check: per-detector counts must equal E1 / algo_v2_EVALUATION.
- McNemar exact test (two-sided binomial on discordant days), v2 vs each comparator,
  separately on fault days (detected) and normal test days (alarmed). Holm adjustment across
  comparators within site × endpoint. Report discordant counts, exact p, Holm p.
- Day bootstrap (B=5000): paired difference v2 − comparator in fault-day sensitivity
  (resampling fault days) and in normal-day FAR (resampling test days); percentile 95% CI.
  This reflects test-day sampling only, not calibration variability (stated as such).

## E8 Operational metrics
- Time to first alarm (TTFA): index (1-based) of the first alarm day in each field fault record,
  counted from the first day of the record (documented fault start: Site 1 2021-06-09,
  Site 2 2020-06-01), for every E7 detector. Day-level decisions are taken at end of day, so
  latency is reported in days.
- Expected false-alarm days per 30 operating days = 30 × test FAR, with exact CI.
- Longest run of consecutive alarm days on normal test days.
- Computational cost: wall time of fit and of scoring one day, median of 5 repeats, machine
  reported. Indicative only.

## E9 Branch and circuit attribution (isolation evidence)
For each alarm day of v2 (fault and normal test days): triggering statistic(s) (max / mean);
per-branch day statistics A^max_{d,b}, A^mean_{d,b} from the branch PIT values; attributed
branch b* = argmax_b of the triggering statistic (if both trigger, both are reported).
Circuit attribution: per-circuit PIT with per-circuit training references (refrigerant
branch), c* = argmax_c of the same day statistic; reported for every alarm day, including
joint-attributed days. Documented faults: Site 2 "Low Charge On Circuit B"; Site 1
"Stage 2 will not engage". The mapping Circuit B ↔ data suffix _2 is an assumption (stated).
Attribution is a post-hoc diagnostic tool; it does not alter alarms.

## E10 Robustness of the frozen configuration (one-at-a-time, post hoc)
alpha ∈ {0.05*, 0.10, 0.20}; compressor gate ∈ {100, 200*, 500} W; covariance ridge
∈ {1e-4, 1e-3*, 1e-2} (* = frozen). Outputs: simulated holdout mean sensitivity and baseline
test FAR; Site 1 and Site 2 test FAR and fault-day sensitivity. Reported as sensitivity
analysis; no value is selected from this grid.

## E11 Field eligibility (sensor-group unavailability), Site 1 and Site 2
Static patterns over the whole evaluation: P0 full; P1 circuit-2 refrigerant sensors absent
(refrigerant branch = circuit 1, joint ineligible); P2 circuit-1 absent; P3 power sensors
absent (power and joint ineligible); P4 all refrigerant sensors absent (power branch only).
Eligibility: branch models/references refitted on training data for the pattern's eligible
branches, thresholds from the same calibration days under that pattern.
Imputation comparator: absent sensors replaced by their training median; full P0 detector and
thresholds applied. For both: test FAR, fault-day sensitivity, and "unsupported attributions"
= alarm days whose attributed branch (E9 rule) uses an absent/imputed sensor.

## E12 Fault injection on real normal field data (semi-synthetic sensor faults)
Carrier: normal **test** days only (Site 2: 44; Site 1: 13); training and calibration untouched.
Injection on raw columns before feature construction (derived DISC−SUCT recomputed).
The compressor-on gate is evaluated on the uncorrupted power signal (stated simplification).
Sensors: circuit-1 suction temp, discharge temp, liquid-line temp; compressor power.
- Temperature sensors: bias +k·IQR_train, k ∈ {−2, −1, −0.5, 0.5, 1, 2}; linear drift from 0 to
  k·IQR_train across the test period, k ∈ {1, 2, 4}; stuck at its first test-period value.
- Compressor power: multiplicative error s ∈ {−0.2, −0.1, −0.05, 0.05, 0.1, 0.2}; stuck.
37 scenarios per site. Detectors as E7 (excluding v1.0.1 and physics). Metrics: alarm rate on
injected days, alarm rate of the same days without injection (paired), and first alarm day.
Purpose: evidence on data-integrity faults of sensors that eligibility treats as present
(addresses the stated limitation); not a claim about equipment faults.

## E13 Physics-based charge indicator baseline
Refrigerant and pressure-reference identification (field documentation names neither):
hypotheses {R-22, R-410A, R-407C} × {gauge, absolute}. On training minutes with circuit c
running (discharge − suction pressure > 3 bar), compute superheat SH = T_suct − T_sat(P_suct),
subcooling SC = T_sat(P_disc) − T_liquid (discharge pressure used as condensing pressure),
condensing approach = T_sat(P_disc) − T_OA. A hypothesis is plausible if median SH ∈ [2,25] K,
median SC ∈ [0,20] K, median approach ∈ [3,30] K and fraction SH<0 < 5%, in both circuits.
If several are plausible, the one with the smallest fraction (SH<0)+(SC<0) is used; if none,
the baseline is reported as not identifiable and dropped. Saturation properties: CoolProp.
Charge indicator per running circuit CI_c = z(SH_c) − z(SC_c) (robust z from training);
minute score = max over running circuits. Two detectors: (i) conventional rule — day alarm if
any minute has SH > train p99 and SC < train p1 in the same circuit; (ii) CI under the same
day-level dual conformal rule (day max and day mean, alpha/2 each) on the same calibration days.

## Theory (manuscript, no computation)
Propositions with proofs: (1) eligibility ⇒ no unsupported branch attribution; (2) per-pattern
dual-statistic day-level bound ≤ alpha, and = 2/(n_S+1) attained bound when k = n_S;
(3) tie-aware PIT is strictly increasing in the raw score and yields alarm decisions identical
to the plain PIT whenever tau < n_b/(n_b+1).

## Reporting rule
All Phase 2 results are reported, including unfavourable ones. Any deviation from this plan is
listed as an amendment with its reason before the corresponding result is used.

## Amendments
**P2-A1 (E13, added after the identification step and before the alternative hypotheses were
evaluated).** The identification rule found more than one plausible hypothesis at both sites
(R-22 and R-407C, gauge and absolute; R-410A implausible everywhere). The pre-specified tie rule
selects R-22/absolute at both sites, and that remains the reported baseline. Because the choice is
not unique, the two physics detectors are additionally evaluated under every plausible hypothesis
and the range is reported, so that the comparison does not rest on one refrigerant assumption.

**P2-A2 (E10, added after the E10 grid).** With ridge 1e-2, Site 1 fault-day sensitivity fell
from 52/62 to 9/62, while the other settings changed little. To characterise rather than hide this,
a finer descriptive ridge sweep {1e-5, 1e-4, 3e-4, 1e-3, 2e-3, 3e-3, 5e-3, 1e-2, 3e-2} is reported for
both field sites, together with the smallest eigenvalues of the joint-branch training covariance.
The frozen ridge (1e-3) was inherited unchanged from v1.0.1 and is not re-selected.

**P2-A3 (E9, added after E9/E10b).** Because Site 1 detection relies on a near-invariant
direction of the joint covariance, a weather-confound check is added for both sites: v2 alarm rate
on fault days whose daily-mean outdoor temperature lies inside vs outside the range of training-day
means, and the same for normal test days.

**P2-A4 (E11, added after the median-imputation result).** Median imputation is a weak comparator.
A regression ("virtual sensor") imputation is added: each absent feature is predicted by ridge
regression (lambda 1e-3, standardised inputs) from all available sensor features plus outdoor- and
return-air temperature, fitted on training days; the full P0 detector and thresholds are then applied
exactly as for median imputation. Both comparators are reported.

**P2-A5 (added 2026-10-16, after review of the manuscript, before computing it).** Equal false-alarm
budget. The generic comparators and v1 use a single day-maximum threshold at alpha (effective bound
1/(n+1) when the threshold is the calibration maximum), while the frozen detector uses two statistics
at alpha/2 (bound 2/(n+1)); at Site 1 and on the simulated RTU the frozen detector therefore had the
larger budget. Every comparator (global Mahalanobis, PCA T2, PCA SPE, isolation forest, v1 tie-aware)
is re-evaluated with exactly the frozen detector's rule: daily maximum and daily mean of its own
minute score, each thresholded at alpha/2 on the same calibration days, alarm if either exceeds.
Reported for both field sites (FAR, sensitivity, McNemar vs frozen with Holm) and, for v1 tie-aware,
on the simulated holdout. The frozen detector is unchanged.

**P2-A6 (same date, before computing).** Condition-dependent physics reference. Superheat and
subcooling of each running circuit are regressed on training data on outdoor- and return-air
temperature and compressor power (linear, ridge 1e-3, standardised inputs); the charge indicator is
built from the residuals (z(res_SH) - z(res_SC), robust training z, maximum over running circuits)
and evaluated with the same two-statistic day-level rule. Same refrigerant hypothesis as E13.

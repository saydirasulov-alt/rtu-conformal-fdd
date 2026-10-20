# Response to the external audit of the JOBE draft (2026-10-20)

Each audit point is listed with our assessment (agree / partly / disagree), what was changed, and where the
change is. The new analyses were pre-specified as amendment P2-A10 in `ANALYSIS_PLAN_PHASE2.md` (commit
9744e89) before they were computed (commit 1311b3e). Results are in `results/e15_audit_response.json`.
`results/e15b_alternative_selection.json` is the one analysis that was not pre-specified.

| Point | Assessment | Change |
|---|---|---|
| Reproducibility (v1.1.0/Zenodo claimed, README outdated) | **Agree.** The manuscript claimed a release that did not exist. | README rewritten for v1.1.0, with a map from manuscript items to scripts, reproduction status and `RESULTS_SHA256.txt`. **Still open:** the release, the Zenodo DOI and the Phase 2 rerun on the second computer. The Code availability text becomes true only once the release exists. |
| M1 marginal vs conditional guarantee; binomial p as a check | **Agree.** | Method section: the marginal bound, the conditional exceedance (Beta(1,n), above alpha/2 with probability 0.33 at n=44 and 0.62 at n=19) and the observed frequency are now defined separately. All binomial tests of the bound were removed (p=0.13, 0.006, 0.15, 0.049). |
| M2 pseudoreplication | **Agree.** | A10.1: lag-1 autocorrelation, n_eff and circular block bootstrap (Table S14). The text says the 89 fault days are two dependent records and McNemar is descriptive. Block intervals were close to the exact ones. |
| M3 attribution vs "always circuit 2" | **Agree.** | The claim is reduced to "diagnostic pointer". Site 2 12/19 vs coin: p=0.18 (stated). A10.2 mirrored injections give balanced accuracy 94.1% (Site 2) and 87.9% (Site 1) vs 50% for always-circuit-2 (Table S16). These are sensor faults, not equipment faults (stated). |
| M4 test-data contamination | **Agree, and it mattered.** | A10.3: without the test days, a different candidate is selected (S3, mean only, no joint). Not pre-specified (E15b): that candidate flags 12/25 simulated test days, 0/27 Site 2 and 54/62 Site 1. Disclosed in Section 4.3 and Limitations. Field data were never used for selection. |
| M5 ridge | **Partly** (already analysed; mechanism now tested further). | A10.4: without the D−S feature the zero eigenvalues disappear, but Site 1 still drops to 8/62 at ridge 1e-2, so the dependence is not a collinearity artefact. The spectrum ridge stays a sensitivity analysis and is not swapped in. |
| M6 within-day pattern changes | **Agree.** | Day-pattern rule stated in Methods (A10.6). Field intermittent loss: 10–40% random loss gives no change in false alarms and 18/25 and 52/61 scored fault days; with a 6 h outage, 13–15/25 and 50/61. Zero alarms on missing sensors. |
| M7 power gate | **Agree.** | ORNL row renamed. Table 5 caption and Limitations state that the gate always uses measured compressor power. |
| M8 two episodes, small undercharge, retrospective | **Agree** (mostly already stated). | Limitations strengthened. No new data available (A9 Mendeley still pending). |
| M9 baselines | **Agree.** | A10.5: max-only, mean-only, two-day persistence and EWMA for the frozen detector and Mahalanobis (Table 7). No rule dominates. |
| M10 sensor vs equipment fault; Figure 6 density | **Agree.** | Figure 6 moved to the Supplement (Figure S1) and replaced by summary Table 4. The text keeps the sensor-fault caveat. |
| Prop. 1 m_b > 0 | **Agree.** | Assumption added to the statement and the proof; the degenerate case is explained. |
| Tail extension arbitrary | **Agree.** | A10.8: exponential extension gives identical counts. |
| Joint statistic J_d | **Agree** (good suggestion). | A10.7: Site 1 bound 10% → 5%, 51/62 and 1/13; Site 2 6/44 and 20/27 (bound 4.4%); sim 0/25 and 67.3%. Recommended for new deployments; not substituted, because it was designed post hoc. Note: the plan said "1/(n+1)", which holds for n=19 but not n=44 (k=43, bound 2/45); the manuscript reports the correct values. |
| S1–S13 "not in PDF" | **Disagree.** They are in the separate Supplementary Material PDF. | — |
| Second-computer reproduction "unverified" | **Partly.** The log exists (`REPRODUCTION_REPORT_PC_2026-10-14.md`) but covers E1–E6 and v2 only. | README states the scope. |
| Contributions too many | **Agree.** | Reduced to two. |

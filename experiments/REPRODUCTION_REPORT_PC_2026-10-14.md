# Independent reproduction report — Phase 1 (E1–E6) and Algorithm v2

Date: 2026-10-14 (Asia/Seoul)
Machine: author's Windows PC, `C:\Users\Gee\rtu-conformal-fdd` (clone of saydirasulov-alt/rtu-conformal-fdd at v1.0.1, commit f124c46), miniconda Python.
Data: `D:\projectlar\modality_gated_diagnosis\data` (LBNL FDD Field RTU, ORNL RTU, Simulated RTU).
Reference: cloud-side run (branch `exp/phase1`, commits 2749dc3 … 52a21ec), results JSON in `experiments/results/`.

## What was run on the PC

| Script | Status | Compared against | Result |
|---|---|---|---|
| `run_phase_all.py` (E1–E6) | ran earlier today | `results/e1..e6*.json`, `SUMMARY.json` | all printed numbers identical |
| `algo_v2_develop.py` (24-candidate grid, Amendment 1 in-script) | ran | `algo_v2_dev_grid.json`, `algo_v2_FROZEN.json` | all 24 rows identical (FAR and DEV mean sens); FROZEN = S0 / Ddual / J=True, DEV 30.3%, baseline FAR 2/25 |
| `algo_v2_evaluate.py` | ran | `algo_v2_EVALUATION.json` | identical: holdout 70.0 vs 36.7; Site 1 52/62 @ 1/13 (REF 1/62 @ 0/13); Site 2 19/27 @ 4/44 (REF 13/27 @ 1/44); rolling 3/84 (REF 1/84); n_cal 19/25/30/44 → FAR 7/7/4/4 of 44 |
| `equal_far_posthoc.py` | ran | `equal_far_POSTHOC.json` | identical (all AUCs and k-matched counts) |
| `roc_dominance_posthoc.py` | ran | `roc_dominance_POSTHOC.json` | identical: Site 1 v2 below Mahalanobis only at k=11; Site 2 v2 below v1-tie-aware at k=0,1,31–35 and below IF at k=0,21–30,33–35 |

Scripts were transferred by pasting their text into PowerShell here-strings (`Set-Content -Encoding UTF8`); chat-card downloads were not working on the PC today. File sizes on the PC are 4 bytes larger than the cloud copies (UTF-8 BOM). Result JSONs differ from the cloud copies in line endings only (CRLF); every printed value is identical.

## Incidents during reproduction (disclosed)

1. **Incomplete simulated dataset on the PC.** The PC's `Simulated RTU` folder initially held 10 of the 25 CSVs (baseline + 9 scenarios). `algo_v2_develop.py` failed with FileNotFoundError on `RTU_sim_condfouling10.csv`. The 15 missing scenarios were extracted from the original `LBNL_FDD_Data_Sets_RTU.zip` (305,603,469 bytes) already present on the PC, giving 25 files; the scripts were then re-run. No script was modified and no scenario list was shortened.
2. **Two wrong "expected values" in the assistant's chat message** before the run: it stated baseline test FAR "1/25" (correct: 2/25) and rolling pooled FAR "7/84" (correct: 3/84; 7/44 is the n_cal=19 figure). These errors were in the chat text only; the stored JSONs and the PC output agree with each other. Manuscript and audit documents use only the JSON values.
3. `algo_v2_develop.py` as first committed (b95d287) lacked the Amendment 1 admissibility filter; a fresh run would have selected S2/Dmean. Fixed in-script in commit 52a21ec before this reproduction; the PC ran the fixed version and reproduced the FROZEN configuration.

## Items still open

- `e6_independent.py` is a hook and has not been run (no independent dataset identified).
- No GitHub push, no v1.1.0 release, no new Zenodo DOI until the auditor's GO.
- `code/` and `results/` (v1.0.1) are unchanged (`git diff --stat main -- code results` empty on the PC).

## Interpretation points carried into the manuscript

- v2 gains are structural (tie-aware PIT, dual day statistic, joint branch) and are large on the simulated holdout (36.7 → 70.0%) and at Site 1 (1 → 52 of 62 fault days). At Site 2 the gain (13 → 19 of 27) comes with FAR 1 → 4 of 44; the post-hoc ROC shows v1 ahead at k=0,1 and v2 ahead from k≥2 (AUC 0.838 vs 0.750). The word "dominates" is not used.
- Simulated mild undercharge (10–20%) is essentially undetected by either version (2–4/25 days); the detected field fault at Site 2 is a 40% undercharge.
- Site 1 FAR 1/13 has CI 0.2–36%; the attained bound with 19 calibration days is 2/20 = 10%, not the nominal 5%.
- Rolling-origin FAR 3/84 (CI 0.7–10.1%) is consistent with nominal; calibration windows of 19–25 days raise FAR to 7/44.

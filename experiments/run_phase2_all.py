"""Run all Phase 2 analyses in order (ANALYSIS_PLAN_PHASE2.md). Needs RTU_DATA_DIR and RTU_SIM_DIR."""
import subprocess,sys,os,time
HERE=os.path.dirname(os.path.abspath(__file__))
for s in ["e13_physics.py","e7_e8_paired_operational.py","e9_attribution.py","e9b_weather_confound.py","e10_robustness.py","e10b_ridge_sweep.py","e11_field_eligibility.py","e12_injection.py","e14_equal_budget.py","e12b_injection_equal_budget.py","e10c_ridge_spectrum.py","e15_audit_response.py","e15b_alternative_selection.py","e15c_minimum_minutes.py"]:
    t=time.time(); print(f"\n##### {s}",flush=True); r=subprocess.run([sys.executable,os.path.join(HERE,s)],cwd=HERE)
    if r.returncode: sys.exit(f"{s} failed")
    print(f"##### {s} done in {time.time()-t:.0f}s",flush=True)

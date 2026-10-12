"""v0.3.6.2 combined regression and GPU acceptance gate.

Combines 141 stable v0.2.34 tests with 92 adaptive-retention tests in one
unittest process. Existing GPU and legacy acceptance checks are optional.
"""
import argparse
import subprocess
import sys
import unittest
from verify_release_candidate_v02334 import LEGACY, CURRENT

ADAPTIVE = [
    "test_adaptive_context_v023350",
    "test_adaptive_retention_eval_v023351",
    "test_retention_cross_scenario_v0300",
    "test_hybrid_retention_v0310",
    "test_adaptive_importance_v0320",
    "test_auto_pin_protection_v0330",
    "test_important_competition_v0340",
    "test_admission_forgetting_v0350",
    "test_retention_shadow_v0360",
    "test_retention_shadow_gpu_accept_v0361",
]
EXPECTED = 233

def run_unit_gate():
    modules = LEGACY + CURRENT + ADAPTIVE
    suite = unittest.defaultTestLoader.loadTestsFromNames(modules)
    discovered = suite.countTestCases()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
    ok = result.wasSuccessful() and not result.skipped and discovered == EXPECTED and result.testsRun == EXPECTED
    print(f"[combined-unit] passed={passed} run={result.testsRun} expected={EXPECTED} ok={ok}",flush=True)
    return ok

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--gpu",action="store_true",help="run both multi-process GPU acceptances")
    parser.add_argument("--legacy",action="store_true",help="run legacy conditional semantic regression")
    parser.add_argument("--timeout",type=int,default=240)
    args=parser.parse_args()
    if args.timeout<=0:
        parser.error("--timeout must be positive")
    ok=run_unit_gate()
    subprocesses=[
        ("RECOVERY_GPU",["context_recovery_gpu_accept_v023344.py","--timeout",str(args.timeout)],args.gpu),
        ("SHADOW_GPU",["retention_shadow_gpu_accept_v0361.py","--timeout",str(args.timeout)],args.gpu),
        ("LEGACY",["verify_conditional_runtime_stable_v10165.py"],args.legacy),
    ]
    for name,cmd,enabled in subprocesses:
        if not enabled:
            continue
        try:
            result=subprocess.run([sys.executable,*cmd],timeout=args.timeout*8,check=False)
            success=result.returncode==0
            print(f"[{name}] exit={result.returncode} pass={success}",flush=True)
        except subprocess.TimeoutExpired:
            success=False
            print(f"[{name}] TIMEOUT",flush=True)
        ok=ok and success
    print("INTEGRATION_GATE_V0362_PASS" if ok else "INTEGRATION_GATE_V0362_FAIL")
    return 0 if ok else 1

if __name__=="__main__":
    sys.exit(main())

"""LLM_CHA v0.3.6.6 264-case unified release-candidate regression.

233 previous stable/research tests + 12 active context + 9 active GPU harness
+ 10 grounded revisit tests. GPU harnesses are optional but independently run.
"""
import argparse
import subprocess
import sys
import unittest
from verify_release_candidate_v02334 import LEGACY,CURRENT
from verify_integration_v0362 import ADAPTIVE

ACTIVE=["test_active_topic_context_v0363",
        "test_active_retention_gpu_accept_v0364",
        "test_grounded_revisit_v0365"]
EXPECTED=264

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--gpu",action="store_true")
    parser.add_argument("--legacy",action="store_true")
    parser.add_argument("--timeout",type=int,default=240)
    args=parser.parse_args()
    if args.timeout<=0:parser.error("--timeout must be positive")
    suite=unittest.defaultTestLoader.loadTestsFromNames(LEGACY+CURRENT+ADAPTIVE+ACTIVE)
    discovered=suite.countTestCases()
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    ok=result.wasSuccessful() and not result.skipped and discovered==EXPECTED and result.testsRun==EXPECTED
    print(f"[unified-unit] expected={EXPECTED} discovered={discovered} run={result.testsRun} pass={ok}",flush=True)
    steps=[
        ("RECOVERY_GPU","context_recovery_gpu_accept_v023344.py",args.gpu),
        ("SHADOW_GPU","retention_shadow_gpu_accept_v0361.py",args.gpu),
        ("ACTIVE_GPU","active_retention_gpu_accept_v0364.py",args.gpu),
        ("REVISIT_GPU","grounded_revisit_gpu_v0366.py",args.gpu),
        ("LEGACY","verify_conditional_runtime_stable_v10165.py",args.legacy),
    ]
    for label,script,enabled in steps:
        if not enabled:continue
        cmd=[sys.executable,script]
        if label!="LEGACY":cmd += ["--timeout",str(args.timeout)]
        try:
            code=subprocess.run(cmd,check=False,timeout=args.timeout*8).returncode
        except subprocess.TimeoutExpired:
            code=-1
        print(f"[{label}] exit={code} pass={code==0}",flush=True)
        ok=ok and code==0
    print("INTEGRATION_GATE_V0366_PASS" if ok else "INTEGRATION_GATE_V0366_FAIL")
    return 0 if ok else 1

if __name__=="__main__":sys.exit(main())

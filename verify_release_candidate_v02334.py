"""LLM_CHA v0.2.34 stable-candidate release gate.

Run the previous 94 cases and the new 47 cases in ONE Python unittest process.
Then optionally run the GPU and legacy compatibility subprocess checks.
No data/model paths are changed by the unit-test runner itself.
"""
import argparse
import subprocess
import sys
import unittest

LEGACY = [
    "test_multi_topic_context_v0233821",
    "test_conversation_topic_adapter_v0233822",
    "test_multi_topic_chat_runtime_v0233823",
    "test_truth_aware_chat_integration_v0233824",
    "test_learning_init_v02338241",
    "test_grounded_followup_v0233825",
    "test_grounded_expansion_v0233826",
    "test_expansion_integration_v0233826",
    "test_proposition_truth_v0233827",
    "test_truth_integration_v0233827",
    "test_proposition_review_v0233828",
    "test_mixed_state_e2e_v0233829",
    "test_mixed_state_gpu_accept_v02338210",
]
CURRENT = [
    "test_longterm_context_v02340",
    "test_context_restore_validation_v023341",
    "test_corpus_restore_adapter_v023342",
    "test_context_recovery_v023343",
    "test_context_recovery_integration_v023343",
    "test_context_recovery_gpu_accept_v023344",
    "test_context_recovery_hardening_v023345",
]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--gpu",action="store_true",help="also run three-process GPU acceptance")
    parser.add_argument("--legacy",action="store_true",help="also run legacy conditional semantic regression")
    args=parser.parse_args()
    suite=unittest.defaultTestLoader.loadTestsFromNames(LEGACY+CURRENT)
    discovered=suite.countTestCases()
    runner=unittest.TextTestRunner(verbosity=2)
    result=runner.run(suite)
    passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped)
    unit_ok=result.wasSuccessful() and result.testsRun==141 and discovered==141
    print(f"[unit-gate] passed={passed} run={result.testsRun} expected=141 ok={unit_ok}",flush=True)
    ok=unit_ok
    for requested, label, command in [
        (args.gpu,"GPU",["context_recovery_gpu_accept_v023344.py","--timeout","240"]),
        (args.legacy,"LEGACY",["verify_conditional_runtime_stable_v10165.py"]),
    ]:
        if not requested:
            continue
        child=subprocess.run([sys.executable,*command],check=False)
        status=child.returncode==0
        print(f"[{label}] exit={child.returncode} pass={status}",flush=True)
        ok=ok and status
    print("RELEASE_GATE_V02334_PASS" if ok else "RELEASE_GATE_V02334_FAIL")
    return 0 if ok else 1

if __name__=="__main__":
    sys.exit(main())

import unittest
from retention_shadow_gpu_accept_v0361 import signature,COMPARE_PREFIXES

class ShadowGpuHarnessTests(unittest.TestCase):
    def test_signature_preserves_truth_and_answer(self):
        transcript = (
            "AI> 【未検証の記録】宇宙は膨張している。\n"
            "[proposition-id=abc, truth_state=UNVERIFIED]\n"
            "[retrieval-first=HIT]\n")
        self.assertEqual(len(signature(transcript)),3)

    def test_shadow_diagnostics_excluded(self):
        transcript=(
            "[adaptive retention shadow enabled; routing unchanged]\n"
            '{"capacity": 8, "mode": "shadow"}\n'
            "AI> 同一応答\n")
        self.assertEqual(signature(transcript),["AI> 同一応答"])

    def test_truth_warning_retained(self):
        self.assertEqual(signature("[truth warning: state=UNVERIFIED]\n"),
                         ["[truth warning: state=UNVERIFIED]"])

    def test_checkpoint_events_retained(self):
        self.assertEqual(signature("[context-save=OK, topics=1]\n"
                                   "[context-load=OK, retained=2, rejected=0]\n"),
                         ["[context-save=OK, topics=1]",
                          "[context-load=OK, retained=2, rejected=0]"])

    def test_differences_visible(self):
        self.assertNotEqual(signature("AI> A\n"),signature("AI> B\n"))

    def test_does_not_consider_full_startup_log(self):
        self.assertEqual(signature("Device : cuda\nGPU: RTX\n"),[])

if __name__=="__main__":
    unittest.main()

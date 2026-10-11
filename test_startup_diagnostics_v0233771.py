import unittest
from chat_runtime_benchmark_v023377 import diagnose_failure,evaluate_transcript
class StartupDiagnosticsTests(unittest.TestCase):
    def test_python_exception(self):
        d=diagnose_failure("Traceback (most recent call last):\nFileNotFoundError: missing model","",1)
        self.assertEqual(d["reason"],"python_exception")
        self.assertIn("FileNotFoundError",d["exception_line"])
    def test_missing_module(self):
        d=diagnose_failure("No module named 'torch'","",1)
        self.assertEqual(d["phase"],"STARTUP_ERROR")
    def test_timeout(self):
        self.assertEqual(diagnose_failure("","",None,True)["phase"],"TIMEOUT")
    def test_no_prompt(self):
        self.assertEqual(diagnose_failure("","startup",0)["reason"],"no_chat_prompt")
    def test_ready_for_evaluation(self):
        self.assertEqual(diagnose_failure("","startup\nYou> ",0)["phase"],"EVALUATION")
    def test_nonzero_generic(self):
        self.assertEqual(diagnose_failure("error","",1)["reason"],"nonzero_exit")
    def test_stale_transcript_not_pass(self):
        self.assertEqual(evaluate_transcript("",1)["passed"],0)
if __name__=="__main__":unittest.main()

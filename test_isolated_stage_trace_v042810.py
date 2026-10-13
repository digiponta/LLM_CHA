"""v0.4.28.10 synthetic tests of isolated trace wiring and no-op default."""
import unittest
from pathlib import Path
class StageTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture=(Path(__file__).parent/"capture_chat_benchmark_v04283.py").read_text(encoding="utf-8")
        cls.wrapper=(Path(__file__).parent/"trace_chat_runtime_v042810.py").read_text(encoding="utf-8")
    def test_opt_in_only(self):
        self.assertIn('ap.add_argument("--trace-stages",action="store_true"',self.capture)
        self.assertIn('if args.trace_stages else "chat.py"',self.capture)
    def test_separate_staged_trace_file(self):
        self.assertIn('trace_path=root/"results"',self.capture)
        self.assertIn('"LLM_CHA_STAGE_TRACE":str(trace_path)',self.capture)
        self.assertIn('if args.trace_stages and trace_path.exists()',self.capture)
    def test_passthrough_generation(self):
        self.assertIn('result=original(*args,**kwargs)',self.wrapper)
        self.assertIn('return result',self.wrapper)
        self.assertIn('chat.generate_reply=traced',self.wrapper)
    def test_explicit_trace_path_and_no_overwrite(self):
        self.assertIn('LLM_CHA_STAGE_TRACE must be explicitly set',self.wrapper)
        self.assertIn('if destination.exists()',self.wrapper)
    def test_trace_not_causal_proof(self):
        self.assertIn('"retrieval_status":"NOT_OBSERVED"',self.capture)
        self.assertIn('"stage_trace_enabled":args.trace_stages',self.capture)
if __name__=="__main__":unittest.main()

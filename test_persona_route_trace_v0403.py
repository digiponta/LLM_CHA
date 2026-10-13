import tempfile
import unittest
from pathlib import Path
from persona_route_trace_v0403 import diagnose

class PersonaRouteTraceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"source.txt"
        self.path.write_text("数学は文学の分類。\n量子力学について考える。",encoding="utf-8")
    def tearDown(self):self.temp.cleanup()
    def test_raw_corpus_hit(self):
        x=diagnose(self.path,"BLOCK","RAW_CORPUS_ONLY","文学")
        self.assertTrue(x["persona_rescue_hit_possible"])
    def test_unknown_with_evidence_not_rescued(self):
        x=diagnose(self.path,"BLOCK","UNKNOWN","文学")
        self.assertGreater(x["ranked_evidence_count_max_2"],0)
        self.assertFalse(x["persona_rescue_hit_possible"])
        self.assertIn("state_not_RAW_CORPUS_ONLY",x["non_hit_reasons"])
    def test_unknown_without_evidence(self):
        x=diagnose(self.path,"BLOCK","UNKNOWN","小説")
        self.assertEqual(x["ranked_evidence_count_max_2"],0)
    def test_truth_block(self):
        x=diagnose(self.path,"BLOCK","RAW_CORPUS_ONLY","文学","BLOCK")
        self.assertFalse(x["persona_rescue_hit_possible"])
    def test_verification_override(self):
        x=diagnose(self.path,"BLOCK","RAW_CORPUS_ONLY","文学",force_verification=True)
        self.assertFalse(x["persona_rescue_hit_possible"])
    def test_retrieve_does_not_rescue(self):
        x=diagnose(self.path,"RETRIEVE","CANONICAL","文学")
        self.assertFalse(x["persona_rescue_hit_possible"])
    def test_no_mutation(self):
        before=self.path.read_bytes()
        diagnose(self.path,"BLOCK","UNKNOWN","文学")
        self.assertEqual(before,self.path.read_bytes())
    def test_chat_wiring(self):
        s=Path("chat.py").read_text(encoding="utf-8")
        self.assertIn("LLM_CHA_PERSONA_ROUTE_TRACE",s)
        self.assertIn("persona_route_diagnose(",s)
        self.assertIn('force_internalized_verification,',s)
if __name__=="__main__":unittest.main()

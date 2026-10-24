import tempfile
import unittest
from pathlib import Path
from unapproved_llm_intake_v074446 import _save
from unapproved_fallback_v0803 import fallback_on_failure

class SemanticFallbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"knowledge.json"
        _save(self.path,{"candidates":[{
            "id":"a","subject":"量子ビット",
            "natural_language":"量子ビットは量子情報の基本単位である。",
            "source":"https://ja.wikipedia.org/wiki/量子ビット",
            "state":"UNAPPROVED","truth_state":"EXTERNAL_UNVERIFIED",
            "semantic_candidate":{"status":"STRUCTURED","subject":"量子ビット",
                                  "relation":"is_basic_unit","object":"基本単位"}}]})
    def test_not_needed_when_success(self):
        self.assertEqual(fallback_on_failure("量子ビットとは",False,self.path)["status"],"NOT_NEEDED")
    def test_grounded_fallback(self):
        result=fallback_on_failure("量子ビットとは",True,self.path)
        self.assertEqual(result["status"],"FOUND")
        self.assertFalse(result["train_ready"])
        self.assertIn("未検証",result["answer"])
        self.assertIn("出典",result["answer"])
    def test_no_match_no_hallucination(self):
        self.assertEqual(fallback_on_failure("数学とは",True,self.path)["status"],"NO_FALLBACK")
    def test_runtime_integration(self):
        text=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn("UNAPPROVED_SEMANTIC_FALLBACK",text)
if __name__=="__main__":unittest.main()

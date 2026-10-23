import json,tempfile,unittest
from pathlib import Path
from audit_experimental_sleep_v0725 import sha256,evaluate_rows

class AuditV0725Tests(unittest.TestCase):
    def test_hash_change_detected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"a"
            p.write_text("before")
            a=sha256(p)
            p.write_text("after")
            self.assertNotEqual(a,sha256(p))
    def test_missing_approved_is_valid_empty_store(self):
        from dual_semantic_memory_v071 import DualMemory
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            approved=root/"approved_v071.jsonl"
            candidate=root/"candidates_v071.jsonl"
            m=DualMemory(approved,candidate)
            m.propose("質問","答え","test")
            self.assertFalse(approved.exists())
            self.assertEqual(m.approved(),[])
            self.assertIsNone(sha256(approved))
    def test_missing_hash(self):
        self.assertIsNone(sha256("/nonexistent/llm-cha-0725-test"))
    def test_compare_counts(self):
        import sys,types
        fake=types.ModuleType("dual_inference_v075")
        def generate(model,tok,q,route,n):
            return "A" if route=="experimental" else "B"
        fake.generate=generate
        prior=sys.modules.get("dual_inference_v075")
        sys.modules["dual_inference_v075"]=fake
        try:
            result=evaluate_rows(None,None,[{"question":"q","answer":"A"}])
            self.assertEqual(result["experimental_exact"],1)
            self.assertEqual(result["base_exact"],0)
        finally:
            if prior is None:sys.modules.pop("dual_inference_v075",None)
            else:sys.modules["dual_inference_v075"]=prior
if __name__=="__main__":unittest.main()

import unittest
from compare_qa_shadows_v042827 import compare

class Tests(unittest.TestCase):
    def fixture(self):
        v={"records":[{"id":f"T{i:02d}","turn":1,"question":"GPUって何？",
            "final_answer":"GPUは並列演算を行う処理装置。" if i%2 else "未学習です",
            "gate_resolution":"ACCEPT","candidate_alignment":"SINGLE_TURN_CONFIRMED",
            "literal_probe_identity":False,"manual_review":{}} for i in range(64)]}
        l={"schema":"llm_cha_chatgpt_qa_v1","label_source":"chatgpt","decisions":[
            {"id":f"T{i:02d}","turn":1,"relevant":i%2==1,"reason":"暫定"} for i in range(64)]}
        c={"records":[{"id":f"T{i:02d}","turn":1,"gate_resolution":"ACCEPT",
          "semantic_agreement":0.85,"human_final_relevant":None} for i in range(64)]}
        return v,l,c
    def test_totals(self):
        r=compare(*self.fixture());self.assertEqual(r["total"],64)
        self.assertEqual(sum(r["matrix"].values()),64)
    def test_no_combined_gate(self):
        r=compare(*self.fixture());self.assertFalse(r["combined_reject_rule"])
        self.assertFalse(r["runtime_modified"])
    def test_label_independent_decisions(self):
        v,l,c=self.fixture();first=compare(v,l,c)
        for d in l["decisions"]:d["relevant"]=not d["relevant"]
        second=compare(v,l,c)
        self.assertEqual([(x["lexical_decision"],x["function_decision"]) for x in first["records"]],
                         [(x["lexical_decision"],x["function_decision"]) for x in second["records"]])
    def test_mismatched_gate_refused(self):
        v,l,c=self.fixture();c["records"][0]["id"]="BAD"
        with self.assertRaises(ValueError):compare(v,l,c)
    def test_no_holdout_claim(self):
        r=compare(*self.fixture());self.assertFalse(r["independent_holdout"])
        self.assertFalse(r["threshold_fitted"])
if __name__=="__main__":unittest.main()

import unittest
from analyze_chatgpt_qa_gate_v042824 import analyze
class Tests(unittest.TestCase):
    def fixture(self):
        records=[{"id":f"T{i:02d}","turn":1,"question":"本は好き？","final_answer":"好き。","gate_resolution":"ACCEPT",
                  "candidate_alignment":"SINGLE_TURN_CONFIRMED","literal_probe_identity":False,"manual_review":{}} for i in range(64)]
        v={"records":records}
        labels={"schema":"llm_cha_chatgpt_qa_v1","label_source":"chatgpt","decisions":[
          {"id":r["id"],"turn":1,"relevant":True,"reason":"適切"} for r in records]}
        c={"records":[{"id":r["id"],"turn":1,"gate_resolution":"ACCEPT","semantic_agreement":0.9,"human_final_relevant":None} for r in records]}
        return v,labels,c
    def test_positive(self):
        v,l,c=self.fixture();r=analyze(v,l,c)
        self.assertEqual((r["positive"],r["provisional_accepted_relevant"]),(64,64))
    def test_false_accept(self):
        v,l,c=self.fixture();l["decisions"][0]["relevant"]=False
        r=analyze(v,l,c);self.assertEqual(r["provisional_false_accept"],1)
    def test_null(self):
        v,l,c=self.fixture();l["decisions"][0]["relevant"]=None
        self.assertEqual(analyze(v,l,c)["uncertain"],1)
    def test_missing_gate(self):
        v,l,c=self.fixture();c["records"][0]["id"]="UNKNOWN"
        with self.assertRaises(ValueError):analyze(v,l,c)
    def test_human_separation(self):
        v,l,c=self.fixture();c["records"][0]["human_final_relevant"]=True
        with self.assertRaises(ValueError):analyze(v,l,c)
    def test_nonfinite_score(self):
        v,l,c=self.fixture();c["records"][0]["semantic_agreement"]=float("nan")
        with self.assertRaises(ValueError):analyze(v,l,c)
if __name__=="__main__":unittest.main()

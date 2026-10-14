import unittest
from chatgpt_qa_label_exchange_v042823 import export_packet,validate_labels

class Tests(unittest.TestCase):
    def fixture(self):
        v={"records":[{"id":f"T{i:02d}","turn":1,"question":"眠たい","final_answer":"少し休もう",
        "gate_resolution":"ACCEPT","candidate_alignment":"SINGLE_TURN_CONFIRMED",
        "literal_probe_identity":False,"manual_review":{}} for i in range(64)]}
        p=export_packet(v)
        labels={"schema":"llm_cha_chatgpt_qa_v1","label_source":"chatgpt",
        "decisions":[{"id":r["id"],"turn":r["turn"],"relevant":True,"reason":"質問に応えている"} for r in p["cases"]]}
        return p,labels
    def test_export_64(self):
        p,_=self.fixture();self.assertEqual(len(p["cases"]),64)
    def test_import_provenance(self):
        p,l=self.fixture();r=validate_labels(p,l)
        self.assertFalse(r["human_ground_truth"])
        self.assertEqual(r["positive"],64)
    def test_uncertain(self):
        p,l=self.fixture();l["decisions"][0]["relevant"]=None
        r=validate_labels(p,l);self.assertEqual(r["uncertain"],1)
    def test_duplicate_rejected(self):
        p,l=self.fixture();l["decisions"][0]=dict(l["decisions"][1])
        with self.assertRaises(ValueError):validate_labels(p,l)
    def test_no_human_masquerade(self):
        p,l=self.fixture();l["label_source"]="human"
        with self.assertRaises(ValueError):validate_labels(p,l)
    def test_missing_reason(self):
        p,l=self.fixture();l["decisions"][0]["reason"]=""
        with self.assertRaises(ValueError):validate_labels(p,l)
if __name__=="__main__":unittest.main()

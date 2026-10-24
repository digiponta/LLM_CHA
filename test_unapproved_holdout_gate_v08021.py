import unittest
from unapproved_holdout_gate_v08021 import formal_holdout_gate

TRAIN=[{"id":"t1","subject":"量子ビット","natural_language":"量子ビットは基本単位である。"}]

def valid(i):
    return {"id":"holdout-"+str(i),"question":"独立した質問"+str(i),
            "reference_answer":"独立した検証文"+str(i),
            "source_url":"https://example.org/reference/"+str(i),
            "source_excerpt":"独立した検証文"+str(i)}
class FormalHoldoutGateTests(unittest.TestCase):
    def test_placeholder_is_rejected(self):
        d={"independent_source_attested":False,"records":[
            {"id":"replace-with-independent-id","question":"ここに未学習の検証質問",
             "reference_answer":"ここに独立資料で確認した参照回答"}]}
        result=formal_holdout_gate(d,TRAIN,["t1"])
        self.assertEqual(result["status"],"NOT_READY")
        self.assertIn("INSUFFICIENT_RECORDS",result["reasons"])
        self.assertTrue(any(r.startswith("PLACEHOLDER_RECORD") for r in result["reasons"]))
    def test_small_set_rejected(self):
        result=formal_holdout_gate(
            {"independent_source_attested":True,"records":[valid(1)]},TRAIN,["t1"])
        self.assertEqual(result["status"],"NOT_READY")
        self.assertIn("INSUFFICIENT_RECORDS",result["reasons"])
    def test_source_required(self):
        rows=[valid(i) for i in range(5)]
        del rows[0]["source_url"]
        result=formal_holdout_gate({"independent_source_attested":True,"records":rows},TRAIN,["t1"])
        self.assertIn("SOURCE_MISSING:0",result["reasons"])
    def test_ready_is_not_verified(self):
        result=formal_holdout_gate(
            {"independent_source_attested":True,"records":[valid(i) for i in range(5)]},TRAIN,["t1"])
        self.assertEqual(result["status"],"READY")
        self.assertFalse(result["independence_verified"])
if __name__=="__main__":unittest.main()

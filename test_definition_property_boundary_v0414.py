import unittest
from evaluate_proposition_holdout_v0413 import evidence
from definition_property_boundary_v0414 import classify,DEFINITION,PROPERTY,ATTRIBUTED,CONTEXT
from evaluate_definition_boundary_v0414 import evaluate

def c(topic,text):
    return classify(evidence({"id":"diagnostic","concept":topic,"text":text}))

class BoundaryTests(unittest.TestCase):
    def kind(self,topic,text):
        return [x["classification"] for x in c(topic,text)["items"]]
    def test_definition(self):self.assertIn(DEFINITION,self.kind("GPU","GPUは並列処理装置である。"))
    def test_property(self):self.assertIn(PROPERTY,self.kind("宇宙","宇宙は広大である。"))
    def test_attribution(self):self.assertIn(ATTRIBUTED,self.kind("惑星","惑星は天体とされる。"))
    def test_context(self):self.assertIn(CONTEXT,self.kind("数学","数学は学問ではない。"))
    def test_naming_definition(self):self.assertIn(DEFINITION,self.kind("哲学","哲学を思考の営みという。"))
    def test_multiple_sentences(self):
        kinds=self.kind("CPU","CPUは演算装置である。しかし、別の説もある。")
        self.assertIn(CONTEXT,kinds)
    def test_evidence_spans(self):
        text="宇宙は広大である。"
        x=c("宇宙",text)["items"][0]
        self.assertEqual(text[x["evidence_start"]:x["evidence_end"]],x["literal"])
    def test_no_promotion(self):
        r=c("GPU","GPUは装置である。")
        self.assertEqual(r["truth_promotions"],0)
        self.assertEqual(r["semantic_memory_writes"],0)
        self.assertFalse(r["training_enabled"])
    def test_evaluation_totals(self):
        r=evaluate()
        self.assertEqual(r["total"],30)
        self.assertEqual(r["tp"]+r["fp"]+r["fn"]+r["tn"],30)
    def test_deterministic(self):self.assertEqual(evaluate(),evaluate())
if __name__=="__main__":unittest.main()

import unittest
from persona_quality_workflow_v0425 import reconcile

def capture(i,q,a):
    return {"id":i,"question":q,"answer":a,"agreement":.5,
            "semantic_agreement":.85,"runtime_accepted":True}
def reviewed(r, bad=False):
    return {**r,"split":"development","gold_inappropriate":bad,
            "label_source":"HUMAN_REVIEW"}
class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.a=capture("a","読書は好きですか","好き。")
        self.b=capture("b","最近は何を読んでいるの","わからない。")
    def test_pending_only_new(self):
        x=reconcile([self.a,self.b],[reviewed(self.a)])
        self.assertEqual(x["reused_labels"],1)
        self.assertEqual([r["id"] for r in x["pending"]],["b"])
        self.assertEqual(len(x["labeled"]),1)
    def test_new_annotation(self):
        x=reconcile([self.a],[ ],[{"id":"a","gold_inappropriate":False,"reviewer":"manual"}])
        self.assertEqual(x["newly_labeled"],1)
        self.assertEqual(x["pending_count"],0)
    def test_changed_capture_rejected(self):
        with self.assertRaisesRegex(ValueError,"changed"):
            reconcile([{**self.a,"answer":"changed"}],[reviewed(self.a)])
    def test_conflict_rejected(self):
        with self.assertRaisesRegex(ValueError,"conflicting"):
            reconcile([self.a],[reviewed(self.a,False)],
                      [{"id":"a","gold_inappropriate":True,"reviewer":"manual"}])
    def test_unexpected_old_id_rejected(self):
        with self.assertRaisesRegex(ValueError,"missing"):
            reconcile([self.a],[reviewed(self.b)])
    def test_invalid_annotation(self):
        with self.assertRaises(ValueError):
            reconcile([self.a],annotations=[{"id":"a","gold_inappropriate":1,"reviewer":"manual"}])
    def test_unreviewed_prior_rejected(self):
        old=reviewed(self.a);old["label_source"]="DEVELOPMENT_EXAMPLE"
        with self.assertRaises(ValueError):
            reconcile([self.a],[old])
    def test_no_automatic_holdout(self):
        x=reconcile([self.a,self.b])
        self.assertEqual(x["pending_count"],2)
        self.assertFalse(x["independent_holdout_claimed"])
if __name__=="__main__":unittest.main()

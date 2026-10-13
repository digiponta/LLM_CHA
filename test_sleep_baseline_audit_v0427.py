import unittest
from sleep_baseline_audit_v0427 import compare

def row(i,q,a):
    return {"id":i,"question":q,"answer":a,"agreement":0.5,
            "semantic_agreement":0.8,"runtime_accepted":True}

class SleepAuditTests(unittest.TestCase):
    def test_identical(self):
        x=[row("a","質問","回答")]
        r=compare(x,x)
        self.assertEqual(r["matched_questions"],1)
        self.assertEqual(r["changed_answers"],0)
        self.assertFalse(r["quality_improvement_claimed"])
    def test_changed(self):
        r=compare([row("a","質問","前")],[row("b","質問","後")])
        self.assertEqual(r["changed_answers"],1)
        self.assertTrue(r["rows"][0]["human_review_required"])
    def test_missing_question(self):
        with self.assertRaises(ValueError):
            compare([row("a","A","前")],[row("b","B","後")])
    def test_duplicate_question(self):
        with self.assertRaises(ValueError):
            compare([row("a","A","前"),row("b","A","前")],[row("c","A","後")])
    def test_empty(self):
        with self.assertRaises(ValueError):
            compare([],[])
    def test_no_mutation(self):
        old=[row("a","A","前")];new=[row("b","A","後")]
        a=dict(old[0]);b=dict(new[0])
        compare(old,new)
        self.assertEqual(old[0],a)
        self.assertEqual(new[0],b)
if __name__=="__main__":unittest.main()

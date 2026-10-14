import copy,unittest
from review_japanese_foundation_qa_v042840 import template,apply

def quality():
    return {"version":"v0.4.28.39","input_sha256":"abc",
      "candidates":[{"id":"JF-1","source":{"file":"source.txt","line":4},
        "answer":"私はコーヒーが好きです。","question":"あなたはコーヒーが好きですか。",
        "suggested_question":"コーヒーが好きですか。","gate_status":"HOLD"},
        {"id":"JF-2","source":{"file":"source.txt","line":5},
        "answer":"私は何者です。","gate_status":"REJECT"}]}
def reviewed():
    q=quality();r=template(q)
    row=r["reviews"][0]
    row.update({"decision":"ACCEPT","verified_question":"コーヒーが好きですか。","reviewer":"reviewer1","review_note":"原文を目視確認"})
    r["reviews"][1]["decision"]="REJECT"
    return q,r
class Tests(unittest.TestCase):
    def test_template_pending(self):
        self.assertEqual([r["decision"] for r in template(quality())["reviews"]],["PENDING","PENDING"])
    def test_approved_positive(self):
        q,r=reviewed();out=apply(q,r)
        self.assertEqual(out["accepted"],1)
        self.assertEqual(out["positives"][0]["source"]["line"],4)
        self.assertFalse(out["train_ready"])
    def test_reject_approval_prohibited(self):
        q,r=reviewed();r["reviews"][1].update({"decision":"ACCEPT","verified_question":"あなたは何者ですか。","reviewer":"x","review_note":"a"})
        with self.assertRaises(ValueError):apply(q,r)
    def test_source_mutation(self):
        q,r=reviewed();r["reviews"][0]["answer"]="変更"
        with self.assertRaises(ValueError):apply(q,r)
    def test_implicit_accept_prohibited(self):
        q,r=reviewed();r["reviews"][0]["reviewer"]=""
        with self.assertRaises(ValueError):apply(q,r)
    def test_duplicate_id(self):
        q,r=reviewed();r["reviews"][1]["id"]="JF-1"
        with self.assertRaises(ValueError):apply(q,r)
    def test_digest_mismatch(self):
        q,r=reviewed();r["source_input_sha256"]="other"
        with self.assertRaises(ValueError):apply(q,r)
    def test_pending_export(self):
        q=quality();out=apply(q,template(q))
        self.assertEqual(out["accepted"],0)
        self.assertEqual(out["pending"],2)
if __name__=="__main__":unittest.main()

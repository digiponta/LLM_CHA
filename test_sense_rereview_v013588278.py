import unittest
from unittest.mock import patch
from sense_rereview_proposals_v013588278 import proposal
from batch_semantic_approval_v013588277 import approve

def data():
    c={"id":"x","subject":"量子力学","meaning":"理論・分野","evidence_sentence":"原文",
       "source_url":"https://example.invalid"}
    return {"candidates":[c]},{"records":[{**c,"candidate_id":"x","decision":"RECOMMEND_APPROVE_WITH_CAUTION"}]}

class RefinementTests(unittest.TestCase):
    def test_caution_proposal_does_not_promote(self):
        q,r=data()
        result=proposal(q,r,{"x":{"decision":"RECOMMEND_APPROVE","note":"independent evidence checked"}})
        self.assertEqual(result["entries"][0]["status"],"PENDING_SEPARATE_ACCEPTANCE")
        self.assertEqual(r["records"][0]["decision"],"RECOMMEND_APPROVE_WITH_CAUTION")
        self.assertFalse(result["review_modified"])
    def test_no_reason_rejected(self):
        q,r=data()
        with self.assertRaises(ValueError):proposal(q,r,{"x":{"decision":"RECOMMEND_APPROVE","note":""}})
    def test_evidence_change_rejected(self):
        q,r=data();q["candidates"][0]["meaning"]="different"
        with self.assertRaises(ValueError):proposal(q,r,{"x":{"decision":"RECOMMEND_APPROVE","note":"checked"}})
    def test_unknown_rejected(self):
        q,r=data()
        with self.assertRaises(ValueError):proposal(q,r,{"unknown":{"decision":"DEFER","note":"checked"}})
    def test_empty_batch_still_not_approvable(self):
        with self.assertRaises(ValueError):
            approve({"status":"BATCH_PREPARED","eligible":[],"batch_hash":"abc"},"yes")
if __name__=="__main__":unittest.main()

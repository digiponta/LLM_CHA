import unittest
from audit_answer_reuse_v0135867 import assess
class Tests(unittest.TestCase):
 def test_pending_not_unknown(self):
  x=assess([{"query_id":"a","query":"Q","candidate_id":"t","proposed_class":"UNKNOWN","review_status":"PENDING","answer_reusable":""}])
  self.assertEqual(x[0]["verified_class"],"UNDETERMINED")
 def test_approved_yes(self):
  x=assess([{"query_id":"a","query":"Q","candidate_id":"t","proposed_class":"UNKNOWN","review_status":"APPROVED","answer_reusable":"YES"}])
  self.assertEqual(x[0]["verified_class"],"KNOWN")
  self.assertTrue(x[0]["top1_answer_reusable"])
 def test_no_approved_reusable(self):
  x=assess([{"query_id":"a","query":"Q","candidate_id":"t","proposed_class":"KNOWN","review_status":"APPROVED","answer_reusable":"NO"}])
  self.assertEqual(x[0]["verified_class"],"UNKNOWN")
 def test_invalid_label(self):
  with self.assertRaises(ValueError):
   assess([{"query_id":"a","query":"Q","candidate_id":"t","proposed_class":"KNOWN","review_status":"APPROVED","answer_reusable":""}])
if __name__=="__main__":unittest.main()

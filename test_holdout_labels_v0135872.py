import unittest
from audit_holdout_labels_v0135872 import check_overlap,assess
class Tests(unittest.TestCase):
 def setUp(self):
  self.train=[{"id":"train1","user":"こんにちは","assistant":"やあ"}]
  self.cases=[{"id":"new","question":"やあ","expected":"KNOWN"}]
 def test_unreviewed_is_not_unknown(self):
  items=[{"query_id":"new","candidate_id":"train1","review_status":"PENDING","answer_reusable":""}]
  self.assertEqual(assess(self.cases,items,self.train)[0]["verified"],"UNDETERMINED")
 def test_all_reviewed_yes(self):
  items=[{"query_id":"new","candidate_id":"train1","review_status":"APPROVED","answer_reusable":"YES"}]
  self.assertEqual(assess(self.cases,items,self.train)[0]["verified"],"KNOWN")
 def test_all_reviewed_no(self):
  items=[{"query_id":"new","candidate_id":"train1","review_status":"APPROVED","answer_reusable":"NO"}]
  self.assertEqual(assess(self.cases,items,self.train)[0]["verified"],"UNKNOWN")
 def test_exact_training_overlap(self):
  x=check_overlap([{"id":"same","question":"こんにちは"}],self.train,[])
  self.assertIn("TRAIN_EXACT",x[0]["flags"])
if __name__=="__main__":unittest.main()

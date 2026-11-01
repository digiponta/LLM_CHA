import unittest
from prepare_rse_holdout_v013588308 import review_stub,construct
class Tests(unittest.TestCase):
 def test_report_has_no_dialogue_text(self):
  rows=[{"id":"a","dialogue_id":"x","question":"秘密の質問","answer":"秘密の回答"}]
  r=review_stub(rows,"test",1)
  self.assertNotIn("秘密",str(r))
  self.assertIsNone(r["cases"][0]["suitable"])
  self.assertFalse(r["human_labels_verified"])
 def test_train_split_disallowed(self):
  with self.assertRaises(ValueError):
   construct(".",split="train")
 def test_non_positive_limit_disallowed(self):
  with self.assertRaises(ValueError):
   construct(".",limit=0)
if __name__=="__main__":unittest.main()

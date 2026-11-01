import unittest
from review_rse_holdout_v013588309 import template,validate
class RSEReviewTests(unittest.TestCase):
 def setUp(self):
  self.h={"split":"test","cases":[{"id":"abc","dialogue_id":"11","question_chars":4,"answer_chars":9}]}
 def test_unreviewed_is_pending(self):
  x=validate(self.h,template(self.h))
  self.assertEqual(x["status"],"HUMAN_LABELING_PENDING")
  self.assertEqual(x["fully_labeled"],0)
 def test_labeled(self):
  r=template(self.h)
  r["cases"][0].update(new_query="こんにちは",intent_match=True,slot_match=True,answer_suitable=True,persona_transfer_risk=False)
  self.assertEqual(validate(self.h,r)["status"],"LABELING_COMPLETE")
 def test_duplicate_case_rejected(self):
  r=template(self.h);r["cases"].append(dict(r["cases"][0]))
  self.assertEqual(validate(self.h,r)["status"],"INVALID")
 def test_no_source_text(self):
  self.assertNotIn("source_answer",str(template(self.h)))
if __name__=="__main__":unittest.main()

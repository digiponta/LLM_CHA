import unittest
from train_iterative_corrective_v0135832 import exact_match,verify_regressions,schedule,ORDER,PROTECTED
class Tests(unittest.TestCase):
 def test_exactness(self):
  self.assertTrue(exact_match("長門有希。","長門有希。"))
  self.assertFalse(exact_match("CPUは中央処理装置。","CPUは中央処理装置。命令を実行する。"))
 def test_regression(self):
  ref={"a":"良好","b":"こんにちは"}
  self.assertEqual(verify_regressions({"a":"悪化","b":"こんにちは"},ref,["a","b"]),["a"])
 def test_schedule(self):
  records=[{"id":i} for i in ORDER+PROTECTED]
  targets,protect=schedule(records)
  self.assertEqual([r["id"] for r in targets],list(ORDER))
  self.assertEqual([r["id"] for r in protect],list(PROTECTED))
 def test_duplicate_reject(self):
  with self.assertRaises(ValueError):schedule([{"id":ORDER[0]}]*8)
if __name__=="__main__":unittest.main()

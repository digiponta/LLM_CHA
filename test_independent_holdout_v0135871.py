import csv,tempfile,unittest
from pathlib import Path
from prepare_independent_holdout_v0135871 import prepare
class Tests(unittest.TestCase):
 def test_template_requires_independent_authorship(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"template.csv"
   prepare(p)
   with p.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
   self.assertEqual(len(rows),24)
   self.assertTrue(all(r["question"]=="" for r in rows))
   self.assertTrue(all(r["review_status"]=="PENDING" for r in rows))
   self.assertTrue(all(r["independence_attested"]=="NO" for r in rows))
 def test_no_overwrite(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"template.csv"
   prepare(p)
   with self.assertRaises(FileExistsError):prepare(p)
if __name__=="__main__":unittest.main()

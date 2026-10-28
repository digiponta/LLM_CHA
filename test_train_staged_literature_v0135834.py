import hashlib,json,tempfile,unittest
from pathlib import Path
from train_staged_literature_v0135834 import validate,SEVEN,START_SHA

class Tests(unittest.TestCase):
 def test_ids(self):
  self.assertEqual(len(SEVEN),7)
  self.assertEqual(len(set(SEVEN)),7)
 def test_not_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);o=root/"out";o.mkdir()
   with self.assertRaises(FileExistsError):
    validate(root/"stages",root/"reviewed",root/"report",root/"start",o,5,10)
 def test_budget(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   with self.assertRaises(ValueError):
    validate(root/"stages",root/"reviewed",root/"report",root/"start",root/"out",0,10)
 def test_expected_sha(self):
  self.assertEqual(len(START_SHA),64)
if __name__=="__main__":unittest.main()

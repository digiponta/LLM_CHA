import tempfile,unittest
from pathlib import Path
from train_literature_theme_v0135838 import validate,ORDER,START_SHA,PREVIOUS_IDS,FACT_IDS
class Tests(unittest.TestCase):
 def test_targets(self):
  self.assertEqual(len(ORDER),3)
  self.assertEqual(len(set(ORDER)),3)
 def test_protected_count(self):
  self.assertEqual(len(PREVIOUS_IDS)+len(FACT_IDS)+1,11)
 def test_checksum_format(self):
  self.assertEqual(len(START_SHA),64)
 def test_output_exists_guard(self):
  with tempfile.TemporaryDirectory() as d:
   class Args:pass
   a=Args();a.output_dir=Path(d)
   with self.assertRaises(FileExistsError):validate(a)
 def test_invalid_budget(self):
  with tempfile.TemporaryDirectory() as d:
   class Args:pass
   a=Args();a.output_dir=Path(d)/"new";a.rounds=0;a.steps_per_round=10;a.max_new_tokens=64
   with self.assertRaises(ValueError):validate(a)
if __name__=="__main__":unittest.main()

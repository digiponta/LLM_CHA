import tempfile,unittest
from pathlib import Path
from train_literature_facts_v0135836 import ORDER,START_SHA,validate
class Tests(unittest.TestCase):
 def test_fact_ids(self):
  self.assertEqual(len(ORDER),4)
  self.assertEqual(len(set(ORDER)),4)
 def test_start_hash_shape(self):
  self.assertEqual(len(START_SHA),64)
 def test_existing_output_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   class Args:pass
   a=Args();a.output_dir=Path(d)
   with self.assertRaises(FileExistsError):validate(a)
 def test_invalid_round_budget(self):
  with tempfile.TemporaryDirectory() as d:
   class Args:pass
   a=Args();a.output_dir=Path(d)/"new";a.rounds=0;a.steps_per_round=10;a.max_new_tokens=64
   with self.assertRaises(ValueError):validate(a)
if __name__=="__main__":unittest.main()

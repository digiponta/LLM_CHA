import tempfile,unittest
from pathlib import Path
from evaluate_literature_generalization_v0135839 import NEW,BASE_SHA,FINAL_SHA,prepare
class Tests(unittest.TestCase):
 def test_unique_candidate_ids(self):
  self.assertEqual(len(NEW),len(set(x[0] for x in NEW)))
 def test_hashes(self):
  self.assertEqual(len(BASE_SHA),64)
  self.assertEqual(len(FINAL_SHA),64)
 def test_output_guard(self):
  class Args:pass
  with tempfile.TemporaryDirectory() as d:
   a=Args();a.output=Path(d)
   with self.assertRaises(FileExistsError):prepare(a)
 def test_candidate_set_has_compounds(self):
  self.assertGreaterEqual(sum(x[0].startswith("compound") for x in NEW),2)
 def test_no_diagnostic_as_truth(self):
  self.assertTrue(all(isinstance(x[2],list) for x in NEW))
if __name__=="__main__":unittest.main()

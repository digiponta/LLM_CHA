import tempfile,unittest
from pathlib import Path
from sweep_qa_fixed_split_v042834 import experiment

class Tests(unittest.TestCase):
    def fixture(self):
        return {"cases":[{"id":f"T{i:02d}","turn":1,"question":f"質問{i//2}",
          "answer":"正答" if i%2 else "不正答",
          "provisional_chatgpt_label":bool(i%2)} for i in range(64)]}
    def test_duplicate_seeds_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):experiment(self.fixture(),[11,11],42,1,"cpu",Path(d))
    def test_checkpoint_collision(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,"qa_cross_encoder_fixed_v042834_seed11.pt").write_bytes(b"existing")
            with self.assertRaises(ValueError):experiment(self.fixture(),[11,12],42,1,"cpu",Path(d))
    def test_two_initialization_seeds_same_partition(self):
        try:import torch
        except ImportError:self.skipTest("PyTorch unavailable")
        with tempfile.TemporaryDirectory() as d:
            result=experiment(self.fixture(),[11,12],42,1,"cpu",Path(d))
            self.assertTrue(result["same_holdout_across_seeds"])
            self.assertEqual(len(result["runs"]),2)
            self.assertEqual(result["runs"][0]["holdout_labeled"],result["runs"][1]["holdout_labeled"])
            self.assertTrue(all(r["checkpoint_verified"] for r in result["runs"]))
            self.assertFalse(result["external_holdout"])
if __name__=="__main__":unittest.main()

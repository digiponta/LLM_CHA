import tempfile,unittest
from pathlib import Path
from sweep_qa_multiseed_v042833 import sweep

class Tests(unittest.TestCase):
    def fixture(self):
        return {"cases":[{"id":f"T{i:02d}","turn":1,
          "question":f"質問{i//2}","answer":"適切" if i%2 else "不適切",
          "provisional_chatgpt_label":bool(i%2)} for i in range(64)]}
    def test_duplicate_seed_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):sweep(self.fixture(),[11,11],1,"cpu",Path(tmp))
    def test_empty_seed_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):sweep(self.fixture(),[],1,"cpu",Path(tmp))
    def test_two_seed_smoke(self):
        try:import torch
        except ImportError:self.skipTest("PyTorch absent")
        with tempfile.TemporaryDirectory() as tmp:
            result=sweep(self.fixture(),[111,222],1,"cpu",Path(tmp))
            self.assertEqual(len(result["runs"]),2)
            self.assertFalse(result["same_holdout_across_seeds"])
            self.assertFalse(result["external_holdout"])
            self.assertTrue(all(r["checkpoint_verified"] for r in result["runs"]))
    def test_occupied_path_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,"qa_cross_encoder_multiseed_v042833_seed111.pt").write_bytes(b"existing")
            with self.assertRaises(ValueError):sweep(self.fixture(),[111,222],1,"cpu",Path(tmp))
if __name__=="__main__":unittest.main()

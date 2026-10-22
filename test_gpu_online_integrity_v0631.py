import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import torch
from verify_gpu_online_integrity_v0631 import model_digest

class IntegrationProbeTests(unittest.TestCase):
    def test_model_digest_detects_weight_change(self):
        with TemporaryDirectory() as d:
            first=Path(d)/"before.pt"
            second=Path(d)/"after.pt"
            torch.save({"model_state_dict":{"weight":torch.tensor([1.0,2.0])}},first)
            torch.save({"model_state_dict":{"weight":torch.tensor([1.0,3.0])}},second)
            self.assertNotEqual(model_digest(first),model_digest(second))
    def test_model_digest_same_weights(self):
        with TemporaryDirectory() as d:
            first=Path(d)/"before.pt"
            second=Path(d)/"after.pt"
            torch.save({"model_state_dict":{"weight":torch.tensor([1.0,2.0])}},first)
            torch.save({"model_state_dict":{"weight":torch.tensor([1.0,2.0])}},second)
            self.assertEqual(model_digest(first),model_digest(second))
if __name__=="__main__":unittest.main()

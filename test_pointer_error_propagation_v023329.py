import unittest
import torch
from model import LanguageModel
from relative_monotonic_pointer_v023328 import PositionPointer
from pointer_error_propagation_v023329 import trace,summary

class PropagationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(329)
        cls.model=LanguageModel(vocab_size=120,d_model=16,num_layers=2,hidden_dim=32,
            num_heads=2,causal=True,context_length=80,use_position_embedding=True).eval()
        for par in cls.model.parameters():par.requires_grad_(False)
    def test_trace_all_modes(self):
        for mode in ("baseline","relative","monotonic","combined"):
            head=PositionPointer(16,mode).eval()
            row=trace(self.model,head,[10,11,12],7,2,3,budget=8)
            self.assertEqual(len(row["teacher"]),4)
            self.assertGreaterEqual(len(row["free"]),1)
            self.assertEqual(len(row["generated"]),len(row["free"]))
            self.assertIn(row["eos_class"],("early","correct","late","missing"))
    def test_first_error_consistency(self):
        head=PositionPointer(16,"baseline").eval()
        row=trace(self.model,head,[10,11],7,2,3,budget=6)
        if row["exact"]:
            self.assertIsNone(row["first_token_error"])
        else:
            self.assertIsNotNone(row["first_token_error"])
    def test_summary_counts(self):
        head=PositionPointer(16,"baseline").eval()
        rows=[trace(self.model,head,s,7,2,3,budget=7) for s in ([10,11],[11,10])]
        val=summary(rows)
        self.assertEqual(val["total"],2)
        self.assertEqual(sum(val["eos_hist"].values()),2)
        self.assertEqual(sum(val["first_token_error_hist"].values()),2)
        self.assertTrue(0<=val["teacher_position_accuracy"]<=1)
    def test_teacher_alignment_uses_gold_prefix(self):
        head=PositionPointer(16,"combined").eval()
        seq=[10,11,12]
        row=trace(self.model,head,seq,7,2,3,budget=5)
        with torch.inference_mode():
            actual=int(head.position_logits(self.model,seq,seq[:2],7,2).argmax())
        self.assertEqual(row["teacher"][2]["predicted_position"],actual)
if __name__=="__main__":unittest.main()

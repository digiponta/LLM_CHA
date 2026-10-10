import unittest,torch
from model import LanguageModel
from cursor_action_state_v023333 import StatefulCursor
from cursor_transition_robustness_v023334 import (
    trace_error,diagnose,summarize,action_composition_probes,ARMS
)
class TransitionRobustnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(334)
        cls.base=LanguageModel(vocab_size=120,d_model=16,num_layers=2,hidden_dim=32,
            num_heads=2,causal=True,context_length=80,use_position_embedding=True).eval()
        for p in cls.base.parameters():p.requires_grad_(False)
    def test_first_mismatch(self):
        self.assertIsNone(trace_error([0,1,3],[0,1,3]))
        self.assertEqual(trace_error([0,1,3],[0,2,3]),1)
        self.assertEqual(trace_error([0,1,3],[0,1]),2)
    def test_confusion_alignment(self):
        head=StatefulCursor(16,"last_action").eval()
        r=diagnose(self.base,head,[("identity",[10,11]),("repeat",[10,11])],7,2,3)
        self.assertEqual(r["total"],2)
        self.assertEqual(sum(r["first_error_hist"].values()),2)
        self.assertEqual(len(r["first_divergence_action_confusion"]),4)
        self.assertTrue(all(len(row)==4 for row in r["first_divergence_action_confusion"]))
    def test_seed_aggregate(self):
        outcomes={}
        for seed in ("42","43"):
            outcomes[seed]={arm:{"evaluation":{"test":{"exact":2,"total":5}}} for arm in ARMS}
        # minimal aggregate shape: all groups are needed
        for record in outcomes.values():
            for arm in ARMS:
                for group in ("long","unseen","mixed_ids","novel_extra"):
                    record[arm]["evaluation"][group]={"exact":1,"total":5}
        r=summarize(outcomes)
        self.assertEqual(r["baseline"]["test"]["mean"],.4)
        self.assertEqual(r["baseline"]["long"]["mean"],.2)
    def test_composition_not_misreported_as_model_scores(self):
        r=action_composition_probes()
        self.assertTrue(all(seq[-1]==3 for seq in r.values()))
        self.assertTrue(all(all(a in (0,1,2,3) for a in seq) for seq in r.values()))
    def test_frozen_base(self):
        head=StatefulCursor(16,"transition_state")
        head.loss_for(self.base,[10,11],"repeat",7,2,3).backward()
        self.assertTrue(all(p.grad is None for p in self.base.parameters()))
if __name__=="__main__":unittest.main()

import unittest
import torch
from model import LanguageModel
from diagnose_copy_output_bias_eos_v023324 import stats,run_mode,compare_modes,probe_logits,embedding_audit
class CopyOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(4)
        cls.model=LanguageModel(vocab_size=120,d_model=16,num_layers=2,hidden_dim=32,num_heads=2,
                                causal=True,context_length=80,use_position_embedding=True).eval()
    def test_stats(self):
        logits=torch.zeros(120);logits[10]=2.
        result=stats(logits,{10,11,3},10)
        self.assertEqual(result["candidate_prediction"],10)
        self.assertEqual(result["candidate_target_rank"],1)
        self.assertFalse(stats(logits,{11,3},10)["candidate_target_present"])
    def test_oracle_contract(self):
        s=[10,11,12]
        r=run_mode(self.model,s,7,2,3,"position_oracle")
        self.assertEqual(r["generated_ids"],[10,11,12,3])
        self.assertTrue(r["exact"])
    def test_known_length_forces_eos_boundary(self):
        s=[10,11,12]
        r=run_mode(self.model,s,7,2,3,"known_length")
        self.assertEqual(r["eos_position"],3)
        self.assertEqual(len(r["generated_ids"]),4)
    def test_restriction(self):
        s=[10,11]
        r=run_mode(self.model,s,7,2,3,"source_candidates")
        self.assertTrue(set(r["generated_ids"])<={10,11,3})
    def test_report_shapes(self):
        ss=[[10,11],[11,10]]
        a=compare_modes(self.model,ss,7,2,3)
        self.assertEqual(set(a),{"normal","source_candidates","known_length","source_and_length","position_oracle"})
        self.assertEqual(a["position_oracle"]["exact"],2)
        p=probe_logits(self.model,ss,7,2,3,list(range(8,72)),list(range(88,104)))
        self.assertEqual(len(p),2)
        self.assertIn("mean_known_logit",p[0])
    def test_embedding_groups(self):
        a=embedding_audit(self.model,list(range(8,72)),list(range(88,104)))
        self.assertEqual(set(a),{"known","unseen"})
if __name__=="__main__":unittest.main()

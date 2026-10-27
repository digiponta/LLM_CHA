import unittest
from evaluate_rpc_context_evidence_v01339 import encode_case,aggregate

class FakeTokenizer:
    def encode(self,text,add_bos=False,add_eos=False):
        x=[(ord(c)%80)+4 for c in text]
        return ([1] if add_bos else [])+x+([2] if add_eos else [])

class ContextEvidenceTests(unittest.TestCase):
    def test_mask_alignment(self):
        x,y,mask,truncated,n=encode_case(FakeTokenizer(),"相手: 猫","はい",128)
        self.assertEqual(sum(mask),n)
        self.assertEqual(truncated,0)
        self.assertEqual(len(x),len(y))
    def test_truncation_preserves_answer(self):
        x,y,mask,truncated,n=encode_case(FakeTokenizer(),"相手: "+"a"*100,"はい",30)
        self.assertEqual(len(x),30)
        self.assertEqual(sum(mask),n)
        self.assertGreater(truncated,0)
    def test_too_long_answer(self):
        with self.assertRaises(ValueError):
            encode_case(FakeTokenizer(),"相手: x","b"*100,30)
    def test_aggregation(self):
        rows=[{"scores":{"FULL_CONTEXT":{"loss_sum":6,"tokens":2,"prompt_truncated_tokens":1}}},
              {"scores":{"FULL_CONTEXT":{"loss_sum":3,"tokens":3,"prompt_truncated_tokens":0}}}]
        a=aggregate(rows,"FULL_CONTEXT")
        self.assertAlmostEqual(a["token_weighted_nll"],1.8)
        self.assertEqual(a["prompt_truncated_pairs"],1)

if __name__=="__main__":unittest.main()

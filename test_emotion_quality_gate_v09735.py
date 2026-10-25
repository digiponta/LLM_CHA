import unittest
import torch
from emotion_aware_dialogue_v09733 import detect
from emotion_quality_gate_v09735 import assess
from emotion_conditioned_generation_v09734 import compare
from train_emotion_conditioned_v09735 import semantic_prompt,encode,training_rows

class GateTests(unittest.TestCase):
    def test_five_observed_false_positives_rejected(self):
        cases=[
            ("今日は楽しかった","~(Kenne_As)は、花音、花音、花音、曼音、拍音、音のたまり役。"),
            ("楽しくなかった","樹"),
            ("悲しくないよ","、曼闘技は、不正な恋。"),
            ("楽しかったけど疲れた","楽しい順"),
            ("こんにちは","へつるは、")]
        for q,bad in cases:
            with self.subTest(q=q):
                self.assertFalse(assess(bad,detect(q))[0])
    def test_approved_strategy(self):
        x=detect("今日は楽しかった")
        self.assertTrue(assess(x.response,x)[0])
    def test_conditioned_prompt_and_mask(self):
        prompt=semantic_prompt("楽しかった","ENJOYMENT","SHARE_JOY")
        self.assertTrue(prompt.startswith("[EMOTION=ENJOYMENT]"))
        class T:
            def encode(self,s,add_bos=False,add_eos=False):
                return ([1] if add_bos else [])+[4+ord(c)%200 for c in s]+([2] if add_eos else [])
        tok=T()
        x,y=encode(tok,prompt,"良かったね。",512)
        self.assertEqual(int((y!=-100).sum()),len(tok.encode("良かったね。",add_eos=True)))
    def test_holdout_isolation(self):
        d=training_rows()
        self.assertEqual(len(d["train"]),73)
        self.assertEqual(len(d["holdout"]),30)
        self.assertFalse(set(r["input"] for r in d["train"])&set(r["input"] for r in d["holdout"]))
if __name__=="__main__":unittest.main()

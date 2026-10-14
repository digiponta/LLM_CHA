import unittest
from train_qa_cross_encoder_v042829 import encode_pair

class Tests(unittest.TestCase):
    def test_pair_boundaries(self):
        tokens,segments=encode_pair("GPU","並列処理")
        self.assertEqual(tokens[0],1)
        self.assertEqual(tokens[4],2)
        self.assertEqual(len(tokens),len(segments))
    def test_segmentation(self):
        _,segments=encode_pair("a","b")
        self.assertEqual(segments,[0,0,0,1])
    def test_long_input_bounded(self):
        tokens,segments=encode_pair("あ"*1000,"い"*1000)
        self.assertLessEqual(len(tokens),160)
        self.assertEqual(len(tokens),len(segments))
    def test_deterministic_encoding(self):
        self.assertEqual(encode_pair("こんにちは","さようなら"),encode_pair("こんにちは","さようなら"))
    def test_torch_forward_training_smoke(self):
        try:import torch
        except ImportError:self.skipTest("PyTorch not installed")
        from train_qa_cross_encoder_v042829 import fit_predict
        cases=[{"id":f"T{i:02d}","turn":1,"question":"GPUとは","answer":"並列処理" if i%2 else "未学習です",
          "provisional_chatgpt_label":i%2==1} for i in range(64)]
        result=fit_predict({"cases":cases},epochs=1)
        self.assertEqual(result["training_examples"],64)
        self.assertEqual(len(result["predictions"]),64)
        self.assertTrue(all(x["decision"]=="ABSTAIN" for x in result["predictions"]))
if __name__=="__main__":unittest.main()

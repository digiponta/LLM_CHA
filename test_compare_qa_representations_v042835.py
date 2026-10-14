import tempfile,unittest
from pathlib import Path
from compare_qa_representations_v042835 import encode_utf8,compare

class Tests(unittest.TestCase):
    def fixture(self):
        return {"cases":[{"id":f"T{i:02d}","turn":1,"question":f"質問{i//2}",
          "answer":"適切" if i%2 else "不適切",
          "provisional_chatgpt_label":bool(i%2)} for i in range(64)]}
    def test_utf8_encoding(self):
        a,s=encode_utf8("あ","GPU")
        self.assertEqual(a[0],1)
        self.assertEqual(a.count(2),1)
        self.assertEqual(len(a),len(s))
    def test_utf8_length(self):
        a,s=encode_utf8("あ"*500,"い"*500)
        self.assertLessEqual(len(a),160)
    def test_determinism(self):
        self.assertEqual(encode_utf8("量子","GPU"),encode_utf8("量子","GPU"))
    def test_seed_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):compare(self.fixture(),[1,1],42,1,"cpu",Path(tmp))
    def test_pairwise_smoke(self):
        try:import torch
        except ImportError:self.skipTest("PyTorch unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            result=compare(self.fixture(),[11,12],42,1,"cpu",Path(tmp))
            self.assertEqual(len(result["runs"]),4)
            self.assertFalse(result["bpe_used"])
            self.assertTrue(all(r["checkpoint_verified"] for r in result["runs"]))
if __name__=="__main__":unittest.main()

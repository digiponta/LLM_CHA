import tempfile, unittest, json
from pathlib import Path
from prepare_japanese_foundation_v0218 import build
from train_foundation_dialogue_v0218 import commands
from argparse import Namespace

class FoundationPilotTests(unittest.TestCase):
    def test_train_only_corpus(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); src=root/"train.jsonl"; out=root/"text.txt"
            src.write_text('{"user":"人: 本です","assistant":"これは日本語の文章構造を学ぶための訓練文です。"}\n',encoding="utf-8")
            meta=build(src,out,limit=5)
            self.assertEqual(meta["sentences"],1)
            self.assertIn("訓練文です。\n",out.read_text(encoding="utf-8"))
            self.assertNotIn("。。",out.read_text(encoding="utf-8"))
    def test_separate_output_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ("corpus","base_model","tokenizer","dialogue_train","dialogue_val","anchors"):
                (root/name).write_text("dummy",encoding="utf-8")
            kwargs={name:str(root/name) for name in ("corpus","base_model","tokenizer","dialogue_train","dialogue_val","anchors")}
            a=Namespace(**kwargs,cpt_output=str(root/"cpt.pt"),sft_output=str(root/"sft.pt"),cpt_epochs=1,sft_epochs=2)
            cpt,sft=commands(a)
            self.assertIn("train_nagato.py",cpt)
            self.assertIn("train_nagato_chat.py",sft)
            a.sft_output=a.base_model
            with self.assertRaises(ValueError):commands(a)
if __name__=="__main__":unittest.main()

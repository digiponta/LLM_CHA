import json,tempfile,unittest
from pathlib import Path
from argparse import Namespace
from prepare_response_quality_v0221 import build
from train_response_quality_v0221 import command

class ResponseQualityTests(unittest.TestCase):
    def test_holdout_disjoint_and_replay_filtered(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);replay=root/"train.jsonl";output=root/"out"
            rows=[{"user":"人: 庭の写真を撮った","assistant":"きれいですね。"},
                  {"user":"人: 読書が好きです","assistant":"どんな作品が好き？"}]
            replay.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
            info=build(output,replay,replay_limit=10,repeat=2)
            train=[json.loads(x) for x in (output/"train.jsonl").read_text(encoding="utf-8").splitlines()]
            val=[json.loads(x) for x in (output/"val.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(info["replay_rows"],1)
            self.assertEqual(len(val),8)
            self.assertFalse({x["user"] for x in train}&{x["user"] for x in val})
            self.assertTrue(any("その話を続けて" in x["user"] for x in train))
    def test_output_protection(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            kwargs={}
            for name in ("train","val","base_model","tokenizer","anchors"):
                path=p/name;path.write_text("x");kwargs[name]=str(path)
            a=Namespace(**kwargs,output=str(p/"new.pt"),epochs=1,batch_size=8,anchor_weight=10,learning_rate=2e-6,lm_head_learning_rate=3e-7)
            self.assertIn("--preformatted-prompts",command(a))
            a.output=a.base_model
            with self.assertRaises(ValueError):command(a)
if __name__=="__main__":unittest.main()

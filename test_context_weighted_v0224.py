import json,tempfile,unittest
from pathlib import Path
from argparse import Namespace
from prepare_context_weighted_v0224 import build
from train_context_weighted_v0224 import command

class ContextWeightedTests(unittest.TestCase):
 def test_exposure_accounting_and_holdout(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);replay=p/"replay.jsonl"
   rows=[{"user":"人: 普段は読書をしています","assistant":"面白い本ですね。"},
         {"user":"人: 映画をよく見ます","assistant":"どんなジャンルですか？"},
         {"user":"人: 写真を撮ります","assistant":"夜景がきれいですね。"}]
   replay.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
   out=p/"out";metrics=build(out,replay,weight=4,replay_limit=10)
   self.assertEqual(metrics["expected_context_exposures"],24)
   self.assertEqual(metrics["replay_pairs"],2)
   anchor=p/"anchor.jsonl"
   anchor.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows[:2]),encoding="utf-8")
   base=p/"base.pt";tok=p/"tok.json";base.write_text("placeholder");tok.write_text("placeholder")
   a=Namespace(train=str(out/"train.jsonl"),context=str(out/"context.jsonl"),
    val=str(out/"val.jsonl"),manifest=str(out/"manifest.json"),
    anchors=str(anchor),base_model=str(base),tokenizer=str(tok),output=str(p/"new.pt"),
    context_weight=4,anchor_weight=2,epochs=1,batch_size=2,
    learning_rate=2e-6,lm_head_learning_rate=3e-7)
   cmd,stats=command(a)
   self.assertEqual(stats["context_exposures_per_epoch"],24)
   self.assertEqual(stats["total_exposures_per_epoch"],30)
   self.assertEqual(cmd[cmd.index("--expansion-weight")+1],"4")
   a.context_weight=5
   with self.assertRaises(ValueError):command(a)
   a.context_weight=4;a.output=a.base_model
   with self.assertRaises(ValueError):command(a)
if __name__=="__main__":unittest.main()

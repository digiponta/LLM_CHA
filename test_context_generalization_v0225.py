import unittest,json,tempfile
from pathlib import Path
from prepare_context_generalization_v0225 import TRAIN,HOLDOUT,make,build
class GeneralizationTests(unittest.TestCase):
 def test_splits(self):
  self.assertEqual(len(TRAIN),18);self.assertEqual(len(HOLDOUT),6)
  self.assertFalse({t[1] for t in TRAIN}&{t[1] for t in HOLDOUT})
  self.assertEqual({make(t)["user"].split("人: ")[-1] for t in TRAIN+HOLDOUT},{"その話を続けて"})
 def test_build(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source=root/"replay.jsonl"
   rows=[{"user":"人: 本です","assistant":"読書は楽しいね。"},{"user":"人: 料理です","assistant":"料理も楽しいね。"},{"user":"人: 夜景の写真","assistant":"きれいな夜景ですね。"}]
   source.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
   result=build(root/"out",source,weight=12,replay_limit=3)
   self.assertEqual(result["context_exposures"],216)
   self.assertEqual(result["replay_pairs"],2)
   self.assertEqual(result["holdout_pairs"],6)
if __name__=="__main__":unittest.main()

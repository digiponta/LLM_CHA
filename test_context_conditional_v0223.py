import json,tempfile,unittest
from pathlib import Path
from prepare_context_conditional_v0223 import TOPICS,HOLDOUT,make,build
class ContextConditioningTests(unittest.TestCase):
 def test_same_question_different_targets(self):
  rows=[make(t) for t in TOPICS]
  self.assertEqual(len({r["assistant"] for r in rows}),len(rows))
  self.assertEqual({r["user"].split("人: ")[-1] for r in rows},{"その話を続けて"})
 def test_holdout_disjoint(self):
  self.assertFalse({t[0] for t in TOPICS}&{t[0] for t in HOLDOUT})
 def test_corpus_split(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);out=root/"out";replay=root/"replay.jsonl"
   replay.write_text('{"user":"人: 読書をしています","assistant":"どんな本ですか"}\n{"user":"人: 写真です","assistant":"夜景です"}\n',encoding="utf-8")
   result=build(out,replay,repeat=2,replay_limit=10)
   self.assertEqual(result["replay_rows"],1)
   self.assertEqual(result["holdout"],2)
   train=[json.loads(s) for s in (out/"train.jsonl").read_text(encoding="utf-8").splitlines()]
   val=[json.loads(s) for s in (out/"val.jsonl").read_text(encoding="utf-8").splitlines()]
   self.assertFalse({x["user"] for x in train}&{x["user"] for x in val})
if __name__=="__main__":unittest.main()

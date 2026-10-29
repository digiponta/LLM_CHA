import json,tempfile,unittest
from pathlib import Path
from diagnose_single_answer_v0135851 import find_row
class Tests(unittest.TestCase):
 def test_target(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.jsonl"
   p.write_text(json.dumps({"split":"train","user":"最近ちょっと眠たい","assistant":"眠いんだね。休めそう？"},ensure_ascii=False)+"\n",encoding="utf-8-sig")
   self.assertEqual(find_row(p,"最近ちょっと眠たい")["assistant"],"眠いんだね。休めそう？")
 def test_holdout_excluded(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.jsonl"
   p.write_text(json.dumps({"split":"holdout","user":"q","assistant":"a"})+"\n",encoding="utf-8")
   with self.assertRaises(ValueError):find_row(p,"q")
 def test_mojibake_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.jsonl"
   p.write_text(json.dumps({"split":"train","user":"q","assistant":"�"})+"\n",encoding="utf-8")
   with self.assertRaises(ValueError):find_row(p,"q")
if __name__=="__main__":unittest.main()

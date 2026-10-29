import json,tempfile,unittest
from pathlib import Path
from prepare_daily_corrective_v0135849 import build
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  self.base=self.root/"base";self.cand=self.root/"cand";self.new=self.root/"new";self.out=self.root/"out"
  def put(path,rows):path.write_text("\n".join(json.dumps(r,ensure_ascii=False) for r in rows)+"\n",encoding="utf-8-sig")
  self.put=put
  put(self.base,[{"id":"t","split":"train","user":"こんにちは","assistant":"こんにちは。"},
                 {"id":"h","split":"holdout","user":"疲れたよ","assistant":"休めそう？"},
                 {"id":"p","split":"protected","user":"あなたは誰","assistant":"長門有希。"}])
  put(self.cand,[{"id":"repair-h","source_id":"h","user":"疲れたよ","assistant":"休めそう？",
  "previous_bad_output":"不明","review_state":"ASSISTANT_PROPOSED_REVIEW_REQUIRED","approved_for_training":False}])
  put(self.new,[{"id":"n"+str(i),"split":"holdout","user":"新しい質問"+str(i),"assistant":"回答"+str(i)} for i in range(6)])
 def tearDown(self):self.tmp.cleanup()
 def test_requires_approval(self):
  with self.assertRaises(ValueError):build(self.base,self.cand,self.new,self.out)
 def test_promote_and_retire(self):
  r=build(self.base,self.cand,self.new,self.out,True)
  self.assertEqual(r["promoted"],1)
  self.assertEqual(r["train"],2)
  self.assertEqual(r["holdout"],6)
  self.assertNotIn('"split": "holdout", "user": "疲れたよ"',self.out.read_text(encoding="utf-8"))
 def test_collision_rejected(self):
  self.put(self.new,[{"id":"n"+str(i),"split":"holdout","user":"こんにちは" if i==0 else "新しい"+str(i),"assistant":"回答"} for i in range(6)])
  with self.assertRaises(ValueError):build(self.base,self.cand,self.new,self.out,True)
 def test_reference_mismatch(self):
  self.put(self.cand,[{"id":"bad","source_id":"h","user":"疲れたよ","assistant":"違う",
   "review_state":"ASSISTANT_PROPOSED_REVIEW_REQUIRED","approved_for_training":False}])
  with self.assertRaises(ValueError):build(self.base,self.cand,self.new,self.out,True)
if __name__=="__main__":unittest.main()

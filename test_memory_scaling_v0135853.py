import json,tempfile,unittest
from pathlib import Path
from train_memory_scaling_v0135853 import validate
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/"data.jsonl"
  rows=[{"id":f"t{i}","split":"train","user":f"質問{i}","assistant":f"答え{i}"} for i in range(56)]
  rows += [{"id":"h","split":"holdout","user":"別の質問","assistant":"別の答え"},
           {"id":"p","split":"protected","user":"あなたは誰","assistant":"長門有希。"}]
  self.rows=rows;self.write()
 def write(self):
  self.path.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in self.rows)+"\n",encoding="utf-8")
 def tearDown(self):self.tmp.cleanup()
 def test_valid_sizes(self):
  for n in (8,16,32,56):
   self.assertEqual(len(validate(self.path,n)[0]),56)
 def test_invalid_size(self):
  with self.assertRaises(ValueError):validate(self.path,64)
 def test_holdout_leak(self):
  self.rows[-2]["user"]=self.rows[0]["user"];self.write()
  with self.assertRaises(ValueError):validate(self.path,8)
if __name__=="__main__":unittest.main()

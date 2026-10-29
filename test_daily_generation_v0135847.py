import json,tempfile,unittest
from pathlib import Path
from train_daily_generation_v0135847 import dataset
class Tests(unittest.TestCase):
 def write(self,path,rows):
  path.write_text("\n".join(json.dumps(r,ensure_ascii=False) for r in rows)+"\n",encoding="utf-8-sig")
 def rows(self):
  return [{"id":"t","user":"こんにちは","assistant":"こんにちは。","split":"train"},
          {"id":"h","user":"やあ","assistant":"やあ。","split":"holdout"},
          {"id":"p","user":"あなたは誰","assistant":"長門有希。","split":"protected"}]
 def test_split(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"data";self.write(p,self.rows())
   t,h,r=dataset(p);self.assertEqual((len(t),len(h),len(r)),(1,1,1))
 def test_duplicate(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"data";x=self.rows();self.write(p,x+[x[0]])
   with self.assertRaises(ValueError):dataset(p)
 def test_holdout_overlap(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"data";x=self.rows();x[1]["user"]=x[0]["user"];self.write(p,x)
   with self.assertRaises(ValueError):dataset(p)
 def test_replacement_character(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"data";x=self.rows();x[0]["assistant"]="不明�";self.write(p,x)
   with self.assertRaises(ValueError):dataset(p)
if __name__=="__main__":unittest.main()

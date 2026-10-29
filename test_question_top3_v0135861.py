import tempfile,unittest
from pathlib import Path
from retrieve_question_top3_v0135861 import retrieve,execute,norm
class Tests(unittest.TestCase):
 def test_nfkc(self):self.assertEqual(norm("Ａ Ｂ"),"ab")
 def test_top3(self):
  rows=[{"id":str(i),"user":q,"assistant":"a"} for i,q in enumerate(["今日は眠い","本を読む","数学の話","音楽を聴く"])]
  result=retrieve(rows,"少し眠い",2,"tfidf")
  self.assertEqual(len(result),3)
  self.assertEqual(result[0]["question"],"今日は眠い")
  self.assertGreater(result[0]["score"],result[1]["score"])
 def test_no_query_overlap(self):
  from unittest.mock import patch
  from retrieve_question_top3_v0135861 import execute
  train=[{"id":"a","user":"今日は眠い","assistant":"OK"}]
  hold=[{"id":"b","user":"今日は眠い","assistant":"? "}]
  with tempfile.TemporaryDirectory() as tmp:
   with patch("retrieve_question_top3_v0135861.dataset",return_value=(train,hold,[])):
    with self.assertRaises(ValueError):execute(Path("x"),Path(tmp)/"out",["tfidf"],[2])
if __name__=="__main__":unittest.main()

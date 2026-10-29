import unittest
from compare_japanese_semantic_v0135863 import topk,MODES
class Tests(unittest.TestCase):
 def test_prefix_modes(self):
  self.assertEqual(MODES["semantic"],("",""))
  self.assertEqual(MODES["retrieval"],("検索クエリ: ","検索文書: "))
 def test_ranking(self):
  import numpy as np
  train=[{"id":"a","user":"A","assistant":"a"},{"id":"b","user":"B","assistant":"b"},{"id":"c","user":"C","assistant":"c"}]
  z=topk(np.array([[1.,0.]]),np.array([[.1,0.],[.9,0.],[-.2,0.]]),train)
  self.assertEqual([x["id"] for x in z[0]],["b","a","c"])
  self.assertEqual(len(z[0]),3)
 def test_tie_break(self):
  train=[{"id":"b","user":"B","assistant":""},{"id":"a","user":"A","assistant":""}]
  self.assertEqual(topk([[1.,0.]],[[1.,0.],[1.,0.]],train)[0][0]["id"],"a")
if __name__=="__main__":unittest.main()

import unittest
from wiki_more_details_v0560 import more

W={"status":"FOUND","title":"重ね合わせ","url":"https://ja.wikipedia.org/wiki/test",
   "extract":"量子力学における重ね合わせは概念である。"}
EXT=W["extract"]+"複数の量子状態は線形結合として表現されることがある。これは状態の数学的な記述に用いられる。"
def fetch(url):
 return {"query":{"pages":[{"title":"重ね合わせ","extract":EXT}]}}
class ExtendedMoreTests(unittest.TestCase):
 def test_found(self):
  r=more(W,"もっと詳しく",fetch=fetch)
  self.assertEqual(r["status"],"FOUND")
  self.assertIn("線形結合",r["answer"])
 def test_unverified(self):
  r=more(W,"もっと詳しく",fetch=fetch)
  self.assertFalse(r["verified"]);self.assertFalse(r["train_ready"])
 def test_invalid_question(self):
  self.assertEqual(more(W,"今日は散歩した",fetch=fetch)["status"],"NOT_APPLICABLE")
 def test_wrong_title(self):
  self.assertEqual(more(W,"もっと詳しく",fetch=lambda x:{"query":{"pages":[{"title":"別の記事","extract":EXT}]}})["status"],"SOURCE_MISMATCH")
 def test_changed_prefix(self):
  self.assertEqual(more(W,"もっと詳しく",fetch=lambda x:{"query":{"pages":[{"title":"重ね合わせ","extract":"違う記事本文。"}]}})["status"],"SOURCE_MISMATCH")
 def test_no_new_sentence(self):
  self.assertEqual(more(W,"もっと詳しく",fetch=lambda x:{"query":{"pages":[{"title":"重ね合わせ","extract":W["extract"]}]}})["status"],"NO_NEW_SENTENCE")
 def test_fetch_error(self):
  def bad(x):raise OSError("offline")
  self.assertEqual(more(W,"もっと詳しく",fetch=bad)["status"],"LOOKUP_FAILED")
 def test_no_context(self):
  self.assertEqual(more(None,"もっと詳しく",fetch=fetch)["status"],"NO_CONTEXT")
if __name__=="__main__":unittest.main()

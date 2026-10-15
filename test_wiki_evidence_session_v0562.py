import unittest
from wiki_evidence_session_v0562 import EvidenceSession
W={"status":"FOUND","title":"重ね合わせ","url":"https://ja.wikipedia.org/wiki/test","extract":"これは重ね合わせの概要である。"}
FULL=W["extract"]+"量子状態は複数の基底状態の線形結合として表現できる。観測結果は状態の振幅と確率則に関連して記述される。"
def fetch(params):return {"query":{"pages":[{"title":"重ね合わせ","extract":FULL}]}}
class EvidenceSessionTests(unittest.TestCase):
 def test_sequential(self):
  session=EvidenceSession()
  a=session.next(W,"もっと詳しく",fetch=fetch)
  b=session.next(W,"もっと詳しく",fetch=fetch)
  c=session.next(W,"もっと詳しく",fetch=fetch)
  self.assertEqual(a["status"],"FOUND")
  self.assertEqual(b["status"],"FOUND")
  self.assertNotEqual(a["answer"],b["answer"])
  self.assertEqual(c["status"],"EVIDENCE_EXHAUSTED")
 def test_topic_change(self):
  session=EvidenceSession()
  a=session.next(W,"もっと詳しく",fetch=fetch)
  w=dict(W,title="別題名",url="https://ja.wikipedia.org/wiki/other")
  def changed(params):return {"query":{"pages":[{"title":"別題名","extract":FULL}]}}
  b=session.next(w,"もっと詳しく",fetch=changed)
  self.assertEqual(a["answer"],b["answer"])
 def test_no_context(self):
  self.assertEqual(EvidenceSession().next(None,"もっと詳しく",fetch=fetch)["status"],"NO_CONTEXT")
 def test_non_followup(self):
  self.assertEqual(EvidenceSession().next(W,"散歩した",fetch=fetch)["status"],"NOT_APPLICABLE")
 def test_mismatch(self):
  def wrong(params):return {"query":{"pages":[{"title":"偽","extract":FULL}]}}
  self.assertEqual(EvidenceSession().next(W,"もっと詳しく",fetch=wrong)["status"],"SOURCE_MISMATCH")
 def test_unverified(self):
  r=EvidenceSession().next(W,"もっと詳しく",fetch=fetch)
  self.assertFalse(r["verified"]);self.assertFalse(r["train_ready"])
 def test_network_failure(self):
  def bad(params):raise OSError("offline")
  self.assertEqual(EvidenceSession().next(W,"もっと詳しく",fetch=bad)["status"],"LOOKUP_FAILED")
if __name__=="__main__":unittest.main()

import unittest
from wiki_evidence_session_v0562 import EvidenceSession, readable_evidence
W={"status":"FOUND","title":"重ね合わせ","url":"https://ja.wikipedia.org/wiki/test","extract":"これは重ね合わせの概要である。"}
FULL=W["extract"]+"量子状態は複数の基底状態の線形結合として表現できる。観測結果は状態の振幅と確率則に関連して記述される。"
def fetch(params):return {"query":{"pages":[{"title":"重ね合わせ","extract":FULL}]}}
class EvidenceSessionTests(unittest.TestCase):
 def test_reject_latex_fragments(self):
  self.assertFalse(readable_evidence(r"{\\displaystyle |\\psi \\rangle }"))
  self.assertFalse(readable_evidence(r"{\\displaystyle \\psi }"))
 def test_reject_equation_in_long_text(self):
  self.assertFalse(readable_evidence(r"量子状態は{\\displaystyle |\\psi \\rangle }で表現される"))
 def test_skip_math_and_advance(self):
  session=EvidenceSession()
  tex=W["extract"]+r"{\\displaystyle |\\psi \\rangle }。"+("量子状態は複数の基底状態の線形結合として表現できる。")
  def mocked(params):return {"query":{"pages":[{"title":"重ね合わせ","extract":tex}]}}
  result=session.next(W,"もっと詳しく",fetch=mocked)
  self.assertEqual(result["status"],"FOUND")
  self.assertIn("線形結合",result["answer"])
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
 def test_prose_fallback_and_exhaustion_diagnostics(self):
  session=EvidenceSession()
  long_sentence="量子状態の記述には複数の基底を用いることが重要な要素となる場合"
  data=W["extract"]+long_sentence+"。"
  def mocked(params):return {"query":{"pages":[{"title":"重ね合わせ","extract":data}]}}
  first=session.next(W,"もっと詳しく",fetch=mocked)
  self.assertEqual(first["status"],"FOUND")
  self.assertIn(long_sentence,first["answer"])
  exhausted=session.next(W,"もっと詳しく",fetch=mocked)
  self.assertEqual(exhausted["status"],"EVIDENCE_EXHAUSTED")
  self.assertEqual(exhausted["reason"],"NO_UNSEEN_READABLE_PROSE")
  self.assertEqual(exhausted["eligible"],1)
 def test_extended_fetch_and_candidate_diagnostics(self):
  urls=[]
  def mocked(url):
   urls.append(url)
   return {"query":{"pages":[{"title":"重ね合わせ","extract":W["extract"]+"短い断片。"}]}}
  result=EvidenceSession().next(W,"もっと詳しく",fetch=mocked)
  self.assertEqual(result["status"],"EVIDENCE_EXHAUSTED")
  self.assertIn("exchars=10000",urls[0])
  self.assertEqual(result["segments"],1)
  self.assertEqual(result["candidates"],0)
  self.assertEqual(result["eligible"],0)
  self.assertGreater(result["extended_chars"],0)
 def test_formula_preserved_and_followup_advances(self):
  session=EvidenceSession()
  one=r"量子力学では、系の状態は{\displaystyle |\psi \rangle }で記述される"
  two=r"このような状態ベクトルの線形結合を重ね合わせと呼ぶ"
  data=W["extract"]+one+"。"+two+"。"
  def mocked(params):return {"query":{"pages":[{"title":"重ね合わせ","extract":data}]}}
  a=session.next(W,"もっと詳しく",fetch=mocked)
  b=session.next(W,"もっと詳しく",fetch=mocked)
  self.assertEqual(a["status"],"FOUND")
  self.assertIn(r"{\displaystyle |\psi \rangle }",a["answer"])
  self.assertEqual(b["status"],"FOUND")
  self.assertIn("線形結合",b["answer"])
  self.assertNotEqual(a["answer"],b["answer"])
 def test_formula_only_not_returned(self):
  session=EvidenceSession()
  data=W["extract"]+r"{\displaystyle |\psi \rangle }。"
  def mocked(params):return {"query":{"pages":[{"title":"重ね合わせ","extract":data}]}}
  result=session.next(W,"もっと詳しく",fetch=mocked)
  self.assertEqual(result["status"],"EVIDENCE_EXHAUSTED")
 def test_rejection_sample_diagnostics(self):
  data=W["extract"]+"短すぎる。"+"量子状態に関する説明が途中で終わり"
  def mocked(url):return {"query":{"pages":[{"title":"重ね合わせ","extract":data}]}}
  result=EvidenceSession().next(W,"もっと詳しく",fetch=mocked)
  self.assertEqual(result["status"],"EVIDENCE_EXHAUSTED")
  self.assertIn("rejected_samples",result)
  self.assertIsInstance(result["rejected_samples"],list)
  self.assertLessEqual(len(result["rejected_samples"]),8)
if __name__=="__main__":unittest.main()

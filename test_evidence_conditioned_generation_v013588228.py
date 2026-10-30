import unittest
from evidence_conditioned_generation_v013588228 import (
 focus_query,retrieve_evidence,conditioned_prompt,evidence_gate,final_answer)
class Tests(unittest.TestCase):
 def setUp(self):
  self.e={"status":"EVIDENCE","topic":"宇宙","query":"宇宙膨張",
   "title":"宇宙膨張","excerpt":"宇宙は膨張している。銀河は遠ざかる。","url":"https://ja.wikipedia.org/wiki/宇宙膨張"}
 def test_focus(self):
  self.assertEqual(focus_query("宇宙","宇宙は全体として膨張している"),"宇宙膨張")
 def test_retrieval(self):
  x=retrieve_evidence("宇宙","膨張",lambda q:{"status":"HIT","hits":[
   {"title":"宇宙膨張","extract":"宇宙膨張の研究。","url":"https://example.test"}]})
  self.assertEqual(x["query"],"宇宙膨張")
  self.assertEqual(x["trust"],"EXTERNAL_UNVERIFIED")
 def test_prompt(self):
  self.assertIn("資料",conditioned_prompt(self.e))
 def test_unknown_rejected(self):
  self.assertEqual(evidence_gate("未学習です",self.e)[0],"REJECT_UNKNOWN")
 def test_hallucination_rejected(self):
  self.assertEqual(evidence_gate("宇宙は渦巻くアフェイン接続である。",self.e)[0],"REJECT_UNGROUNDED")
 def test_unsupported_rejected(self):
  self.assertEqual(evidence_gate("宇宙は完全に平坦になり、永久に停止する。",self.e)[0],"REJECT_NOT_ENTAILED")
 def test_evidence_fallback(self):
  result=final_answer("宇宙は完全に平坦になり、永久に停止する。",self.e)
  self.assertIn("宇宙は膨張",result["answer"])
  self.assertIn("出典:",result["answer"])
 def test_accepted_quote(self):
  x=evidence_gate("宇宙は膨張している。銀河は遠ざかる。",self.e)
  self.assertEqual(x[0],"ACCEPT_SOURCE_EXTRACT")
 def test_no_evidence(self):
  x=final_answer("宇宙は膨張している。",{"status":"NO_EVIDENCE"})
  self.assertIn("確認できなかった",x["answer"])
if __name__=="__main__":unittest.main()

import ast
import unittest
from pathlib import Path
from answer_quality_gate_v0542 import evaluate
Q="今日は量子コンピュータの記事を読んだ"
def check(reply,accepted,agreement=None,topic="量子コンピュータ"):
 return evaluate(Q,reply,accepted=accepted,agreement=agreement,wiki_topic=topic)
class QualityTests(unittest.TestCase):
 def test_unknown(self):self.assertTrue(check("未学習です",False)["suggest_wiki"])
 def test_low_agreement(self):
  x=check("不明な応答",True,0.087)
  self.assertEqual(x["reason"],"LOW_PROBE_AGREEMENT")
 def test_boundary(self):self.assertEqual(check("回答",True,0.35)["status"],"ACCEPT")
 def test_high(self):self.assertFalse(check("回答",True,0.8)["suggest_wiki"])
 def test_no_topic(self):self.assertEqual(check("未学習です",False,topic=None)["status"],"NO_WIKI_TOPIC")
 def test_missing_utterance(self):
  self.assertEqual(evaluate("","回答",accepted=False,wiki_topic="SQUID")["status"],"NO_USER_CONTEXT")
 def test_no_lookup(self):
  self.assertFalse(check("未学習です",False)["auto_lookup"])
 def test_no_learning(self):
  result=check("未学習です",False)
  self.assertFalse(result["auto_promote"]);self.assertFalse(result["train_ready"])
 def test_chat_integration(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn("[answer_quality=",s)
  self.assertIn("[wiki_repair_hint=",s)
if __name__=="__main__":unittest.main()

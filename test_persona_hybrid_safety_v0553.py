import unittest
from persona_hybrid_safety_v0553 import decide,assess_raw
from persona_context_v0550 import PersonaContext
from replay_persona_hybrid_safety_v0553 import replay

def row(user,raw="意味のある文章です。",ctrl=None):
 return {"scenario":"test","turn":1,"user":user,
         "controller":{"reply":ctrl},"raw_llm":{"reply":raw},
         "hybrid":{"selected":"RAW_LLM"}}

class HybridSafetyTests(unittest.TestCase):
 def test_controller_priority(self):
  self.assertEqual(decide(row("今日は散歩した",ctrl="そう。"))["selected"],"CONTROLLER")
 def test_knowledge_block(self):
  self.assertEqual(decide(row("量子ビットとは？"))["selected"],"KNOWLEDGE_GATE_REQUIRED")
 def test_knowledge_even_runtime_pass(self):
  self.assertEqual(decide(row("量子ビットとは？"),runtime_accepted=True)["reply"],None)
 def test_evidence_not_raw(self):
  self.assertEqual(decide(row("量子ビットとは？"),evidence_verified=True)["selected"],"EXTERNAL_VERIFIED_RETRIEVAL_REQUIRED")
 def test_unassessed_raw(self):
  self.assertEqual(decide(row("今日はどうだった"))["selected"],"RUNTIME_GATE_REQUIRED")
 def test_runtime_accept(self):
  self.assertEqual(decide(row("別の話をした"),runtime_accepted=True)["selected"],"RAW_RUNTIME_ACCEPTED")
 def test_fragment(self):
  self.assertEqual(assess_raw("の前身。")["status"],"REVIEW")
 def test_repeat(self):
  self.assertEqual(assess_raw("宇宙全体として、宇宙全体として、宇宙全体として")["status"],"REVIEW")
 def test_grammar_neutral(self):
  p=PersonaContext("neutral")
  p.handle("今日は、天文学の記事を読んだ")
  self.assertNotIn("についてについて",p.handle("星について書かれていた")["answer"])
 def test_replay(self):
  r=replay({"rows":[row("量子ビットとは？"),row("今日は散歩した",ctrl="そう。")]})
  self.assertEqual(r["selection_counts"]["KNOWLEDGE_GATE_REQUIRED"],1)
  self.assertEqual(r["selection_counts"]["CONTROLLER"],1)
if __name__=="__main__":unittest.main()

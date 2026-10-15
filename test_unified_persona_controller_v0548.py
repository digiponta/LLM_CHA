import ast
import unittest
from pathlib import Path
from unified_persona_controller_v0548 import audit, status, persona_for
from persona_priority_v0547 import apply
ROOT=Path(__file__).parent
E={"status":"EVIDENCE_FOUND","topic":"量子コンピュータ",
 "evidence_span":"量子コンピュータは量子力学の原理を応用する。",
 "source":"https://example.org","verified":False,"train_ready":False}
class PersonaControllerTests(unittest.TestCase):
 def test_default(self):self.assertEqual(status()["active_persona"],"nagato")
 def test_fallback(self):self.assertEqual(persona_for("unsupported"),"neutral")
 def test_routes(self):self.assertEqual(len(status()["routes"]),4)
 def test_model_gap(self):
  a=audit("MODEL_GENERATION","未学習です")
  self.assertTrue(a["persona_gap"]);self.assertTrue(a["answer_unchanged"])
 def test_semantic_gap(self):
  self.assertTrue(audit("SEMANTIC_MEMORY","量子情報",source="memory")["persona_gap"])
 def test_wiki_styled(self):
  r=apply("量子コンピュータの記事を読んだ",E)
  a=audit("WIKIPEDIA_REPAIR",r["answer"],persona=r["persona"],persona_applied=r["persona_applied"])
  self.assertFalse(a["persona_gap"])
 def test_no_mutation_claim(self):
  a=audit("MODEL_GENERATION","回答")
  self.assertFalse(a["auto_lookup"]);self.assertFalse(a["auto_promote"]);self.assertFalse(a["train_ready"])
 def test_reject_unknown_route(self):
  with self.assertRaises(ValueError):audit("FAKE","")
 def test_integration(self):
  s=(ROOT/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn('if user_text=="/persona-status":',s)
  self.assertIn('persona=cha_wiki_conversation.persona)',s)
  self.assertIn('cha_persona_audit(',s)
if __name__=="__main__":unittest.main()

import ast
import unittest
from pathlib import Path
from definition_grounding_v05111 import definition_grounded

class DefinitionGroundingTests(unittest.TestCase):
 def test_reject_bad_sensor(self):
  self.assertFalse(definition_grounded("量子センサーとは何ですか？","量子数のフィールドは計算能力を予測する。")[0])
 def test_accept_sensor(self):
  self.assertTrue(definition_grounded("量子センサーとは何ですか？","量子センサーは量子状態を利用する計測技術です。")[0])
 def test_generation_unknown_not_definition(self):
  self.assertTrue(definition_grounded("今日は映画について話そう","こんにちは")[0])
 def test_no_false_knowledge_in_context(self):
  self.assertFalse(definition_grounded("ブラックホールとは何ですか？","一般相対性理論の説明です。")[0])
 def test_question_intent(self):
  self.assertTrue(definition_grounded("量子センサーについて教えて","量子センサーとは計測装置です")[0])
 def test_chat_syntax(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(src)
  self.assertIn("cha_definition_grounded(",src)
  self.assertIn("cha_unknown_teacher.begin(",src)
 def test_legacy_sleep(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',src)
if __name__=="__main__":unittest.main()

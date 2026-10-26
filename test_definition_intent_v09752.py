import unittest
from definition_intent_v09752 import resolve,is_relevant_definition

class DefinitionIntentTests(unittest.TestCase):
    def test_satisfaction_definition(self):
        d=resolve("満足とは")
        self.assertEqual(d.route,"CURATED_DEFINITION")
        self.assertIn("期待や欲求",d.response)
    def test_satisfaction_question(self):
        self.assertEqual(resolve("満足とは何ですか？").target,"満足")
    def test_unknown_search_fallback(self):
        d=resolve("量子力学とは")
        self.assertEqual(d.route,"EXISTING_SEARCH")
        self.assertIsNone(d.response)
    def test_embedded_toha_remains_search(self):
        self.assertEqual(resolve("満足とはどういう意味ですか").intent,"DEFINITION")
    def test_non_definition(self):
        self.assertIsNone(resolve("満足"))
    def test_disambiguation_rejected(self):
        body="モーツァルト 満足 K.349 および満足 K.473 は作曲された歌曲"
        self.assertFalse(is_relevant_definition("満足","満足",body))
    def test_matching_article(self):
        self.assertTrue(is_relevant_definition("満足","満足","期待や欲求が満たされていると感じる心理的な状態を指します。生活満足度などの文脈で使われます。"))
    def test_different_article_rejected(self):
        self.assertFalse(is_relevant_definition("満足","満足 (楽曲)","期待や欲求が満たされている状態です。"*4))
    def test_no_promotion(self):
        d=resolve("満足とは")
        self.assertFalse(d.train_ready or d.auto_promote or d.persisted)
if __name__=="__main__":unittest.main()

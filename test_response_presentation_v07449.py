import unittest
from response_presentation_v07449 import is_bare_term,present_synonym_recovery

class PresentationTests(unittest.TestCase):
    def test_bare(self):
        self.assertEqual(present_synonym_recovery("ぬこ","ネコ","Wikipediaの説明"),
                         "「ぬこ」は「ネコ」の別の呼び方。詳しく説明する？")
    def test_definition_unchanged(self):
        self.assertEqual(present_synonym_recovery("ぬことは","ネコ","百科事典の説明"),"百科事典の説明")
    def test_question_not_bare(self):
        self.assertFalse(is_bare_term("猫って何？"))
    def test_empty(self):
        self.assertFalse(is_bare_term(""))

if __name__=="__main__":
    unittest.main()

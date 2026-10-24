import unittest
from pathlib import Path
from wiki_selection_relation_v08012 import selection_relation,selection_notice

class SelectionRelationTests(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(selection_relation("量子ビット","量子ビット"),"EXACT")
        self.assertEqual(selection_notice("量子ビット","量子ビット"),"")
    def test_different_article_is_not_alias(self):
        self.assertEqual(selection_relation("古典ビット","量子ビット"),"RELATED_UNVERIFIED")
        msg=selection_notice("古典ビット","量子ビット")
        self.assertIn("同じ概念とは確認されていません",msg)
    def test_unknown(self):
        self.assertEqual(selection_relation("","量子ビット"),"UNKNOWN")
    def test_runtime_has_both_subjects(self):
        code=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn("requested_topic=ambiguous_choice",code)
        self.assertIn("selected_article={}",code)
if __name__=="__main__":unittest.main()

import unittest
from pathlib import Path
from wiki_synonym_articles_v0628 import filter_explicit_topic_pages

class ExplicitTopicPageTests(unittest.TestCase):
    def test_reject_previous_topic(self):
        pages=[{"title":"量子ビット","summary":"量子情報の基本単位","source":"https://example.org/qubit"}]
        self.assertEqual(filter_explicit_topic_pages(pages,"古典ビットについて教えて"),[])
    def test_keep_requested_topic(self):
        pages=[{"title":"古典ビット","summary":"古典的な情報単位","source":"https://example.org/bit"}]
        self.assertEqual(len(filter_explicit_topic_pages(pages,"古典ビットについて教えて")),1)
    def test_followup_without_subject_is_unfiltered(self):
        pages=[{"title":"量子ビット","summary":"量子情報","source":"https://example.org/qubit"}]
        self.assertEqual(len(filter_explicit_topic_pages(pages,"もう少し詳しく")),1)
    def test_integration(self):
        code=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn("filter_explicit_topic_pages([direct_article, synonym_article], raw_user_text)",code)

if __name__=="__main__":unittest.main()

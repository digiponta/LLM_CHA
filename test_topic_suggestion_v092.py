import unittest
from topic_suggestion_v092 import topic_request,suggest

CORPUS=("量子力学的な粒子の波動は宇宙全体に広がる。\n"
        "エネルギー準位は外力により分裂。\n"
        "量子力学で言う零点エネルギーのアナロジ。")

class TopicSuggestionTests(unittest.TestCase):
    def test_quantum_topic(self):
        r=suggest("量子力学的な話題は",CORPUS)
        self.assertEqual(r["route"],"TOPIC_SUGGESTION_CORPUS")
        self.assertIn("粒子と波動",r["answer"])
        self.assertNotEqual(r["answer"],"未学習です")
        self.assertFalse(r["verified"])
    def test_definition_unaffected(self):
        self.assertIsNone(suggest("量子力学とは",CORPUS))
    def test_math_definition_unaffected(self):
        self.assertIsNone(suggest("数学とは",CORPUS))
    def test_literature_definition_unaffected(self):
        self.assertIsNone(suggest("文学とは",CORPUS))
    def test_generic_topic(self):
        self.assertEqual(suggest("何か話題はありますか",CORPUS)["route"],
                         "TOPIC_SUGGESTION_CORPUS")
    def test_no_corpus_still_suggests(self):
        r=suggest("量子力学的な話題は","")
        self.assertEqual(r["route"],"TOPIC_SUGGESTION")
    def test_unrelated_question_passes(self):
        self.assertIsNone(topic_request("今日の天気は"))
if __name__=="__main__":unittest.main()

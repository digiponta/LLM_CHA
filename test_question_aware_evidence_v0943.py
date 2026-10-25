import unittest
from question_aware_evidence_v0943 import question_intent,select_evidence
from explicit_topic_corpus_v0941 import augment_explicit_answer

class QuestionAwareTests(unittest.TestCase):
    def setUp(self):
        self.corpus=("数学は、文学の分類。\n"
            "数学的に証明される。\n"
            "量子力学に通じる言葉。\n"
            "量子力学的に考えると粒子の波動は宇宙全体に広がっている存在。")
    def test_definition_intent(self):
        self.assertEqual(question_intent("数学とは"),"DEFINITION")
    def test_discussion_intent(self):
        self.assertEqual(question_intent("量子力学について"),"DISCUSSION")
    def test_math_subject_relation_preserved(self):
        r=augment_explicit_answer("数学","Wikipediaでの説明",self.corpus,"数学とは")
        self.assertIn("数学は、文学の分類。",r["answer"])
        self.assertIn("直接的な定義は見つからず",r["answer"])
    def test_literature_incidental_only_suppressed(self):
        r=augment_explicit_answer("文学","Wikipediaでの説明",self.corpus,"文学とは")
        self.assertEqual(r["route"],"EXPLICIT_TOPIC_WIKIPEDIA_ONLY")
        self.assertNotIn("数学は、文学の分類。",r["answer"])
    def test_quantum_discussion_precedes_incidental(self):
        r=select_evidence("量子力学",self.corpus,"量子力学とは")
        self.assertEqual(r["selected"][0]["role"],"TOPIC_DISCUSSION")
        self.assertGreaterEqual(r["suppressed_incidental"],1)
    def test_missing_topic_falls_back(self):
        self.assertEqual(select_evidence("古生物学",self.corpus)["selected"],[])
    def test_metadata_preserves_unverified(self):
        r=augment_explicit_answer("数学","Wiki",self.corpus,"数学とは")
        self.assertFalse(r["auto_promote"])
        self.assertFalse(r["train_ready"])
if __name__=="__main__":unittest.main()

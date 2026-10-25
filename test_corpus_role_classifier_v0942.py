import unittest
from corpus_role_classifier_v0942 import classify,rank_mentions
from explicit_topic_corpus_v0941 import corpus_mentions,augment_explicit_answer

class RoleClassifierTests(unittest.TestCase):
    def test_math_subject_relation(self):
        self.assertEqual(classify("数学","数学は、文学の分類。"),"SUBJECT_RELATION")
    def test_literature_object_not_definition(self):
        self.assertEqual(classify("文学","数学は、文学の分類。"),"INCIDENTAL_MENTION")
    def test_definition_priority(self):
        corpus="数学的に証明される。\n数学は、文学の分類。\n数学とは数の研究をする学問のことである。"
        self.assertEqual(rank_mentions("数学",corpus)[0]["role"],"DIRECT_DEFINITION")
    def test_quantum_incidental_mention(self):
        self.assertEqual(classify("量子力学","量子力学に通じる言葉。"),"INCIDENTAL_MENTION")
    def test_quantum_discussion_priority(self):
        corpus="量子力学に通じる言葉。\n量子力学的に考えると粒子の波動は宇宙全体に広がっている存在。"
        self.assertEqual(rank_mentions("量子力学",corpus)[0]["role"],"TOPIC_DISCUSSION")
    def test_preserve_original_wording(self):
        text="数学は、文学の分類。\n数学的に証明される。"
        r=augment_explicit_answer("数学","数学は研究分野。",text)
        self.assertIn("数学は、文学の分類。",r["answer"])
        self.assertIn("[SUBJECT_RELATION]",r["answer"])
        self.assertFalse(r["auto_promote"])
    def test_no_match(self):
        self.assertEqual(corpus_mentions("古生物学","数学は、文学の分類。"),[])
if __name__=="__main__":unittest.main()

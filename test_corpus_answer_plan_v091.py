import unittest
from corpus_answer_plan_v091 import route

class CorpusAnswerPlanTests(unittest.TestCase):
    def setUp(self):
        self.corpus=("量子力学で表現可能な動的平衡状態にある系では、外力により準位が分裂。\n"
                     "数学とは数量と構造について研究する学問のことである。\n"
                     "宇宙の広がりについて述べる。")
    def test_mentions_not_definition(self):
        r=route("量子力学とは",self.corpus)
        self.assertEqual(r["route"],"CORPUS_THEN_EXTERNAL_DEFINITION")
        self.assertEqual(len(r["corpus_evidence"]),1)
    def test_explicit_definition_candidate(self):
        self.assertEqual(route("数学とは",self.corpus)["route"],"CORPUS_DEFINITION_CANDIDATE")
    def test_missing_topic_fallback(self):
        self.assertEqual(route("古生物学とは",self.corpus)["route"],"EXTERNAL_FALLBACK_CANDIDATE")
    def test_nondefinition_topic(self):
        self.assertEqual(route("宇宙について",self.corpus)["route"],"CORPUS_CONTEXT_CANDIDATE")
    def test_empty_input(self):
        self.assertEqual(route("",self.corpus)["route"],"INVALID_INPUT")
    def test_known_topic_without_definition_uses_corpus_then_external(self):
        r=route("量子力学とは",self.corpus)
        self.assertEqual(r["route"],"CORPUS_THEN_EXTERNAL_DEFINITION")
        self.assertGreater(len(r["corpus_evidence"]),0)
    def test_unknown_topic_has_no_corpus_evidence(self):
        r=route("古生物学とは",self.corpus)
        self.assertEqual(r["route"],"EXTERNAL_FALLBACK_CANDIDATE")
        self.assertEqual(r["corpus_evidence"],[])
    def test_unverified_not_promoted(self):
        self.assertFalse(route("数学とは",self.corpus)["corpus_is_verified_fact"])
if __name__=="__main__":
    unittest.main()

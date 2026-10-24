import unittest
from aspect_relevance_v074427 import ranked_evidence

def wiki(text):
    return {"status":"FOUND","url":"https://ja.wikipedia.org/wiki/量子力学","extract":text}

class RankingTests(unittest.TestCase):
    def test_explanation_over_generic_definition(self):
        d=wiki("量子力学は、現代物理学の根幹を成す理論の一つであり非常に重要な分野である。"
               "量子力学の基本原理は、物理系の状態を波動関数で記述することによって現象を表現するものである。")
        x=ranked_evidence(d,"基本原理")
        self.assertIn("波動関数",x["answer"])
    def test_formula_name_only_rejected(self):
        d=wiki("エルヴィン・シュレーディンガーによって創始されたシュレーディンガー方程式は歴史的に重要である。")
        self.assertIsNone(ranked_evidence(d,"数式"))
    def test_experiment_relevance(self):
        d=wiki("この理論は重要であり様々な物理学の分野で古くから議論されている。"
               "量子力学の実験では、粒子の状態を測定することによって理論の予測を観測している。")
        self.assertIn("実験",ranked_evidence(d,"実験")["answer"])
    def test_missing_source(self):
        self.assertIsNone(ranked_evidence({"status":"FOUND","extract":"量子力学の実験では様々な粒子の運動を測定する。"},"実験"))
    def test_unverified(self):
        x=ranked_evidence(wiki("量子力学の実験では粒子の状態を測定することによって現象の観測を行う。"),"実験")
        self.assertEqual(x["truth_state"],"EXTERNAL_UNVERIFIED")
        self.assertFalse(x["train_ready"])
if __name__=="__main__":unittest.main()

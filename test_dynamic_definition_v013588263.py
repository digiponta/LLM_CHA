import unittest
from evidence_dynamic_definition_v013588263 import bind,explicit_definition
def ev(title,text):
    return {"status":"EVIDENCE","topic":title,"excerpt":text,"url":"https://example.invalid/fixture"}
class DynamicDefinitionTests(unittest.TestCase):
 def test_dark_energy(self):
    s="ダークエネルギー（英: dark energy）とは、宇宙全体に広がる仮説上のエネルギーである。"
    self.assertEqual(bind("ダークエネルギーとは",ev("ダークエネルギー",s))["status"],"BOUND_EXTRACT_ACCEPTED")
 def test_quantum_mechanics(self):
    s="量子力学（英: quantum mechanics）は、現代物理学の根幹を成す理論・分野。"
    self.assertEqual(bind("量子力学とは",ev("量子力学",s))["status"],"BOUND_EXTRACT_ACCEPTED")
 def test_photoelectric(self):
    s="光電効果（英: photoelectric effect）とは、物質に光を照射したときに電子が放出される現象である。"
    self.assertEqual(bind("光電効果とは",ev("光電効果",s))["status"],"BOUND_EXTRACT_ACCEPTED")
 def test_history_abstains(self):
    s="20世紀前半までは天文学者の間で宇宙は定常的と考えられていた。"
    self.assertNotEqual(bind("宇宙とは",ev("宇宙",s))["status"],"BOUND_EXTRACT_ACCEPTED")
 def test_unrelated_source_rejected(self):
    s="光電効果とは、電子の放出が起こる現象である。"
    self.assertEqual(bind("量子力学とは",ev("光電効果",s))["status"],"ABSTAIN_SUBJECT_MISMATCH")
 def test_lexical_translation_not_definition(self):
    s="「宇宙」という単語は一般には、cosmos, universe の訳語として用いられる。"
    self.assertFalse(explicit_definition(s,"宇宙"))
 def test_consequence_not_cause(self):
    s="宇宙は膨張することによって平均密度が低下する。"
    self.assertNotEqual(bind("宇宙はなぜ膨張するのか",ev("宇宙",s))["status"],"BOUND_EXTRACT_ACCEPTED")
if __name__=="__main__":unittest.main()

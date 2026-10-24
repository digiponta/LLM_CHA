import unittest
from wiki_fragment_gate_v074428 import coherent_scientific_evidence as ok
class WikiFragmentGateTests(unittest.TestCase):
    def test_tex_orphan(self): self.assertFalse(ok(r"{\\displaystyle \\hbar }"))
    def test_missing_sentence_subject(self): self.assertFalse(ok("はディラック定数、Ψ(x, t) は波動関数、ˆH は系のハミルトニアンである"))
    def test_equation_intro_without_equation(self): self.assertFalse(ok("シュレーディンガー方程式は、最も基本的な形では以下のように表される"))
    def test_short_name_origin(self): self.assertFalse(ok("名前はエルヴィン・シュレーディンガーにちなむ"))
    def test_good_science(self): self.assertTrue(ok("状態ベクトルの時間発展は、シュレーディンガー方程式で表される"))
if __name__=="__main__": unittest.main()

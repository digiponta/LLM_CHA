import unittest
from aspect_evidence_v074425 import choose_aspect,extract_aspect
class AspectTests(unittest.TestCase):
    def test_aspect(self):self.assertEqual(choose_aspect("数式"),"数式")
    def test_not_question(self):self.assertIsNone(choose_aspect("数式について全部教えて"))
    def test_with_provenance(self):
        d={"status":"FOUND","url":"https://ja.wikipedia.org/wiki/Test","extract":"この理論の原理は観測の結果と対応するように構築されている。"}
        self.assertEqual(extract_aspect(d,"基本原理")["truth_state"],"EXTERNAL_UNVERIFIED")
    def test_without_evidence(self):
        d={"status":"FOUND","url":"https://ja.wikipedia.org/wiki/Test","extract":"記述がありません。"}
        self.assertIsNone(extract_aspect(d,"数式"))
    def test_missing_source(self):
        self.assertIsNone(extract_aspect({"status":"FOUND","extract":"実験で測定されている。"},"実験"))
if __name__=="__main__":unittest.main()

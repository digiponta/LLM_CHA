import unittest
from clipboard_attribute_retrieval_v09759 import retrieve

SOURCE = """スファレライト
スファレライト（閃亜鉛鉱）は硫化亜鉛（ZnS）の鉱物。
基本データ
化学組成: ZnS（硫化亜鉛）
モース硬度: 3.5 〜 4（非常に脆い）
屈折率: 2.37（ダイヤモンドは2.42）
分散度: ダイヤモンドの約4倍
主な産地: スペイン、メキシコ、アメリカ
"""

class AttributeRetrievalTests(unittest.TestCase):
    def test_followups(self):
        cases={"硬度は？":"3.5", "屈折率は？":"2.37",
               "主な産地は？":"スペイン", "分散度は？":"約4倍",
               "化学組成を知りたい":"ZnS"}
        for q, expected in cases.items():
            with self.subTest(q=q):
                self.assertIn(expected,retrieve(q,SOURCE,"スファレライト"))

    def test_explicit_subject(self):
        self.assertIn("2.37",retrieve("スファレライトの屈折率は？",SOURCE))

    def test_wrong_topic(self):
        self.assertIsNone(retrieve("ダイヤモンドの硬度は？",SOURCE))

    def test_no_evidence(self):
        self.assertIsNone(retrieve("硬度は？","スファレライトについての紹介","スファレライト"))

    def test_ambiguous_values(self):
        s="スファレライト\nモース硬度: 2\nモース硬度: 4"
        self.assertIsNone(retrieve("硬度は？",s,"スファレライト"))

    def test_no_inference(self):
        self.assertIsNone(retrieve("なぜ虹色に輝くの？",SOURCE,"スファレライト"))

    def test_no_context(self):
        self.assertIsNone(retrieve("硬度は？",SOURCE))

if __name__=="__main__":
    unittest.main()

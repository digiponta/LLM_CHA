import unittest
from audit_japanese_foundation_v01346 import normalize,find_overlap,audit
class Tok:
    def encode(self,s):return list(s)
class AuditTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize("Ａ Ｂ\nＣ"),"ABC")
    def test_exact(self):
        a,b=find_overlap(["これは長い日本語文章です。"],["全く異なる文章を用います。"],["これは長い日本語文章です。"])
        self.assertEqual(len(a),1)
    def test_near(self):
        a,b=find_overlap(["研究者は装置の出力を測定し記録を残した。"],["研究者は装置の出力を測定し記録を残した。違い"],[])
        self.assertFalse(a);self.assertEqual(len(b),1)
    def test_tiny_data_fails(self):
        r=audit(["短い文"],["別の文"],["保留文"],Tok())
        self.assertEqual(r["status"],"NOT_READY")
        self.assertIn("INSUFFICIENT_TRAIN_TOKENS",r["issues"])
    def test_can_pass_size(self):
        r=audit(["ひらがなの練習です。"],["漢字の練習です。"],["数字の練習です。"],Tok(),1,1)
        self.assertEqual(r["status"],"READY_FOR_TRAINING")
if __name__=="__main__":unittest.main()

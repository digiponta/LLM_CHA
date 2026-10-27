import unittest
from audit_aozora_quality_v01348 import assess
class Tokenizer:
    def encode(self,s):return list(s)
class AuditQualityTests(unittest.TestCase):
    def test_inline_ruby_suspected(self):
        r=assess(["吾輩わがはいは猫である。"],Tokenizer())
        self.assertGreater(r["possible_ruby_occurrences"],0)
        self.assertFalse(r["training_approved"])
    def test_no_auto_modification(self):
        s="吾輩わがはいは猫である。"
        r=assess([s],Tokenizer())
        self.assertEqual(r["characters"],len(s))
    def test_bpe_count(self):
        r=assess(["これは文章です。","別の文章です。"],Tokenizer())
        self.assertEqual(r["bpe_tokens"],len("これは文章です。")+len("別の文章です。"))
    def test_anomaly(self):
        r=assess(["長い文章"+("あ"*510)],Tokenizer())
        self.assertEqual(r["anomalies"][0]["reason"],"LONG_SENTENCE")
    def test_review_always_required(self):
        r=assess(["普通の日本語です。"],Tokenizer())
        self.assertEqual(r["status"],"REVIEW_REQUIRED")
if __name__=="__main__":unittest.main()

import unittest
from sense_definition_quality_v013588270 import qualify,evaluate

def candidate(subject,meaning):
    return {"id":"sense-old","subject":subject,"meaning":meaning,
            "evidence_sentence":subject+"とは、"+meaning+"。",
            "source_topic":subject,"source_url":"https://example.invalid",
            "review_status":"PENDING_HUMAN_REVIEW","approved":False}

class QualityTests(unittest.TestCase):
    def test_leading_comma_normalized(self):
        r,reason=qualify(candidate("光電効果","、光を照射すると電子が放出される現象である"))
        self.assertIsNone(reason)
        self.assertEqual(r["meaning"],"光を照射すると電子が放出される現象である")
    def test_history_not_definition(self):
        r,reason=qualify(candidate("ビッグバン理論","紆余曲折を経て認められるようになってきた歴史がある"))
        self.assertIsNone(r)
        self.assertEqual(reason,"NON_DEFINITION")
    def test_mineral(self):
        self.assertIsNotNone(qualify(candidate("閃亜鉛鉱","亜鉛の硫化鉱物である"))[0])
    def test_quantum(self):
        self.assertIsNotNone(qualify(candidate("量子力学","現代物理学の根幹を成す理論・分野"))[0])
    def test_big_bang(self):
        self.assertIsNotNone(qualify(candidate("ビッグバン","宇宙開始時の爆発的膨張"))[0])
    def test_unrelated_prose_rejected(self):
        self.assertIsNone(qualify(candidate("光電効果","研究が進められている"))[0])
    def test_review_not_transferred(self):
        original=candidate("光電効果","、電子が放出される現象である")
        original["approved"]=True
        r=evaluate({"candidates":[original]})
        self.assertFalse(r["accepted"][0]["approved"])
        self.assertFalse(r["id_migrations"][0]["review_transfer_allowed"])
    def test_five_source_candidates(self):
        rows=[candidate("ビッグバン","、宇宙開始時の爆発的膨張"),
              candidate("ビッグバン理論","紆余曲折を経て認められるようになってきた歴史がある"),
              candidate("閃亜鉛鉱","亜鉛の硫化鉱物である"),
              candidate("量子力学","現代物理学の根幹を成す理論・分野"),
              candidate("光電効果","、電子が放出される現象である")]
        report=evaluate({"candidates":rows})
        self.assertEqual(report["candidate_count_after"],4)
        self.assertEqual(len(report["rejected"]),1)
        self.assertEqual(report["approved_count"],0)

if __name__=="__main__":unittest.main()

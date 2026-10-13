import unittest
from persona_quality_benchmark_v0422 import score,validate

def row(id,split,q,a,bad,agree,sem,accepted=True,source="DEVELOPMENT_EXAMPLE"):
    return {"id":id,"split":split,"question":q,"answer":a,
            "gold_inappropriate":bad,"agreement":agree,
            "semantic_agreement":sem,"runtime_accepted":accepted,
            "label_source":source}
class BenchmarkTests(unittest.TestCase):
    def test_dev_confusion_matrix(self):
        data=[
            row("good-divergent","development","今日は何をしていたの","特に変化はない。",False,.333,.85),
            row("bad-fragment","development","貴方は誰","連載後半は対話。 |読切・",True,.032,.881),
            row("good-clean","development","こんにちは","こんにちは。",False,.9,.9),
            row("bad-undetected","development","こんにちは","物理学の論文です。",True,.9,.9)
        ]
        s=score(data,split="development")
        self.assertEqual((s["tp"],s["fp"],s["tn"],s["fn"]),(1,1,1,1))
        self.assertEqual(s["precision"],.5)
        self.assertEqual(s["recall"],.5)
        self.assertEqual(s["false_positive_rate"],.5)
        self.assertEqual(s["false_negative_rate"],.5)
        self.assertFalse(s["runtime_decisions_modified"])
    def test_no_holdout_claim(self):
        dev=[row("dev","development","こんにちは","こんにちは。",False,.9,.9)]
        s=score(dev,split="holdout")
        self.assertEqual(s["benchmark_status"],"NO_LABELED_SAMPLES")
        self.assertIsNone(s["precision"])
        self.assertIsNone(s["recall"])
        self.assertFalse(s["independent_holdout_claimed"])
    def test_holdout_review_required(self):
        x=row("x","holdout","こんにちは","こんにちは。",False,.9,.9)
        with self.assertRaises(ValueError):validate(x)
    def test_holdout_review_allowed_but_no_independence_claim(self):
        x=row("x","holdout","こんにちは","こんにちは。",False,.9,.9,source="HUMAN_REVIEW")
        s=score([x],split="holdout")
        self.assertEqual(s["count"],1)
        self.assertFalse(s["independent_holdout_claimed"])
    def test_duplicate_ids(self):
        x=row("x","development","こんにちは","こんにちは。",False,.9,.9)
        with self.assertRaises(ValueError):score([x,x],split="development")
    def test_bad_score_and_bool(self):
        x=row("x","development","こんにちは","こんにちは。",False,2,.9)
        with self.assertRaises(ValueError):validate(x)
        x["agreement"]=.5;x["gold_inappropriate"]=1
        with self.assertRaises(ValueError):validate(x)
    def test_zero_denominator(self):
        x=row("a","development","こんにちは","こんにちは。",False,.9,.9)
        s=score([x],split="development")
        self.assertIsNone(s["precision"])
        self.assertIsNone(s["recall"])
        self.assertIsNone(s["false_negative_rate"])
    def test_split_isolation(self):
        a=row("a","development","こんにちは","こんにちは。",False,.9,.9)
        b=row("b","holdout","こんにちは","ひどく不適切な文章",True,.9,.9,source="HUMAN_REVIEW")
        self.assertEqual(score([a,b],split="development")["count"],1)
        self.assertEqual(score([a,b],split="holdout")["count"],1)
if __name__=="__main__":unittest.main()

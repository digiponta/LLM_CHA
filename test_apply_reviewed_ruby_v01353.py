import unittest
from apply_reviewed_ruby_v01353 import apply_review,propose
class ApplyReviewedRubyTests(unittest.TestCase):
    def sample(self):
        return {"version":"v0.13.52","manual_review_complete":True,"review_items":[
            {"id":"L1-C0","line":1,"start":0,"end":7,"surface":"肝心かんじんの",
             "kanji":"肝心","reading":"かんじん","decision":"ACCEPT"},
            {"id":"L2-C0","line":2,"start":0,"end":3,"surface":"見ると",
             "kanji":"見","reading":None,"decision":"REJECT"}]}
    def test_approved_only(self):
        out,changes=apply_review(["肝心かんじんの話。","見ると分かる。"],self.sample())
        self.assertEqual(out,["肝心の話。","見ると分かる。"])
        self.assertEqual(len(changes),1)
    def test_missing_reading_requires_override(self):
        item={"id":"L1-C0","line":1,"start":0,"end":8,
              "surface":"照準しょうじゅん","kanji":"照準","reading":None}
        with self.assertRaises(ValueError):propose(item,"照準しょうじゅん")
        p=propose(item,"照準しょうじゅん",{"kanji":"照準","reading":"しょうじゅん"})
        self.assertEqual(p["removed"],"しょうじゅん")
    def test_mismatch_rejected(self):
        item=self.sample()["review_items"][0]
        with self.assertRaises(ValueError):propose(item,"別物かんじんの話")
    def test_not_final_rejected(self):
        r=self.sample();r["manual_review_complete"]=False
        with self.assertRaises(ValueError):apply_review(["肝心かんじんの話。","見ると分かる。"],r)
    def test_no_unsure_edits(self):
        r=self.sample();r["review_items"][0]["decision"]="UNSURE"
        out,changes=apply_review(["肝心かんじんの話。","見ると分かる。"],r)
        self.assertEqual(changes,[])
        self.assertEqual(out[0],"肝心かんじんの話。")
if __name__=="__main__":unittest.main()

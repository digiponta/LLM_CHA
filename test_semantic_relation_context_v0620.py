import unittest
from semantic_relation_context_v0620 import RelationContext,grounded_attribute_answer,clarification

class RelationTests(unittest.TestCase):
    def test_explicit(self):
        r=RelationContext().observe("トヨタの歴史")
        self.assertEqual((r["subject"],r["attribute"]),("トヨタ","歴史"))
    def test_topic_followup(self):
        c=RelationContext()
        self.assertIsNone(c.observe("トヨタの話題"))
        self.assertEqual(c.observe("歴史")["subject"],"トヨタ")
    def test_context_reset(self):
        c=RelationContext();c.observe("トヨタの話題");c.observe("長門")
        self.assertIsNone(c.observe("歴史"))
    def test_sourced_attribute(self):
        wiki={"status":"FOUND","url":"https://ja.wikipedia.org/wiki/X","summary":"この企業の歴史は長い。"}
        result=grounded_attribute_answer({"subject":"X","attribute":"歴史"},wiki)
        self.assertIn("歴史",result["answer"])
    def test_no_unrelated_assertion(self):
        wiki={"status":"FOUND","url":"https://ja.wikipedia.org/wiki/X","summary":"自動車を製造する企業。"}
        self.assertIsNone(grounded_attribute_answer({"subject":"X","attribute":"所在地"},wiki))
    def test_clarify(self):
        self.assertIn("価格",clarification({"subject":"X","attribute":"価格"}))
if __name__=="__main__":unittest.main()

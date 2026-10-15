import unittest
from wiki_typed_propositions_v0532 import extract, assess
S="超伝導量子干渉計 (SQUID) とは、ジョセフソン接合を含む環状超伝導体に基く、極めて弱い磁場の検出に用いられる非常に感度の高い磁気センサの一種である。"
U="https://ja.wikipedia.org/wiki/超伝導量子干渉計"
class TypedPropositionTests(unittest.TestCase):
 def setUp(self):self.records=extract(S,U)
 def test_four(self):self.assertEqual(len(self.records),4)
 def test_subject(self):self.assertTrue(all(x["subject"]=="超伝導量子干渉計 (SQUID)" for x in self.records))
 def test_types(self):self.assertEqual([x["type"] for x in self.records],["COMPONENT","STRUCTURE","FUNCTION","PERFORMANCE"])
 def test_components(self):self.assertEqual(self.records[0]["object"],"ジョセフソン接合")
 def test_structure(self):self.assertEqual(self.records[1]["object"],"環状超伝導体")
 def test_function(self):self.assertEqual(self.records[2]["object"],"極めて弱い磁場")
 def test_performance(self):self.assertEqual(self.records[3]["object"],"非常に高い感度")
 def test_provenance(self):self.assertTrue(all(x["source"]==U and x["original"]==S and x["evidence_span"] in S for x in self.records))
 def test_never_promote(self):self.assertTrue(all(not x["verified"] and not x["promoted"] and not x["train_ready"] for x in self.records))
 def test_no_causality(self):self.assertTrue(all(not x["inferred_causality"] for x in self.records))
 def test_why_reject(self):self.assertFalse(any(x["answerable"] for x in assess(self.records,"なぜ高感度なの？")))
 def test_structure_question(self):self.assertEqual(sum(x["answerable"] for x in assess(self.records,"構造は？")),2)
 def test_detection_question(self):self.assertEqual(sum(x["answerable"] for x in assess(self.records,"何を検出する？")),1)
 def test_unrelated(self):self.assertEqual(extract("ただの短い文章。",U),[])
 def test_unsplit(self):self.assertEqual(extract("SQUIDとは、磁気センサである。",U),[])
if __name__=="__main__":unittest.main()

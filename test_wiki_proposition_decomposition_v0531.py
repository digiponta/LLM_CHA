import unittest
from wiki_proposition_decomposition_v0531 import decompose
from wiki_causal_diagnostics_v0530 import diagnose_extract

TEXT="超伝導量子干渉計 (superconducting quantum interference device, SQUID) とは、ジョセフソン接合を含む環状超伝導体に基く、極めて弱い磁場の検出に用いられる非常に感度の高い磁気センサの一種である。"
URL="https://ja.wikipedia.org/wiki/超伝導量子干渉計"
class PropositionDecompositionTests(unittest.TestCase):
 def test_two_propositions(self):
  parts=decompose(TEXT,URL)
  self.assertEqual(len(parts),2)
  self.assertEqual([p["kind"] for p in parts],["STRUCTURE","ROLE"])
 def test_subject_repeated(self):
  p=decompose(TEXT,URL)
  self.assertTrue(all(x["text"].startswith("超伝導量子干渉計") for x in p))
 def test_content_preserved(self):
  p=decompose(TEXT,URL)
  self.assertIn("ジョセフソン接合",p[0]["text"])
  self.assertIn("高い磁気センサ",p[1]["text"])
 def test_provenance(self):
  self.assertTrue(all(x["source"]==URL and x["original"]==TEXT for x in decompose(TEXT,URL)))
 def test_no_inferred_causality(self):
  self.assertTrue(all(not x["inferred_causality"] for x in decompose(TEXT,URL)))
 def test_not_trained(self):
  self.assertTrue(all(not x["train_ready"] and not x["verified"] for x in decompose(TEXT,URL)))
 def test_unrelated_commas(self):
  self.assertEqual(len(decompose("これは、量子干渉、ジョセフソン接合などを扱う。")),1)
 def test_no_phantom_split(self):
  self.assertEqual(len(decompose("SQUIDとは、ジョセフソン接合に基く。")),1)
 def test_diagnostics(self):
  r=diagnose_extract(TEXT,URL)
  self.assertEqual(r["counts"]["sentences"],1)
  self.assertEqual(r["counts"]["decomposed_propositions"],2)
 def test_unsplit_metadata(self):
  p=decompose("SQUIDは高感度なセンサである。")[0]
  self.assertEqual(p["kind"],"UNSPLIT")
  self.assertFalse(p["inferred_causality"])
if __name__=="__main__":unittest.main()

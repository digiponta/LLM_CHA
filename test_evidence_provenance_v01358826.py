import unittest
from temporary_evidence_v01358824 import TemporaryEvidence
SAMPLE="スファレライト\n化学組成：ZnS（硫化亜鉛）\n屈折率：2.37\n産地：スペイン"
class ProvenanceTests(unittest.TestCase):
 def test_quote_matches_value(self):
  e=TemporaryEvidence();e.set_topic("スファレライト")
  self.assertTrue(e.add(SAMPLE,"clipboard",source_title="検索結果の貼付",retrieved_at="2026-10-29T16:00:00+09:00"))
  result=e.lookup("屈折率は？")
  self.assertEqual(result["value"],"2.37")
  self.assertEqual(result["quote"],"屈折率：2.37")
  self.assertEqual(result["source_title"],"検索結果の貼付")
  self.assertEqual(result["retrieved_at"],"2026-10-29T16:00:00+09:00")
  self.assertEqual(result["truth_state"],"EXTERNAL_UNVERIFIED")
 def test_missing_quote(self):
  e=TemporaryEvidence();e.set_topic("スファレライト")
  e.add("スファレライトの屈折率は約2.37。","clipboard")
  self.assertIsNone(e.lookup("屈折率は？"))
 def test_topic_isolation(self):
  e=TemporaryEvidence();e.set_topic("スファレライト");e.add(SAMPLE,"clipboard")
  e.set_topic("CPU")
  self.assertIsNone(e.lookup("屈折率は？"))
 def test_metadata_url(self):
  e=TemporaryEvidence();e.add(SAMPLE,"Wikipedia",topic="スファレライト",source_url="https://example.org/reference")
  self.assertEqual(e.lookup("化学組成は？")["source_url"],"https://example.org/reference")
if __name__=="__main__":unittest.main()

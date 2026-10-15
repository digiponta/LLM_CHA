import unittest
from wiki_proposition_comparison_v0537 import collect,compare,compare_all
from wiki_multi_evidence_alignment_v0536 import analyze
from urllib.parse import urlsplit,parse_qs
URL="https://ja.wikipedia.org/wiki/SQUID"
def item(p,o,source=URL):return {"subject":"SQUID","predicate":p,"object":o,"source":source}
def mock(url):
 params=parse_qs(urlsplit(url).query)
 if params.get("prop")==["links"]:
  return {"query":{"pages":[{"title":"SQUID","links":[{"title":"SQUIDの機能"}]}]}}
 title=params["titles"][0]
 sentence="SQUIDはジョセフソン接合を含む。" if title=="SQUID" else "SQUIDは微弱な磁場を検出する。"
 return {"query":{"pages":[{"title":title,"extract":sentence}]}}
class ComparisonTests(unittest.TestCase):
 def test_independent_contains(self):self.assertEqual(collect("SQUIDはジョセフソン接合を含む。",URL)[0]["predicate"],"contains")
 def test_independent_detects(self):self.assertEqual(collect("SQUIDは微弱な磁場を検出する。",URL)[0]["predicate"],"detects")
 def test_no_complex_split(self):self.assertEqual(collect("SQUIDは超伝導体を含む、そして高感度だ。",URL),[])
 def test_match(self):self.assertEqual(compare(item("contains","ジョセフソン接合"),item("contains","ジョセフソン接合"))["status"],"MATCH")
 def test_complement(self):self.assertEqual(compare(item("contains","ジョセフソン接合"),item("detects","磁場"))["status"],"COMPLEMENT")
 def test_conflict_candidate(self):self.assertEqual(compare(item("contains","ジョセフソン接合"),item("contains","非ジョセフソン接合"))["status"],"CONFLICT")
 def test_different_subject(self):
  other=item("contains","ジョセフソン接合");other["subject"]="MRI"
  self.assertEqual(compare(item("contains","ジョセフソン接合"),other)["status"],"INSUFFICIENT")
 def test_different_object_not_conflict(self):self.assertEqual(compare(item("detects","磁場"),item("detects","電場"))["status"],"INSUFFICIENT")
 def test_bounded(self):self.assertEqual(len(compare_all([item("contains",str(x)) for x in range(15)],max_pairs=4)),4)
 def test_multi_article(self):
  r=analyze({"status":"FOUND","title":"SQUID"},"なぜ高感度なの？",fetch=mock)
  self.assertEqual(r["status"],"EVIDENCE_COLLECTED")
  self.assertEqual(len(r["propositions"]),2)
  self.assertTrue(any(p["status"]=="COMPLEMENT" for p in r["comparison"]))
  self.assertFalse(r["causal_answer_approved"])
 def test_unverified(self):
  self.assertFalse(collect("SQUIDは微弱な磁場を検出する。",URL)[0]["verified"])
if __name__=="__main__":unittest.main()

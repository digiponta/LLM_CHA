import json,tempfile,unittest
from pathlib import Path
from semantic_proposition_v1090 import Proposition,compose_propositions
from propose_rse_unified_repair_v013588317 import propose
class PropositionComposeFixTests(unittest.TestCase):
 def test_single_preexisting_copula(self):
  x=compose_propositions([Proposition("閃亜鉛鉱","亜鉛の硫化鉱物である")])
  self.assertEqual(x,"閃亜鉛鉱は、亜鉛の硫化鉱物である。")
 def test_plain_value_unchanged(self):
  x=compose_propositions([Proposition("GPU","計算装置")])
  self.assertEqual(x,"GPUは、計算装置である。")
 def test_multi_mixed(self):
  x=compose_propositions([Proposition("GPU","高速である"),Proposition("GPU","並列計算が得意")])
  self.assertEqual(x,"GPUは、高速であり、並列計算が得意である。")
 def test_duplicate_mixed_values(self):
  x=compose_propositions([Proposition("鉱物","結晶である"),Proposition("鉱物","結晶")])
  self.assertEqual(x,"鉱物は、結晶である。")
 def test_dry_run_does_not_write_stores(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/"atomic.jsonl";u=Path(d)/"unified.jsonl"
   a.write_text(json.dumps({"subject":"閃亜鉛鉱","value":"亜鉛の硫化鉱物である"},ensure_ascii=False)+"\n",encoding="utf-8")
   u.write_text(json.dumps({"concept":"閃亜鉛鉱","assistant":"閃亜鉛鉱は、亜鉛の硫化鉱物であるである。"},ensure_ascii=False)+"\n",encoding="utf-8")
   before=(a.read_bytes(),u.read_bytes())
   x=propose(a,u)
   self.assertEqual(x["proposed_repairs"],1)
   self.assertEqual(x["changes"][0]["proposed"],"閃亜鉛鉱は、亜鉛の硫化鉱物である。")
   self.assertEqual(before,(a.read_bytes(),u.read_bytes()))
if __name__=="__main__":unittest.main()

import unittest
from chat_semantic_router_v0135844 import route
class Tests(unittest.TestCase):
 def test_default_off(self):
  self.assertIsNone(route("『吾輩は猫である』の著者は？",environ={}))
 def test_missing_paths_fallback(self):
  self.assertIsNone(route("『吾輩は猫である』の著者は？",environ={"LLM_CHA_SEMANTIC_RUNTIME":"1"}))
 def test_missing_stores_fallback(self):
  self.assertIsNone(route("『吾輩は猫である』の著者は？",environ={
   "LLM_CHA_SEMANTIC_RUNTIME":"1","LLM_CHA_SEMANTIC_PROPOSITIONS":"no-props.jsonl",
   "LLM_CHA_SEMANTIC_TRUTH":"no-truth.jsonl","LLM_CHA_SEMANTIC_MANIFEST":"no-manifest.json"}))
if __name__=="__main__":unittest.main()

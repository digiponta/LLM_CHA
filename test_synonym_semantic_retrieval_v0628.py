import unittest
import json
from synonym_semantic_retrieval_v0628 import allowable_substitution,trace_match

class SemanticSynonymTests(unittest.TestCase):
    def test_synonym_rewrite_allowed(self):
        self.assertTrue(allowable_substitution("SYNONYM"))
    def test_related_not_equivalent(self):
        for relation in ("RELATED","BROADER","NARROWER"):
            self.assertFalse(allowable_substitution(relation))
    def test_unknown_relation_rejected(self):
        with self.assertRaises(ValueError):allowable_substitution("CAUSES")
    def test_trace(self):
        result=trace_match("クルマ","自動車","WIKIPEDIA","https://ja.wikipedia.org/wiki/自動車","EXTERNAL_UNVERIFIED")
        self.assertEqual(result.relation,"SYNONYM")
        self.assertEqual(json.loads(result.as_json())["requested"],"クルマ")
    def test_exact(self):
        self.assertEqual(trace_match("猫","猫","CORPUS","local","UNVERIFIED").relation,"EXACT")
if __name__=="__main__":unittest.main()

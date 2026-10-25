import unittest
from types import SimpleNamespace
from clipboard_grounded_generation_v09714 import experiment

DOC="""Quantum Hyper-Aether
A quantum-inspired distributed computing concept in which virtual machines, language models, and neural networks cooperate through meaning, purpose, context, and knowledge.
Semantic Routing
"""
class ModelGenerationTests(unittest.TestCase):
    def test_real_generate_called_but_not_automatically_selected(self):
        calls=[]
        def generate(**kw):
            calls.append(kw)
            return SimpleNamespace(text="Quantum Hyper-Aetherは未検証の考察です。",token_count=17)
        result=experiment("このページでQuantum Hyper-Aetherについて記述は？",
                          DOC,object(),object(),generate)
        self.assertEqual(len(calls),1)
        self.assertEqual(result["generation_origin"],"REAL_CHECKPOINT")
        self.assertEqual(result["selected"],result["baseline"])
        self.assertFalse(result["candidate_auto_selected"])
        self.assertFalse(result["train_ready"])
    def test_no_evidence_no_generation(self):
        def fail(**kwargs):
            raise AssertionError("generator should not be called")
        result=experiment("無関係", "",object(),object(),fail)
        self.assertEqual(result["status"],"NO_EVIDENCE")
    def test_prompt_contains_source(self):
        def generate(**kwargs):
            self.assertIn("virtual machines",kwargs["prompt"])
            return SimpleNamespace(text="不明",token_count=2)
        result=experiment("このページでQuantum Hyper-Aetherについて記述は？",
                          DOC,object(),object(),generate)
        self.assertFalse(result["gate"]["accept"])
        self.assertIn("関連する後続記述",result["selected"])
if __name__=="__main__":unittest.main()

import unittest
from clipboard_context_expansion_v09712 import expand,answer
from clipboard_context_v0976 import ClipboardContext
TEXT="""Quantum Hyper-Aether
A quantum-inspired distributed computing concept in which virtual machines, language models, and neural networks cooperate through meaning, purpose, context, and knowledge.
Semantic Routing
VM Dynamics
Semantic Operating Systems
An operating-system direction that treats semantic tasks—not only processes and files—as first-class units for decomposition, scheduling, routing, memory, and answer generation.
Task Decomposition
Semantic Scheduler
"""
class StructuredAssociationTests(unittest.TestCase):
    def test_exact_quantum_heading(self):
        result=expand("このページでQuantum Hyper-Aetherについて記述は？",TEXT)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["topic"],"Quantum Hyper-Aether")
        self.assertIn("virtual machines",result[0]["description"])
    def test_semantic_os_no_neighbor_heading(self):
        result=expand("このページでSemantic Operating Systemsについて記述は？",TEXT)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["topic"],"Semantic Operating Systems")
        self.assertIn("semantic tasks",result[0]["description"])
    def test_answer_deduplicates_description(self):
        value=answer("このページでSemantic Operating Systemsについて記述は？",TEXT)
        self.assertEqual(value.count("An operating-system direction"),1)
    def test_heading_not_linked_across_short_labels(self):
        result=expand("このページでSemantic Routingについて記述は？",TEXT)
        self.assertEqual(result[0]["topic"],"Semantic Routing")
        self.assertIsNone(result[0]["description"])
    def test_unverified(self):
        self.assertFalse(any(x["truth_state"]!="EXTERNAL_UNVERIFIED" for x in expand("Quantum Hyper-Aether",TEXT)))
    def test_existing_context(self):
        context=ClipboardContext();context.set(TEXT)
        self.assertIn("virtual machines",context.answer("このページでQuantum Hyper-Aetherについて記述は？"))
if __name__=="__main__":unittest.main()

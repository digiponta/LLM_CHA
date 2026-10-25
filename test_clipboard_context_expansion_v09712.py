import unittest
from clipboard_context_expansion_v09712 import expand,answer
from clipboard_context_v0976 import ClipboardContext
DOC="""Personal Research
Quantum Hyper-Aether
A quantum-inspired distributed computing concept in which virtual machines, language models, and neural networks cooperate through meaning, purpose, context, and knowledge.
Semantic Routing
VM Dynamics
Semantic Operating Systems
An operating-system direction that treats semantic tasks—not only processes and files—as first-class units for decomposition, scheduling, routing, memory, and answer generation.
Task Decomposition
Semantic Scheduler
"""
class ExpansionTests(unittest.TestCase):
    def test_quantum_heading_has_description(self):
        hits=expand("このページでQuantum Hyper-Aetherについて記述は？",DOC)
        item=next(x for x in hits if x["topic"]=="Quantum Hyper-Aether")
        self.assertIn("quantum-inspired",item["description"])
    def test_semantic_os_description(self):
        hits=expand("このページでSemantic Operating Systemsについて記述は？",DOC)
        item=next(x for x in hits if x["topic"]=="Semantic Operating Systems")
        self.assertIn("semantic tasks",item["description"])
    def test_non_llm_and_unverified(self):
        self.assertTrue(all(x["truth_state"]=="EXTERNAL_UNVERIFIED" for x in expand("Semantic Operating Systems",DOC)))
    def test_context_integration(self):
        c=ClipboardContext();c.set(DOC)
        self.assertIn("virtual machines",c.answer("このページでQuantum Hyper-Aetherについて記述は？"))
    def test_empty(self):
        self.assertEqual(expand("研究",""),[])
if __name__=="__main__":unittest.main()

import tempfile,unittest
from pathlib import Path
from runtime_reference_integration_v023352 import SessionReferenceStore,RuntimeReferenceBridge
from safe_reference_semantic_bridge_v023354 import SafeReferenceSemanticBridge,render_safe_semantic_result

class SafeBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.store=SessionReferenceStore(root/"references.db")
        self.propositions=root/"facts.jsonl"
        self.bridge=SafeReferenceSemanticBridge(self.store,self.propositions)
        self.runtime=RuntimeReferenceBridge(self.store)
    def approve(self,context="A",value="cursor"):
        self.runtime.receive("昨日の実験の続きをやって",context)
        self.runtime.receive(value,context)
        self.assertEqual(self.runtime.receive("はい",context)["status"],"resolved")
    def test_no_reference(self):
        self.assertEqual(self.bridge.lookup("A")["status"],"no_approved_reference")
    def test_no_unverified_inference(self):
        self.approve()
        self.assertEqual(self.bridge.lookup("A")["status"],"no_semantic_evidence")
        self.assertFalse(self.propositions.exists())
    def test_exact_match_readonly(self):
        self.propositions.write_text('{"subject":"cursor","value":"参照操作"}\n'
                                     '{"subject":"other","value":"無関係"}\n',encoding="utf8")
        self.approve()
        before=self.propositions.read_bytes()
        result=self.bridge.lookup("A")
        self.assertEqual(result["status"],"evidence_found")
        self.assertEqual(result["facts"],[{"subject":"cursor","value":"参照操作"}])
        self.assertIn("未検証",render_safe_semantic_result(result))
        self.assertEqual(before,self.propositions.read_bytes())
    def test_no_cross_context_leak(self):
        self.propositions.write_text('{"subject":"cursor","value":"参照操作"}\n',encoding="utf8")
        self.approve("A")
        self.assertEqual(self.bridge.lookup("B")["status"],"no_approved_reference")
    def test_invalidation(self):
        self.approve()
        self.runtime.invalidate("A")
        self.assertEqual(self.bridge.lookup("A")["status"],"no_approved_reference")
    def test_no_automatic_promote(self):
        self.approve()
        self.assertEqual(self.bridge.lookup("A")["facts"],[])
        self.assertFalse(self.propositions.exists())

if __name__=="__main__":unittest.main()

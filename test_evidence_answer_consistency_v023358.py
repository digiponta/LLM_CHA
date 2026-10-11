import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock
from runtime_reference_integration_v023352 import SessionReferenceStore,RuntimeReferenceBridge
from verified_reference_concept_v023356 import VerifiedConceptMapping
from evidence_answer_consistency_v023358 import supporting_evidence,ConsistencyReferenceBridge,render_consistency

def semantic_result(answer="量子力学は物理学の理論である。", evidence="量子力学は物理学の理論である。",
                    truth="TRUE", source="reviewed-record",action="ANSWER",state="KNOWN"):
    return NS(answer=answer,truth_state=truth,action=action,state=state,
              provenance=NS(source=source,evidence=evidence,origin="fixture"))

class ConsistencyTests(unittest.TestCase):
    def test_exact_evidence(self):
        self.assertEqual(supporting_evidence(semantic_result()),(True,"exact_statement_match"))
    def test_trailing_punctuation_normalization(self):
        self.assertTrue(supporting_evidence(semantic_result(answer="量子力学は物理学の理論である",
                                                           evidence="量子力学は物理学の理論である。"))[0])
    def test_unsupported_addition(self):
        s=semantic_result(answer="量子力学は物理学の理論であり、すべてを説明できる。")
        self.assertEqual(supporting_evidence(s)[1],"answer_not_exactly_supported")
    def test_subset_is_not_full_support(self):
        s=semantic_result(answer="量子力学",evidence="量子力学は物理学の理論である。")
        self.assertFalse(supporting_evidence(s)[0])
    def test_missing_evidence(self):
        self.assertEqual(supporting_evidence(semantic_result(evidence=""))[1],"missing_evidence_text")
    def test_unverified_even_if_matching(self):
        with tempfile.TemporaryDirectory() as td:
            ref=SessionReferenceStore(Path(td)/"ref.sqlite3")
            runtime=RuntimeReferenceBridge(ref)
            for text in ("昨日の実験の続きをやって","cursor","はい"):runtime.receive(text,"A")
            maps=VerifiedConceptMapping(Path(td)/"map.sqlite3")
            token=maps.propose("A","cursor","量子力学","experiment")
            self.assertTrue(maps.approve("A",token))
            semantic=Mock()
            semantic.resolve.return_value=semantic_result(truth="UNVERIFIED")
            bridge=ConsistencyReferenceBridge(ref,maps,semantic)
            denied=bridge.lookup("A")
            self.assertEqual(denied["status"],"consistency_blocked")
            self.assertEqual(denied["reason"],"truth_not_true")
            self.assertEqual(denied["answer"],"")
            semantic.resolve.return_value=semantic_result()
            accepted=bridge.lookup("A")
            self.assertEqual(accepted["status"],"consistent_evidence")
            self.assertIn("証拠と完全一致",render_consistency(accepted))
            semantic.resolve.return_value=semantic_result(answer="根拠にない追記")
            self.assertEqual(bridge.lookup("A")["reason"],"answer_not_exactly_supported")
            self.assertEqual(bridge.lookup("B")["status"],"no_approved_reference")
            semantic.resolve.assert_called_with("量子力学とは")
if __name__=="__main__":unittest.main()

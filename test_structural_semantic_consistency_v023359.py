import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock
from structural_semantic_consistency_v023359 import parse,structural_support,StructuralReferenceBridge
from runtime_reference_integration_v023352 import SessionReferenceStore,RuntimeReferenceBridge
from verified_reference_concept_v023356 import VerifiedConceptMapping

def fixture(evidence,answer,truth="TRUE"):
    return NS(answer=answer,truth_state=truth,state="KNOWN",action="ANSWER",
              provenance=NS(source="reviewed-record",evidence=evidence,origin="fixture"))

class StructuralTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse("AはBを含む。"),("includes","A","B",True,""))
        self.assertEqual(parse("条件XではAはBである。"),("is_a","A","B",True,"X"))
    def test_positive(self):
        for sentence in ("AはBを含む","GPUは並列計算に適する","条件XではAはBである"):
            with self.subTest(sentence=sentence):
                self.assertEqual(structural_support(fixture(sentence,sentence)),
                                 (True,"exact_structural_match"))
    def test_polarity(self):
        self.assertEqual(structural_support(fixture("GPUは並列計算に適する",
                                                    "GPUは並列計算に適さない"))[1],"polarity_mismatch")
    def test_reversed_arguments(self):
        self.assertEqual(structural_support(fixture("AはBを含む","BはAを含む"))[1],
                         "argument_mismatch")
    def test_dropped_condition(self):
        self.assertEqual(structural_support(fixture("条件XではAはBである","AはBである"))[1],
                         "condition_mismatch")
    def test_unsupported(self):
        self.assertEqual(structural_support(fixture("一般的な説明です","一般的な説明です"))[1],
                         "unsupported_grammar")
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as td:
            refs=SessionReferenceStore(Path(td)/"refs.db")
            runtime=RuntimeReferenceBridge(refs)
            for q in ("昨日の実験の続きをやって","cursor","はい"):runtime.receive(q,"A")
            mappings=VerifiedConceptMapping(Path(td)/"maps.db")
            token=mappings.propose("A","cursor","GPU","test");self.assertTrue(mappings.approve("A",token))
            sem=Mock();sem.resolve.return_value=fixture("GPUは並列計算に適する",
                                                        "GPUは並列計算に適する")
            bridge=StructuralReferenceBridge(refs,mappings,sem)
            self.assertEqual(bridge.lookup("A")["status"],"structural_match")
            sem.resolve.assert_called_once_with("GPUとは")
            sem.resolve.return_value=fixture("GPUは並列計算に適する","GPUは並列計算に適さない")
            r=bridge.lookup("A")
            self.assertEqual(r["status"],"structural_blocked")
            self.assertEqual(r["reason"],"polarity_mismatch")
            self.assertEqual(r["answer"],"")
            self.assertEqual(bridge.lookup("B")["status"],"no_approved_reference")

if __name__=="__main__":unittest.main()

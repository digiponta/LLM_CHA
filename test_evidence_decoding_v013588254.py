import unittest
from evidence_guided_decoding_v013588254 import select_extract,evaluate_decoding
from compare_evidence_decoding_v013588254 import benchmark

EVIDENCE={"status":"EVIDENCE","topic":"宇宙",
          "excerpt":"宇宙は非常に高温高密度の状態から始まり、膨張した。遠方の銀河は観測上遠ざかっている。",
          "url":"https://example.test/wiki","title":"宇宙"}

class EvidenceDecodingTests(unittest.TestCase):
    def test_extract_uses_exact_source_span(self):
        selected=select_extract(EVIDENCE)
        self.assertEqual(selected["status"],"EXTRACT_ACCEPTED")
        self.assertIn(selected["candidate"],EVIDENCE["excerpt"])
        self.assertEqual(selected["gate"],"ACCEPT_SOURCE_EXTRACT")

    def test_rejected_raw_uses_source_only(self):
        result=evaluate_decoding("1967年 APB THEAT",EVIDENCE)
        self.assertEqual(result["raw_gate"],"REJECT_NOT_ENTAILED")
        self.assertEqual(result["strategy"],"EXTRACTIVE_FALLBACK")
        self.assertIn("宇宙は非常に",result["answer"])
        self.assertNotIn("1967年",result["answer"])

    def test_no_evidence_remains_no_evidence(self):
        result=evaluate_decoding("怪しい文章",{"status":"NO_EVIDENCE"})
        self.assertEqual(result["strategy"],"ATTRIBUTED_FALLBACK")
        self.assertEqual(result["gate"],"NO_EXTRACT")

    def test_no_safe_sentence_does_not_invent(self):
        evidence={**EVIDENCE,"excerpt":"短い。"}
        selected=select_extract(evidence)
        self.assertEqual(selected["status"],"NO_SAFE_EXTRACT")
        self.assertIsNone(selected["candidate"])

    def test_benchmark_is_offline(self):
        report=benchmark(EVIDENCE,{"prefix":{"base":{"text":"1967年 APB THEAT"},
                                               "candidate":{"text":"1967年 Ablect"}}})
        self.assertEqual(report["cases"],2)
        self.assertFalse(report["production_changed"])
        self.assertTrue(all(c["strategy"]=="EXTRACTIVE_FALLBACK" for c in report["cases_detail"]))

if __name__=="__main__":
    unittest.main()

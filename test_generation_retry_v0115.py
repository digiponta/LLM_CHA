import tempfile
import unittest
from dataclasses import dataclass
from semantic_live_bridge_v0113 import process_turn
from semantic_dialogue_bridge_v0112 import DialogueBridge

@dataclass
class Output:
    text: str
    termination_reason: str

@dataclass
class Memory:
    hit: bool = True
    answer: str = "人類は影響を調べている。"
    provenance: str = "test:unverified"

class RetryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.bridge=DialogueBridge(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def test_retry_then_reconcile(self):
        calls=[]
        def retry(q,n):
            calls.append(n)
            return Output("人類は影響を調べているわけではない。","EOS")
        r=process_turn("人類とは",generate=lambda q:Output("人類は、","MAX_TOKENS"),
                       regenerate=retry,retrieve=lambda s:Memory(),bridge=self.bridge)
        self.assertEqual(r["action"],"ASK_USER")
        self.assertEqual(calls,[1])
        self.assertEqual(r["retry_history"][0]["status"],"VALID")
    def test_two_retries_bounded(self):
        calls=[]
        def retry(q,n):
            calls.append(n)
            return Output("壊れている。","MAX_TOKENS")
        r=process_turn("人類とは",generate=lambda q:Output("人類は、","MAX_TOKENS"),
                       regenerate=retry,retrieve=lambda s:Memory(),bridge=self.bridge)
        self.assertEqual(r["action"],"GENERATION_QUALITY_REVIEW")
        self.assertEqual(calls,[1,2])
        self.assertFalse(list(self.bridge.tickets.root.glob("*.json")))
    def test_no_retry_still_review(self):
        r=process_turn("人類とは",generate=lambda q:Output("人類は、","MAX_TOKENS"),
                       retrieve=lambda s:Memory(),bridge=self.bridge)
        self.assertEqual(r["action"],"GENERATION_QUALITY_REVIEW")
    def test_no_unnecessary_retry(self):
        def no_retry(q,n):
            raise AssertionError("retry not expected")
        r=process_turn("人類とは",generate=lambda q:Output("答えA","EOS"),
                       regenerate=no_retry,retrieve=lambda s:Memory(),bridge=self.bridge)
        self.assertEqual(r["action"],"ASK_USER")
if __name__=="__main__":
    unittest.main()

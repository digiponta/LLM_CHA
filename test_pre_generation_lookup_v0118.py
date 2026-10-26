import tempfile
import unittest
from dataclasses import dataclass
from semantic_subject_preferences_v0117 import SubjectPreferenceBridge
from semantic_live_bridge_v0113 import process_turn

@dataclass
class Memory:
    hit: bool=True
    answer: str="記憶側の命題"
    provenance: str="corpus:unverified"

class PrefetchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.bridge=SubjectPreferenceBridge(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def seed(self):
        x=process_turn("人類とは",generate=lambda q:"生成A",
                       retrieve=lambda s:Memory(),bridge=self.bridge)
        self.assertEqual(x["action"],"ASK_USER")
        self.bridge.review(x["ticket_id"],"prefer_b")
    def test_skips_gpu_generation_on_hit(self):
        self.seed()
        def fail(q):raise AssertionError("generation must be skipped")
        r=process_turn("人類とは",generate=fail,retrieve=lambda s:Memory(),
                       bridge=self.bridge,regenerate=lambda q,n:fail(q))
        self.assertEqual(r["action"],"USER_PREFERENCE")
        self.assertTrue(r["generation_skipped"])
        self.assertEqual(r["answer"],Memory().answer)
    def test_changed_memory_no_skip(self):
        self.seed()
        calls=[]
        def gen(q):calls.append(q);return "別の生成A"
        r=process_turn("人類とは",generate=gen,
                       retrieve=lambda s:Memory(answer="更新後の命題"),bridge=self.bridge)
        self.assertEqual(r["action"],"ASK_USER")
        self.assertEqual(calls,["人類とは"])
    def test_changed_subject_no_skip(self):
        self.seed()
        calls=[]
        def gen(q):calls.append(q);return "別の生成A"
        r=process_turn("人類とは",subject="生命",generate=gen,
                       retrieve=lambda s:Memory(),bridge=self.bridge)
        self.assertEqual(r["action"],"ASK_USER")
        self.assertEqual(len(calls),1)
    def test_changed_context_no_skip(self):
        self.seed()
        calls=[]
        def gen(q):calls.append(q);return "別の生成A"
        r=process_turn("人類とは",context="別の文脈",generate=gen,
                       retrieve=lambda s:Memory(),bridge=self.bridge)
        self.assertEqual(r["action"],"ASK_USER")
        self.assertEqual(len(calls),1)
    def test_miss_does_not_skip(self):
        self.seed()
        calls=[]
        def gen(q):calls.append(q);return "新しい生成A"
        r=process_turn("人類とは",generate=gen,retrieve=lambda s:Memory(hit=False,answer=""),
                       bridge=self.bridge)
        self.assertEqual(r["action"],"MEMORY_MISS")
        self.assertEqual(len(calls),1)
if __name__=="__main__":unittest.main()

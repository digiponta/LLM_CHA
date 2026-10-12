import tempfile
from pathlib import Path
import json
import unittest
from conversation_topic_adapter_v0233822 import ConversationTopicAdapter
from grounded_expansion_v0233826 import PropositionCursor
from proposition_truth_v0233827 import TruthOverlay
from context_recovery_v023343 import save,load

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name)
        self.corpus=base/"corpus.jsonl"
        self.saved=base/"state.json"
        record={"subject":"宇宙","statement":"宇宙は広大 / 宇宙は膨張","relation":"is",
        "source_text":"宇宙は広大","object_description":"","source":"test"}
        self.corpus.write_text(json.dumps(record,ensure_ascii=False)+"\n",encoding="utf-8")
        self.adapter=ConversationTopicAdapter()
        self.cursor=PropositionCursor()
        self.adapter.context.observe("宇宙")
        self.cursor.seen["宇宙"]={"宇宙は広大"}

    def test_roundtrip(self):
        save(self.saved,self.adapter.context,self.cursor,self.corpus)
        self.adapter.context.reset()
        self.cursor.reset()
        report=load(self.saved,self.adapter,self.cursor,self.corpus,lambda _:("TRUE",True),TruthOverlay())
        self.assertEqual(report.retained,1)
        self.assertEqual(self.cursor.seen["宇宙"],{"宇宙は広大"})
        self.assertEqual(self.adapter.context.active_topic,"宇宙")

    def test_reject_after_subject_false(self):
        save(self.saved,self.adapter.context,self.cursor,self.corpus)
        report=load(self.saved,self.adapter,self.cursor,self.corpus,lambda _:("FALSE",False),TruthOverlay())
        self.assertEqual(report.retained,0)
        self.assertEqual(self.adapter.context.topics,())

    def test_reset_followed_by_load(self):
        save(self.saved,self.adapter.context,self.cursor,self.corpus)
        self.adapter.context.reset()
        self.cursor.reset()
        self.assertEqual(self.cursor.seen,{})
        report=load(self.saved,self.adapter,self.cursor,self.corpus,lambda _:("TRUE",True),TruthOverlay())
        self.assertEqual(report.retained,1)

    def test_reject_changed_corpus(self):
        save(self.saved,self.adapter.context,self.cursor,self.corpus)
        s=self.corpus.read_text(encoding="utf-8").replace("宇宙は広大","宇宙は未知")
        self.corpus.write_text(s,encoding="utf-8")
        report=load(self.saved,self.adapter,self.cursor,self.corpus,lambda _:("TRUE",True),TruthOverlay())
        self.assertEqual(report.retained,0)

    def test_corrupt_snapshot_keeps_live_state(self):
        self.saved.write_text("{bad",encoding="utf-8")
        with self.assertRaises(ValueError):
            load(self.saved,self.adapter,self.cursor,self.corpus,lambda _:("TRUE",True),TruthOverlay())
        self.assertEqual(self.adapter.context.active_topic,"宇宙")
        self.assertIn("宇宙は広大",self.cursor.seen["宇宙"])

if __name__=="__main__":unittest.main()

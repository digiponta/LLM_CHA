"""v0.2.34.5 hardening checks for checkpoint save/recovery."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from context_recovery_v023343 import save, load
from conversation_topic_adapter_v0233822 import ConversationTopicAdapter
from grounded_expansion_v0233826 import PropositionCursor
from proposition_truth_v0233827 import TruthOverlay

class RecoveryHardeningTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.corpus=self.root/"corpus.jsonl"
        self.checkpoint=self.root/"checkpoint.json"
        with self.corpus.open("w",encoding="utf-8") as out:
            for subject,answer in (("宇宙","宇宙は広大 / 宇宙は膨張"),("GPU","GPUは並列処理を行う")):
                out.write(json.dumps({"subject":subject,"statement":answer,"relation":"is",
                    "source_text":answer,"object_description":"","source":"fixture"},ensure_ascii=False)+"\n")
        self.adapter=ConversationTopicAdapter()
        self.cursor=PropositionCursor()

    def test_two_topics_restore(self):
        self.adapter.context.observe("宇宙")
        self.adapter.context.observe("GPU")
        self.cursor.seen={"宇宙":{"宇宙は広大"},"GPU":{"GPUは並列処理を行う"}}
        self.assertEqual(save(self.checkpoint,self.adapter.context,self.cursor,self.corpus),2)
        self.adapter.context.reset()
        self.cursor.reset()
        r=load(self.checkpoint,self.adapter,self.cursor,self.corpus,lambda _:("TRUE",True),TruthOverlay())
        self.assertEqual((r.retained,r.rejected),(2,0))
        self.assertEqual(self.adapter.context.active_topic,"GPU")
        self.assertEqual(self.cursor.seen["宇宙"],{"宇宙は広大"})
        self.assertEqual(self.cursor.seen["GPU"],{"GPUは並列処理を行う"})

    def test_atomic_replacement_failure_preserves_previous_file(self):
        self.adapter.context.observe("宇宙")
        self.cursor.seen["宇宙"]={"宇宙は広大"}
        save(self.checkpoint,self.adapter.context,self.cursor,self.corpus)
        before=self.checkpoint.read_bytes()
        self.cursor.seen["宇宙"].add("宇宙は膨張")
        with patch("context_recovery_v023343.os.replace",side_effect=OSError("simulated failure")):
            with self.assertRaises(OSError):
                save(self.checkpoint,self.adapter.context,self.cursor,self.corpus)
        self.assertEqual(before,self.checkpoint.read_bytes())
        self.assertEqual(list(self.root.glob(".llm-cha-context-*.tmp")),[])

    def test_oversized_checkpoint_rejected_without_state_mutation(self):
        self.adapter.context.observe("GPU")
        self.cursor.seen["GPU"]={"GPUは並列処理を行う"}
        self.checkpoint.write_bytes(b"x"*131073)
        with self.assertRaises(ValueError):
            load(self.checkpoint,self.adapter,self.cursor,self.corpus,lambda _:("TRUE",True),TruthOverlay())
        self.assertEqual(self.adapter.context.active_topic,"GPU")
        self.assertEqual(self.cursor.seen["GPU"],{"GPUは並列処理を行う"})

    def test_corpus_revocation_between_save_and_load(self):
        self.adapter.context.observe("宇宙")
        self.cursor.seen["宇宙"]={"宇宙は広大"}
        save(self.checkpoint,self.adapter.context,self.cursor,self.corpus)
        self.assertEqual(load(self.checkpoint,self.adapter,self.cursor,self.corpus,
            lambda _:("OUTDATED",False),TruthOverlay()).retained,0)
        self.assertIsNone(self.adapter.context.active_topic)

if __name__=="__main__":
    unittest.main()

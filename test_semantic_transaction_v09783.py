import unittest
from types import SimpleNamespace
from semantic_dialogue_manager_v09772 import SemanticDialogueManager
from semantic_transaction_v09783 import process_semantic_transaction

class TransactionTests(unittest.TestCase):
    def test_preference_commit(self):
        m=SemanticDialogueManager(); t=SimpleNamespace(active_topic=None)
        r=process_semantic_transaction(m,t,"私は、スファレライトが好きです。")
        self.assertTrue(r.committed)
        self.assertEqual(m.journal.sequence,1)
    def test_switch_commit(self):
        m=SemanticDialogueManager();t=SimpleNamespace(active_topic="スファレライト")
        r=process_semantic_transaction(m,t,"ところでダイヤモンドは？")
        self.assertTrue(r.committed)
        self.assertEqual(t.active_topic,"ダイヤモンド")
    def test_exception_rollback(self):
        m=SemanticDialogueManager();t=SimpleNamespace(active_topic="スファレライト")
        original=m.handle
        def broken(q,topic=None):
            m.journal.record("switch_topic","ダイヤモンド",source_topic="bad",target_topic="ダイヤモンド")
            raise ValueError("test")
        m.handle=broken
        r=process_semantic_transaction(m,t,"test")
        self.assertFalse(r.committed)
        self.assertEqual(m.journal.sequence,0)
        self.assertEqual(t.active_topic,"スファレライト")
        m.handle=original
    def test_corrupt_update_rollback(self):
        m=SemanticDialogueManager();t=SimpleNamespace(active_topic="スファレライト")
        original=m.handle
        def broken(q,topic=None):
            m.journal.record("switch_topic","ダイヤモンド",source_topic="incorrect",target_topic="ダイヤモンド")
            t.active_topic="ダイヤモンド"
            return None
        m.handle=broken
        r=process_semantic_transaction(m,t,"test")
        self.assertFalse(r.committed)
        self.assertEqual(m.journal.sequence,0)
        self.assertEqual(t.active_topic,"スファレライト")
        m.handle=original
if __name__=="__main__":unittest.main()

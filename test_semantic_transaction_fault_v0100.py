"""v0.10.0 deterministic fault injection for session-only transactions."""
import unittest
from types import SimpleNamespace
from semantic_dialogue_manager_v09772 import SemanticDialogueManager
from semantic_transaction_v09783 import process_semantic_transaction

class FaultInjectionTests(unittest.TestCase):
    def setUp(self):
        self.manager=SemanticDialogueManager()
        self.topic=SimpleNamespace(active_topic="スファレライト")
        first=process_semantic_transaction(
            self.manager,self.topic,"私は、スファレライトが好きです。")
        self.assertTrue(first.committed)

    def inject(self, mutation, utterance="fault"):
        manager,ctx=self.manager,self.topic
        old=manager.handle
        before=(manager.journal.sequence,
                tuple(e.to_dict().items() for e in manager.journal.events),
                dict(manager.journal.focus),ctx.active_topic,
                manager.awaiting_clarification,manager.awaiting_new_reason)
        def faulty(text,topic=None):
            return mutation(manager,ctx)
        manager.handle=faulty
        try:
            result=process_semantic_transaction(manager,ctx,utterance)
        finally:
            manager.handle=old
        after=(manager.journal.sequence,
               tuple(e.to_dict().items() for e in manager.journal.events),
               dict(manager.journal.focus),ctx.active_topic,
               manager.awaiting_clarification,manager.awaiting_new_reason)
        self.assertFalse(result.committed)
        self.assertEqual(before,after)
        return result

    def test_bad_provenance(self):
        def corrupt(m,t):
            m.journal.record("switch_topic","ダイヤモンド",
                source_topic="ルビー",target_topic="ダイヤモンド")
            t.active_topic="ダイヤモンド"
        self.assertIn("ROLLBACK",self.inject(corrupt).status)

    def test_cross_topic_quality(self):
        def corrupt(m,t):
            m.journal.record("explain_preference","ダイヤモンド",
                updated_quality="sparkling")
        self.assertIn("ROLLBACK",self.inject(corrupt).status)

    def test_focus_corruption(self):
        def corrupt(m,t):
            m.journal.focus["スファレライト"]="fabricated"
        self.assertIn("ROLLBACK",self.inject(corrupt).status)

    def test_exception_after_mutation(self):
        def corrupt(m,t):
            m.awaiting_clarification="ダイヤモンド"
            m.journal.record("reject_previous","スファレライト")
            raise RuntimeError("injected")
        self.assertEqual(self.inject(corrupt).status,"ROLLBACK:EXCEPTION")

    def test_recovery_commit(self):
        self.test_bad_provenance()
        result=process_semantic_transaction(
            self.manager,self.topic,"ところでダイヤモンドは？")
        self.assertTrue(result.committed)
        self.assertEqual(self.topic.active_topic,"ダイヤモンド")
        self.assertEqual(self.manager.journal.sequence,2)

if __name__=="__main__":
    unittest.main()

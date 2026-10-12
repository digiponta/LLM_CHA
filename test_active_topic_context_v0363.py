import unittest
from active_topic_context_v0363 import ActiveTopicContext
from conversation_topic_adapter_v0233822 import ConversationTopicAdapter

class ActiveTopicTests(unittest.TestCase):
    def test_default_empty(self):
        self.assertEqual(ActiveTopicContext().topics,())
    def test_repeated_frequency_preferred(self):
        c=ActiveTopicContext(max_topics=2,ttl_turns=100)
        for t in ("A","A","B","C"):c.observe(t)
        self.assertIn("A",c.topics)
        self.assertNotIn("B",c.topics)
    def test_explicit_pin_survives(self):
        c=ActiveTopicContext(max_topics=2,pinned_topics=("A",))
        for t in ("A","B","C"):c.observe(t)
        self.assertIn("A",c.topics)
    def test_all_pinned_refusal(self):
        c=ActiveTopicContext(max_topics=2,pinned_topics=("A","B"))
        c.observe("A");c.observe("B")
        self.assertEqual(c.observe("C").status,"MISSING")
        self.assertEqual(c.admission_rejections,1)
        self.assertNotIn("C",c.topics)
    def test_rejected_does_not_switch_active(self):
        c=ActiveTopicContext(max_topics=1,pinned_topics=("A",))
        c.observe("A");c.observe("B")
        self.assertEqual(c.active_topic,"A")
    def test_reset(self):
        c=ActiveTopicContext(max_topics=2)
        for t in ("A","B","C"):c.observe(t)
        c.reset()
        self.assertEqual(c.metrics()["evictions"],0)
        self.assertEqual(c.topics,())
    def test_adapter_uses_existing_interface(self):
        a=ConversationTopicAdapter(ActiveTopicContext())
        self.assertEqual(a.process_user_turn("宇宙とは").action,"READY")
    def test_not_knowledge_mutation(self):
        c=ActiveTopicContext()
        self.assertNotIn("truth_state",c.metrics())
    def test_invalid_pins(self):
        with self.assertRaises(ValueError):
            ActiveTopicContext(max_topics=1,pinned_topics=("A","B"))
    def test_expired_topic_missing(self):
        c=ActiveTopicContext(max_topics=2,ttl_turns=1)
        c.observe("A")
        c.advance_turn();c.advance_turn()
        self.assertNotIn("A",c.topics)

if __name__=="__main__":
    unittest.main()

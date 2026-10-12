"""Regression tests for conversation-only multi-topic context."""
import unittest

from multi_topic_context_v0233821 import MultiTopicContext


class MultiTopicContextTests(unittest.TestCase):
    def test_switch_and_return(self):
        c = MultiTopicContext()
        c.observe("宇宙")
        c.advance_turn()
        c.observe("GPU")
        self.assertEqual(c.resolve().topic, "GPU")
        self.assertEqual(c.resolve(explicit_topic="宇宙").topic, "宇宙")
        c.observe("宇宙")
        self.assertEqual(c.resolve().topic, "宇宙")

    def test_ambiguous_reference_fails_closed(self):
        c = MultiTopicContext()
        c.observe("宇宙")
        c.observe("GPU")
        r = c.resolve(ambiguous_reference=True)
        self.assertEqual(r.status, "AMBIGUOUS")
        self.assertEqual(set(r.candidates), {"宇宙", "GPU"})
        self.assertIsNone(r.topic)

    def test_single_topic_reference(self):
        c = MultiTopicContext()
        c.observe("宇宙")
        self.assertEqual(c.resolve(ambiguous_reference=True).topic, "宇宙")

    def test_expiry(self):
        c = MultiTopicContext(ttl_turns=2)
        c.observe("宇宙")
        c.advance_turn()
        c.advance_turn()
        self.assertEqual(c.resolve().status, "RESOLVED")
        c.advance_turn()
        self.assertEqual(c.resolve().status, "MISSING")

    def test_eviction(self):
        c = MultiTopicContext(max_topics=2)
        c.observe("宇宙")
        c.advance_turn()
        c.observe("GPU")
        c.advance_turn()
        c.observe("数学")
        self.assertEqual(set(c.topics), {"GPU", "数学"})

    def test_reset_is_context_only(self):
        knowledge = {"宇宙": {"truth_state": "UNVERIFIED"}}
        c = MultiTopicContext()
        c.observe("宇宙")
        self.assertEqual(c.handle_command("/reset").status, "RESET")
        self.assertEqual(c.topics, ())
        self.assertEqual(knowledge["宇宙"]["truth_state"], "UNVERIFIED")

    def test_commands_do_not_become_topics(self):
        c = MultiTopicContext()
        self.assertEqual(c.observe("/sleep").status, "MISSING")
        self.assertIsNone(c.handle_command("/sleep"))
        self.assertEqual(c.topics, ())

    def test_missing_explicit_topic_does_not_fallback(self):
        c = MultiTopicContext()
        c.observe("GPU")
        self.assertEqual(c.resolve(explicit_topic="量子力学").status, "MISSING")

    def test_invalid_configuration(self):
        with self.assertRaises(ValueError):
            MultiTopicContext(ttl_turns=0)


if __name__ == "__main__":
    unittest.main()

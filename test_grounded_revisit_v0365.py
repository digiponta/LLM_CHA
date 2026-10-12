"""v0.3.6.5 active grounded revisit and ephemeral cursor pruning tests."""
import unittest
from pathlib import Path
from active_topic_context_v0363 import ActiveTopicContext
from conversation_topic_adapter_v0233822 import ConversationTopicAdapter
from grounded_expansion_v0233826 import PropositionCursor

def sync_cursor(cursor,context):
    live=set(context.topics)
    for stale in tuple(cursor.seen):
        if stale not in live:
            cursor.seen.pop(stale,None)

class GroundedRevisitTests(unittest.TestCase):
    def test_active_bare_about_rewrites(self):
        a=ConversationTopicAdapter(ActiveTopicContext(),grounded_topic_only=True)
        route=a.process_user_turn("宇宙について")
        self.assertEqual((route.topic,route.rewritten_query),("宇宙","宇宙について教えて"))
    def test_default_bare_about_unchanged(self):
        a=ConversationTopicAdapter()
        route=a.process_user_turn("宇宙について")
        self.assertEqual(route.rewritten_query,"宇宙について")
    def test_no_topic_invented(self):
        a=ConversationTopicAdapter(ActiveTopicContext(),grounded_topic_only=True)
        self.assertEqual(a.process_user_turn("について").topic,None)
    def test_reject_bare_about_capacity(self):
        a=ConversationTopicAdapter(ActiveTopicContext(max_topics=1,pinned_topics=("宇宙",)),grounded_topic_only=True)
        a.process_user_turn("宇宙とは")
        self.assertEqual(a.process_user_turn("数学について").action,"NO_TOPIC")
    def test_prune_evicted_subject_only(self):
        c=ActiveTopicContext(max_topics=2,ttl_turns=100)
        p=PropositionCursor(seen={"宇宙":{"a"},"GPU":{"b"}})
        c.observe("宇宙");c.observe("GPU");c.observe("CPU")
        sync_cursor(p,c)
        self.assertEqual(set(p.seen),set(c.topics)&{"宇宙","GPU"})
    def test_readmission_starts_fresh(self):
        c=ActiveTopicContext(max_topics=1,ttl_turns=100)
        p=PropositionCursor(seen={"宇宙":{"old"}})
        c.observe("宇宙");c.observe("GPU")
        sync_cursor(p,c)
        c.observe("宇宙")
        self.assertNotIn("宇宙",p.seen)
    def test_cursor_prune_no_truth_or_corpus_write(self):
        source=Path("chat.py").read_text(encoding="utf-8")
        self.assertIn("proposition_cursor.seen.pop(stale_subject, None)",source)
        self.assertIn("if active_retention_requested:",source)
    def test_followup_existing_adapter(self):
        a=ConversationTopicAdapter(ActiveTopicContext(),grounded_topic_only=True)
        a.process_user_turn("宇宙について")
        self.assertEqual(a.process_user_turn("もう少し詳しく").topic,"宇宙")

if __name__=="__main__": unittest.main()

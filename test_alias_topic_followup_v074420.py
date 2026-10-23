import ast
import unittest
from pathlib import Path

class AliasTopicFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(cls.source)

    def test_alias_activates_wiki_context(self):
        start=self.source.index('normalized_wiki = cha_unknown_wiki_fallback(')
        end=self.source.index('relation = relation_context.observe(raw_user_text)',start)
        block=self.source[start:end]
        self.assertIn('normalized_wiki.get("wiki_context")',block)
        self.assertIn('cha_wiki_conversation.offer(normalized_wiki["wiki_context"])',block)
        self.assertLess(block.index('cha_wiki_conversation.offer(normalized_wiki["wiki_context"])'),block.index('print("AI> " + normalized_wiki["answer"])'))

    def test_followup_reads_active_context(self):
        self.assertIn('raw_user_text,cha_wiki_conversation.current',self.source)
        self.assertIn('cha_wiki_evidence_session.next(',self.source)

    def test_truth_gate_unchanged(self):
        start=self.source.index('normalized_wiki = cha_unknown_wiki_fallback(')
        end=self.source.index('relation = relation_context.observe(raw_user_text)',start)
        block=self.source[start:end]
        self.assertIn("truth_state=EXTERNAL_UNVERIFIED",block)
        self.assertIn("train_ready=False, auto_promote=False",block)

if __name__=="__main__":
    unittest.main()

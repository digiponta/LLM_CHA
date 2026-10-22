import ast
import unittest
from pathlib import Path
from multi_topic_evidence_v0639 import TopicEvidenceContext

class MultiTopicEvidenceTests(unittest.TestCase):
    def test_restore_previous_topic(self):
        c=TopicEvidenceContext()
        c.remember("スターバックス","","wiki-starbucks")
        c.remember("トヨタ","本社は豊田市","wiki-toyota")
        r=c.restore("スターバックスに戻って")
        self.assertEqual(r["status"],"RESTORED")
        self.assertEqual(c.current()["source"],"wiki-starbucks")
        self.assertEqual(c.current()["truth_state"],"EXTERNAL_UNVERIFIED")
    def test_missing_topic_does_not_change_active(self):
        c=TopicEvidenceContext()
        c.remember("トヨタ","本文","url")
        self.assertEqual(c.restore("スターバックスに戻って")["status"],"NOT_FOUND")
        self.assertEqual(c.active,"トヨタ")
    def test_eviction(self):
        c=TopicEvidenceContext(max_topics=2)
        for x in ("A","B","C"):c.remember(x,"",x)
        self.assertNotIn("A",c.items)
        self.assertEqual(len(c.items),2)
    def test_reset(self):
        c=TopicEvidenceContext()
        c.remember("トヨタ")
        c.reset()
        self.assertIsNone(c.current())
    def test_non_restore_input(self):
        self.assertIsNone(TopicEvidenceContext().restore("メニューは"))
    def test_chat_wiring(self):
        s=Path("chat.py").read_text(encoding="utf-8")
        ast.parse(s)
        self.assertIn("topic_evidence.restore(user_text)",s)
        self.assertIn("route=TOPIC_RESTORE",s)
        self.assertIn("topic_evidence.remember(active_evidence_topic",s)
if __name__=="__main__":unittest.main()

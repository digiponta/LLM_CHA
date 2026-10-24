import unittest
from wiki_persona_multiturn_v0520 import WikiConversation

W={"status":"FOUND","title":"量子ビット","url":"https://ja.wikipedia.org/wiki/量子ビット",
   "extract":"概要。"}

class FollowupExhaustionTests(unittest.TestCase):
    def test_repeated_evidence_insufficiency_changes_message(self):
        c=WikiConversation()
        c.offer(W)
        a=c.respond("もっと詳しく")
        b=c.respond("もっと詳しく")
        self.assertEqual(a["route"],"WIKIPEDIA_EVIDENCE_INSUFFICIENT")
        self.assertEqual(b["route"],"WIKIPEDIA_EVIDENCE_INSUFFICIENT")
        self.assertNotEqual(a["answer"],b["answer"])
        self.assertIn("観点",b["answer"])
        self.assertFalse(b["train_ready"])
    def test_topic_reset(self):
        c=WikiConversation()
        c.offer(W)
        c.respond("もっと詳しく")
        c.respond("もっと詳しく")
        c.offer(W)
        self.assertIn("根拠がない",c.respond("もっと詳しく")["answer"])

if __name__=="__main__":unittest.main()

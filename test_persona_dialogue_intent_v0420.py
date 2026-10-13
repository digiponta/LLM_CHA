import unittest
from pathlib import Path
from persona_dialogue_intent_v0420 import classify_dialogue_intent as classify

class DialogueIntentTests(unittest.TestCase):
    def test_incomplete(self):
        for q in ("貴方は","あなたは","あなたの","私は","それは","貴方って"):
            with self.subTest(q=q):
                r=classify(q)
                self.assertEqual(r["intent"],"INCOMPLETE")
                self.assertEqual(r["answer"],"続きを聞かせて。")
    def test_identity(self):
        self.assertEqual(classify("貴方は誰")["intent"],"IDENTITY")
        self.assertEqual(classify("あなたは誰ですか")["action"],"IDENTITY_ROUTE")
    def test_knowledge(self):
        for q in ("化学とは","CPUとは","哲学について教えて"):
            with self.subTest(q=q):
                self.assertEqual(classify(q)["intent"],"KNOWLEDGE")
                self.assertEqual(classify(q)["action"],"PASS_THROUGH")
    def test_conversation(self):
        self.assertEqual(classify("今日は何をしていたの")["intent"],"CONVERSATION")
        self.assertEqual(classify("最近どう")["action"],"PASS_THROUGH")
    def test_no_false_fragment(self):
        for q in ("貴方は何をしているの","貴方は誰","あなたの趣味は何","私は数学を学ぶ","あなたの名前は"):
            self.assertNotEqual(classify(q)["intent"],"INCOMPLETE")
    def test_commands(self):
        self.assertEqual(classify("/truth CPU")["action"],"PASS_THROUGH")
    def test_readonly(self):
        r=classify("貴方は")
        self.assertFalse(r["truth_gate_modified"])
        self.assertEqual(r["semantic_memory_writes"],0)
        self.assertFalse(r["training_enabled"])
    def test_chat_hook_priority(self):
        s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
        self.assertIn('dialogue_intent = classify_dialogue_intent(raw_user_text)',s)
        self.assertLess(s.index('dialogue_intent = classify_dialogue_intent(raw_user_text)'),s.index('identity_reply = identity_answer(raw_user_text)'))
        self.assertLess(s.index('dialogue_intent = classify_dialogue_intent(raw_user_text)'),s.index('if command.startswith("/wiki "):'))
if __name__=="__main__":unittest.main()

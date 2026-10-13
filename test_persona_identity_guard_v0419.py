import unittest
from pathlib import Path
from persona_identity_guard_v0419 import identity_answer
from persona_answer_relevance_v0419 import diagnose_relevance

class PersonaIdentityGuardTests(unittest.TestCase):
    def test_exact_identity_variants(self):
        for q in ("貴方は誰","あなたは誰ですか","君は誰？","お名前は","名前を教えて","自己紹介して","貴方は何者"):
            with self.subTest(question=q):
                self.assertEqual(identity_answer(q),"長門有希。")
    def test_fragment_not_identity(self):
        for q in ("貴方は","貴方は何をしている","哲学とは","誰が書いた","彼女は誰","/teach 貴方は誰","貴方は誰と話す"):
            with self.subTest(question=q):
                self.assertIsNone(identity_answer(q))
    def test_only_nagato_persona(self):
        self.assertIsNone(identity_answer("貴方は誰",persona_id="other"))
    def test_readonly_relevance(self):
        r=diagnose_relevance("貴方は誰","連載後半は対話。 |読切・",agreement=0.032,semantic_agreement=0.881)
        self.assertTrue(r["relevance_warning"])
        self.assertFalse(r["identity_matched"])
        self.assertFalse(r["modifies_truth_gate"])
        self.assertFalse(r["writes_memory"])
    def test_low_agreement_independent_of_semantic(self):
        r=diagnose_relevance("近況を教えて","話したい",agreement=0.032,semantic_agreement=0.881)
        self.assertTrue(r["low_probe_agreement"])
        self.assertTrue(r["relevance_warning"])
    def test_clean_diagnostic(self):
        r=diagnose_relevance("貴方は誰","長門有希。",agreement=1,semantic_agreement=1)
        self.assertFalse(r["relevance_warning"])
    def test_bad_score(self):
        with self.assertRaises(ValueError):diagnose_relevance("q","a",agreement=-1,semantic_agreement=0.8)
    def test_chat_hook(self):
        s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
        self.assertIn("identity_reply = identity_answer(raw_user_text)",s)
        self.assertIn('print(f"persona> {identity_reply}")',s)
        self.assertIn("diagnose_relevance(",s)
        self.assertLess(s.index("identity_reply = identity_answer(raw_user_text)"),s.index('if command.startswith("/wiki "):'))
if __name__=="__main__":unittest.main()

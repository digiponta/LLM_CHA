import unittest
from semantic_action_subject_v09749 import parse,check

class SubjectAwareTests(unittest.TestCase):
    def test_speaker_same(self):
        r=check("私は本を買った","私は本を借りた。")
        self.assertEqual(r.decision,"REPAIR")
        self.assertIn("買った",r.selected)
    def test_other_person_same(self):
        r=check("友人は本を買った","友人は本を借りた。")
        self.assertEqual(r.decision,"REPAIR")
        self.assertEqual(r.input_fact["subject"],"FRIEND")
    def test_subject_mismatch(self):
        r=check("私は本を買った","友人は本を借りた。")
        self.assertEqual(r.decision,"REVIEW")
        self.assertEqual(r.selected,r.original)
    def test_implicit_subject_review(self):
        r=check("友人は本を買った","本を借りた。")
        self.assertEqual(r.decision,"REVIEW")
    def test_negation(self):
        r=check("私は本を買わなかった","私は本を買った。")
        self.assertEqual(r.decision,"REPAIR")
        self.assertIn("買わなかった",r.selected)
    def test_clipboard_without_subject(self):
        r=check("バゲットサンドを食べた","そう、バゲットサンドを飲んだのね。")
        self.assertEqual(r.decision,"REPAIR")
    def test_quote_review(self):
        self.assertEqual(check("「私は本を買った」","私は本を借りた。").decision,"REVIEW")
    def test_multiple_clauses(self):
        self.assertEqual(check("私は本を買った。そして読んだ。","私は本を借りた。").decision,"REVIEW")
    def test_unspecified_is_not_forced_user(self):
        a=parse("本を買った","USER_UTTERANCE")
        self.assertEqual(a.subject,"UNSPECIFIED")
    def test_no_promotion(self):
        r=check("私は本を買った","私は本を借りた。")
        self.assertFalse(r.train_ready or r.auto_promote or r.persisted)
if __name__=="__main__":unittest.main()

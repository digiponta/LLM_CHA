import unittest
from topic_suggestion_followup_v093 import (options_for_suggestion,resolve_followup,explain_followup)
class TopicFollowupTests(unittest.TestCase):
    def setUp(self):
        self.options=["粒子と波動","エネルギー準位","零点エネルギー"]
        self.corpus="量子力学的に考えると、１つの粒子の波動は宇宙全体に広がっている。"
    def test_first_topic(self):
        r=explain_followup("最初の話題について教えて",self.options,self.corpus)
        self.assertEqual(r["route"],"TOPIC_FOLLOWUP_CORPUS")
        self.assertEqual(r["topic"],"粒子と波動")
    def test_second_topic(self):
        self.assertEqual(resolve_followup("2番目の話題を教えて",self.options)["index"],1)
    def test_last_topic(self):
        self.assertEqual(resolve_followup("最後の話題について",self.options)["index"],2)
    def test_unrelated_question(self):
        self.assertIsNone(explain_followup("数学とは",self.options,self.corpus))
    def test_no_options(self):
        self.assertIsNone(explain_followup("最初の話題について",[],self.corpus))
    def test_out_of_range(self):
        self.assertEqual(explain_followup("3番目の話題",["粒子と波動"],self.corpus)["route"],
                         "TOPIC_FOLLOWUP_CLARIFICATION")
    def test_absent_corpus_is_not_invented(self):
        self.assertEqual(explain_followup("最初の話題について",self.options,"")["route"],
                         "TOPIC_FOLLOWUP_NO_EVIDENCE")
    def test_extract_options_from_displayed_answer(self):
        s={"route":"TOPIC_SUGGESTION_CORPUS","answer":
           "量子力学に関係する話題なら、粒子と波動、エネルギー準位、零点エネルギーがある。どれについて話す？"}
        self.assertEqual(options_for_suggestion(s),self.options)
if __name__=="__main__":unittest.main()

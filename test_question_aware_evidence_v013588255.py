import unittest
from question_aware_evidence_v013588255 import classify,select_for_question,answer_or_abstain

E={"status":"EVIDENCE","topic":"ビッグバン","url":"https://example.test/wiki",
   "excerpt":"ビッグバンとは、宇宙の初期に起きた大規模な膨張である。観測により宇宙膨張の証拠が確認された。その時刻は今から138億年前と計算されている。"}

class QuestionAwareTests(unittest.TestCase):
 def test_attribute(self):
  self.assertEqual(classify("ビッグバンはいつ起きたのか"),"time")
  self.assertEqual(classify("宇宙はなぜ膨張するのか"),"cause")
 def test_time(self):
  r=select_for_question("ビッグバンはいつ起きたのか",E)
  self.assertEqual(r["status"],"EXTRACT_ACCEPTED")
  self.assertIn("138億年前",r["sentence"])
 def test_definition(self):
  r=select_for_question("ビッグバンとは",E)
  self.assertEqual(r["status"],"EXTRACT_ACCEPTED")
  self.assertIn("ビッグバンとは",r["sentence"])
 def test_cause_abstain(self):
  e={**E,"excerpt":"遠方の銀河が観測される。膨張している宇宙がある。"}
  r=answer_or_abstain("宇宙はなぜ膨張するのか",e)
  self.assertEqual(r["status"],"ABSTAIN_NO_MATCHING_ATTRIBUTE")
 def test_unknown_abstain(self):
  self.assertEqual(select_for_question("もっと詳しく",E)["status"],"ABSTAIN_UNSUPPORTED_QUESTION")
 def test_no_evidence(self):
  self.assertEqual(select_for_question("ビッグバンとは",{"status":"NO_EVIDENCE"})["status"],"ABSTAIN_NO_EVIDENCE")

if __name__=="__main__":unittest.main()

import unittest
from evaluate_rpc_context_v01338 import split_history,context_variants,char_similarity,summary

class ContextDiagnosticsTests(unittest.TestCase):
    def rows(self):
        return [
          {"dialogue_id":1,"user":"相手: 料理\n自分: 好き\n相手: ラーメンは？","assistant":"好きです","utterance_id":2},
          {"dialogue_id":2,"user":"相手: 旅行\n自分: 山\n相手: 車ですか？","assistant":"電車です","utterance_id":2}]
    def test_last_turn(self):
        prior,last=split_history(self.rows()[0]["user"])
        self.assertEqual(last,"相手: ラーメンは？")
        self.assertEqual(len(prior),2)
    def test_shuffled_preserves_last_and_changes_prior(self):
        rows=self.rows();v=context_variants(rows)
        self.assertEqual(v[0]["LAST_TURN"],"相手: ラーメンは？")
        self.assertTrue(v[0]["SHUFFLED_CONTEXT"].startswith("相手: 旅行"))
        self.assertTrue(v[0]["SHUFFLED_CONTEXT"].endswith("相手: ラーメンは？"))
        self.assertNotEqual(v[0]["FULL_CONTEXT"],v[0]["SHUFFLED_CONTEXT"])
    def test_rejects_wrong_last_speaker(self):
        with self.assertRaises(ValueError):split_history("自分: こんにちは")
    def test_similarity(self):
        self.assertAlmostEqual(char_similarity("abcdef","abcdef"),1.0)
        self.assertAlmostEqual(char_similarity("abcdef","uvwxyz"),0.0)
    def test_summary(self):
        row={"tokens":4,"repetition":0,"generic_reply":True,"text":"そうですね","reference_char3_jaccard":0.2}
        self.assertEqual(summary([row])["generic_reply"],1)
if __name__=="__main__":unittest.main()

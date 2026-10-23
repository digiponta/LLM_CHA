import unittest
from prepare_approved_paraphrase_v0743 import prepare
from evaluate_approved_paraphrase_v0743 import probes

class ParaphraseTests(unittest.TestCase):
    def test_isolated_holdout(self):
        rows=[{"id":"id1","user":"真空管の原文記述は",
               "question":"原文証拠：真空管 #abcdef123456",
               "assistant":"真空管の説明。","source_id":"src"}]
        data=prepare(rows)
        self.assertEqual((len(data["train"]),len(data["holdout"])),(3,2))
        self.assertFalse(set(r["question"] for r in data["train"]) &
                         set(r["question"] for r in data["holdout"]))
        self.assertEqual({r["approved_id"] for r in data["train"]+data["holdout"]},{"id1"})
    def test_no_unqualified_rows(self):
        self.assertEqual(prepare([{"question":"普通のQA","id":"1"}]),
                         {"train":[],"holdout":[]})
    def test_incomplete_source_record_rejected(self):
        with self.assertRaisesRegex(ValueError,"incomplete Approved"):
            prepare([{"question":"原文証拠：真空管 #abcdef123456","id":"1"}])
    def test_non_source_without_question(self):
        self.assertEqual(prepare([{"id":"1"}]),{"train":[],"holdout":[]})
    def test_probe_groups(self):
        rows=[{"id":"x","user":"宇宙の原文記述は",
               "question":"原文証拠：宇宙 #abcdefabcdef",
               "assistant":"宇宙。","source_id":"src"}]
        p=probes(prepare(rows))
        self.assertEqual([v["group"] for v in p].count("holdout"),2)
if __name__=="__main__":unittest.main()

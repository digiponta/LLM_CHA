import unittest
from reconstruct_dialogue_qa_v042847 import build_json, build_text, parse_json

class BoundaryQATests(unittest.TestCase):
    def test_unstructured_text_rejected(self):
        r = build_text("食事管理していますか。\n全く違う話です。")
        self.assertEqual(r["candidate_count"], 0)
        self.assertTrue(r["source_diagnostics"]["boundary_evidence_missing"])

    def test_role_labels_without_boundary_rejected(self):
        r = build_text("ユーザー: 元気ですか？\nアシスタント: はい、元気です。")
        self.assertEqual(r["candidate_count"], 0)

    def test_explicit_text_boundary(self):
        r = build_text("---\nユーザー: 元気ですか？\nアシスタント: はい、元気です。")
        self.assertEqual(r["candidate_count"], 1)

    def test_no_cross_boundary_pair(self):
        r = build_text("---\nユーザー: 元気ですか？\n---\nアシスタント: はい。")
        self.assertEqual(r["candidate_count"], 0)

    def test_json_explicit_dialogues(self):
        data = {"dialogues":[{"id":"d1","turns":[{"role":"user","text":"元気ですか？"},
               {"role":"assistant","text":"元気です。"}]}]}
        r = build_json(data)
        self.assertEqual(r["candidate_count"], 1)
        self.assertFalse(r["train_ready"])
        self.assertEqual(r["candidates"][0]["review_status"], "pending")

    def test_wrong_role_order(self):
        data = {"dialogues":[{"id":"d1","turns":[{"role":"user","text":"元気ですか？"},
              {"role":"user","text":"聞こえますか？"}]}]}
        r = build_json(data)
        self.assertEqual(r["candidate_count"], 0)

    def test_duplicate_dialogue_id_rejected(self):
        data = {"dialogues":[{"id":"d1","turns":[]},{"id":"d1","turns":[]}]}
        with self.assertRaises(ValueError): build_json(data)

    def test_question_answer_not_accepted(self):
        data = {"dialogues":[{"id":"d1","turns":[{"role":"user","text":"元気ですか？"},
                {"role":"assistant","text":"元気ですか？"}]}]}
        self.assertEqual(build_json(data)["candidate_count"], 0)

    def test_not_train_eligible(self):
        r = build_text("---\nユーザー: 元気ですか？\nアシスタント: はい、元気です。")
        self.assertFalse(r["candidates"][0]["train_eligible"])
        self.assertFalse(r["runtime_modified"])

if __name__ == "__main__":
    unittest.main()

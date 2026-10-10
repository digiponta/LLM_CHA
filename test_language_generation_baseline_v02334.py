import unittest
from unittest.mock import Mock
from evaluate_language_generation_baseline_v02334 import TASKS,verify_tasks,evaluate
class LanguageBaselineTests(unittest.TestCase):
    def test_categories(self):
        self.assertTrue(verify_tasks())
        self.assertEqual(set(t["ability"] for t in TASKS),set(("continuation","explanation","procedure","context","conditioning","retention")))
    def test_dedup(self):
        with self.assertRaises(ValueError):verify_tasks(TASKS+[TASKS[0]])
    def test_no_external_semantics(self):
        m=Mock()
        m.generate.return_value={"text":"sample","generated_tokens":1,"elapsed_seconds":.01}
        out=evaluate({"base":m},TASKS[:3],12)
        self.assertEqual(len(out),3)
        for call in m.generate.call_args_list:
            self.assertEqual(call.kwargs["temperature"],0)
            self.assertEqual(call.kwargs["max_new_tokens"],12)
            self.assertFalse("話題:" in call.args[0] or "目的:" in call.args[0])
    def test_manual_grade_unfilled(self):
        m=Mock()
        m.generate.return_value={"text":"a"}
        records=evaluate({"base":m},TASKS[:1])
        self.assertIsNone(records[0]["manual_review"]["base"]["task_success"])
if __name__=="__main__":unittest.main()

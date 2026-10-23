import unittest
from diagnose_nagato_length_v0729 import analyze_records,common_prefix
class NagatoLengthTests(unittest.TestCase):
    def test_prefix(self):
        self.assertEqual(common_prefix([1,2,3],[1,2,4]),2)
    def test_long_budget(self):
        rows=[{"id":"x","source_id":"data-nagato.txt:line=1",
                "question":"Q","answer":"abcdefghij"}]
        r=analyze_records(rows,lambda s:list(s),
            lambda q:"abc",max_new_tokens=3,context_length=30)
        self.assertEqual(r["too_long_for_budget"],1)
        self.assertEqual(r["cases"][0]["prefix_tokens"],3)
        self.assertEqual(r["exact"],0)
    def test_no_limit(self):
        rows=[{"id":"x","source_id":"source","question":"Q","answer":"ok"}]
        r=analyze_records(rows,lambda s:list(s),lambda q:"ok",
            max_new_tokens=32,context_length=512)
        self.assertEqual(r["exact"],1)
    def test_context_overflow(self):
        rows=[{"id":"x","source_id":"source","question":"Q","answer":"x"*100}]
        r=analyze_records(rows,lambda s:list(s),lambda q:"x"*3,
            context_length=50)
        self.assertEqual(r["too_long_for_context"],1)
if __name__=="__main__":unittest.main()

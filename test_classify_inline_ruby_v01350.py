import unittest
from classify_inline_ruby_v01350 import classify,analyze,DEFAULT_READINGS
class Tests(unittest.TestCase):
    def test_confirmed(self):
        self.assertEqual(classify("掌てのひら",DEFAULT_READINGS)[0],"CONFIRMED_RUBY")
    def test_normal(self):
        self.assertEqual(classify("見ると",DEFAULT_READINGS)[0],"NORMAL_TEXT")
    def test_ambiguous(self):
        self.assertEqual(classify("大きな声",DEFAULT_READINGS)[0],"AMBIGUOUS")
    def test_prefix_ambiguous(self):
        self.assertEqual(classify("大おおいに",DEFAULT_READINGS)[0],"AMBIGUOUS")
    def test_no_edits(self):
        lines=["掌てのひらに載せた。","見ると云って帰った。"]
        snapshot=list(lines)
        result=analyze(lines,DEFAULT_READINGS)
        self.assertEqual(lines,snapshot)
        self.assertEqual(result["automatic_replacements"],0)
        self.assertFalse(result["training_approved"])
if __name__=="__main__":unittest.main()

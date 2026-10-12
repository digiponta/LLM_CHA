import unittest
from grounded_expansion_v0233826 import PropositionCursor

class PropositionCursorTests(unittest.TestCase):
    def test_sequence(self):
        c = PropositionCursor()
        self.assertEqual(c.next("宇宙","A / B / C")[0],"A")
        self.assertEqual(c.next("宇宙","A / B / C")[0],"B")
        self.assertEqual(c.next("宇宙","A / B / C")[0],"C")
        self.assertIsNone(c.next("宇宙","A / B / C")[0])

    def test_topic_independence(self):
        c = PropositionCursor()
        c.next("A","one / two")
        self.assertEqual(c.next("B","one / two")[0],"one")
        self.assertEqual(c.next("A","one / two")[0],"two")

    def test_reset(self):
        c = PropositionCursor()
        c.next("宇宙","a / b")
        c.reset()
        self.assertEqual(c.next("宇宙","a / b")[0],"a")

    def test_duplicates(self):
        c=PropositionCursor()
        self.assertEqual(c.split("A / A / B"),["A","B"])

    def test_no_sentence_split(self):
        c=PropositionCursor()
        self.assertEqual(c.split("A。B。"),["A。B。"])

    def test_no_content(self):
        c=PropositionCursor()
        self.assertEqual(c.next("宇宙","")[0],None)

    def test_source_unchanged(self):
        c=PropositionCursor()
        text="A / B"
        c.next("x",text)
        self.assertEqual(text,"A / B")

if __name__=="__main__":
    unittest.main()

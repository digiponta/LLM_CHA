import unittest
from clipboard_browser_reader_v0975 import read_clipboard,MAX_CHARS

class ClipboardReaderTests(unittest.TestCase):
    def test_clipboard_text(self):
        r=read_clipboard(lambda:"スタバの紹介を読みました")
        self.assertEqual(r["route"],"CLIPBOARD_CONTEXT_READ")
        self.assertFalse(r["train_ready"])
        self.assertFalse(r["persisted"])
        self.assertIsNone(r["source_url"])
    def test_empty(self):
        with self.assertRaises(ValueError):
            read_clipboard(lambda:" ")
    def test_limit(self):
        r=read_clipboard(lambda:"A"*(MAX_CHARS+100))
        self.assertEqual(r["characters"],MAX_CHARS)
        self.assertTrue(r["truncated"])
if __name__=="__main__":unittest.main()

import unittest
from gui_command_capture_v074411 import CommandOutputCapture

class CaptureTests(unittest.TestCase):
    def test_multiline_status(self):
        p=CommandOutputCapture()
        p.start()
        found=None
        for ch in "Status\ntrained=3\npending=0\nYou> ":
            x=p.feed(ch)
            if x is not None:found=x
        self.assertEqual(found,"Status\ntrained=3\npending=0")
    def test_inactive(self):
        p=CommandOutputCapture()
        self.assertIsNone(p.feed("x"))
    def test_reset(self):
        p=CommandOutputCapture()
        p.start()
        p.feed("old")
        p.start()
        self.assertEqual("".join(filter(None,(p.feed(c) or "" for c in "new\nYou> "))),"new")
    def test_truncate(self):
        p=CommandOutputCapture(max_chars=4)
        p.start()
        outputs=[p.feed(c) for c in "abcde"]
        self.assertTrue(any(x and "truncated" in x for x in outputs))

if __name__=="__main__":
    unittest.main()

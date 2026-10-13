import tempfile
import unittest
import json
from pathlib import Path
from persona_quality_capture_v0424 import QualityCapture

class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"capture.jsonl"
        self.cap=QualityCapture(self.path)
    def test_disabled_by_default(self):
        self.assertIsNone(self.cap.record("質問","答え",agreement=.2,semantic_agreement=.9,runtime_accepted=True))
        self.assertFalse(self.path.exists())
    def test_on_off_and_append(self):
        self.cap.command("/capture on")
        a=self.cap.record("質問1","答え1",agreement=.2,semantic_agreement=.9,runtime_accepted=True)
        b=self.cap.record("質問2","答え2",agreement=.3,semantic_agreement=.8,runtime_accepted=False)
        self.assertNotEqual(a,b)
        self.assertEqual(len(self.path.read_text(encoding="utf-8").splitlines()),2)
        self.cap.command("/capture off")
        self.assertIsNone(self.cap.record("質問3","答え3",agreement=.4,semantic_agreement=.9,runtime_accepted=True))
    def test_schema(self):
        self.cap.command("/capture on")
        self.cap.record("質問","答え",agreement=.2,semantic_agreement=.9,runtime_accepted=True)
        d=json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(set(d),{"id","question","answer","agreement","semantic_agreement","runtime_accepted"})
    def test_invalid_scores_no_write(self):
        self.cap.command("/capture on")
        with self.assertRaises(ValueError):
            self.cap.record("質問","答え",agreement=float("nan"),semantic_agreement=.8,runtime_accepted=True)
        self.assertFalse(self.path.exists())
    def test_status(self):
        self.assertEqual(self.cap.command("/capture status")["records"],0)
        self.assertIsNone(self.cap.command("/reset"))
    def test_chat_hook(self):
        s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
        self.assertIn('if command in ("/capture on", "/capture off", "/capture status"):',s)
        self.assertIn("quality_capture.record(",s)
        self.assertLess(s.index('print(f"AI> {reply}")'),s.index("quality_capture.record("))
if __name__=="__main__":unittest.main()

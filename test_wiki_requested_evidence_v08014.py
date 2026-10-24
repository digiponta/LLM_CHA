import unittest
from pathlib import Path
from wiki_requested_evidence_v08014 import requested_topic_evidence

class RequestedEvidenceTests(unittest.TestCase):
    def test_explicit_mention(self):
        wiki={"title":"量子ビット","url":"https://example.org/qubit",
              "extract":"量子ビットは量子情報を表現する基本単位である。古典的なビットが0または1のいずれかの状態のみをとるのに対し、量子ビットは重ね合わせ状態をとることができる。"}
        out=requested_topic_evidence("古典ビット",wiki)
        self.assertEqual(out["status"],"FOUND")
        self.assertIn("古典的なビット",out["answer"])
        self.assertEqual(out["selected_article"],"量子ビット")
    def test_no_match(self):
        out=requested_topic_evidence("古典ビット",{"title":"量子ビット","extract":"量子状態を考える。"})
        self.assertEqual(out["status"],"NO_EVIDENCE")
    def test_no_fabrication(self):
        out=requested_topic_evidence("数学",{"title":"量子ビット","extract":"古典的なビットは0または1である。"})
        self.assertEqual(out["status"],"NO_EVIDENCE")
    def test_integrated(self):
        code=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn("WIKIPEDIA_REQUESTED_TOPIC_PARTIAL_EVIDENCE",code)
if __name__=="__main__":unittest.main()

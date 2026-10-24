import tempfile
import unittest
from pathlib import Path
from wiki_topic_memory_v074441 import learn_candidate,approve_topic,suggest_topic

WIKI={"status":"FOUND","title":"量子ビット",
      "url":"https://ja.wikipedia.org/wiki/量子ビット",
      "extract":"量子ビットは量子情報科学および量子コンピュータにおいて情報を表現するための基本単位である。古典的なビットと異なり重ね合わせ状態をとることができる。"}
class WikiTopicMemoryTests(unittest.TestCase):
    def test_approval_gate(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"memory.json"
            stored=learn_candidate(WIKI,path)
            self.assertEqual(stored["status"],"CANDIDATE_STORED")
            self.assertEqual(suggest_topic(path)["status"],"NO_APPROVED_TOPIC")
            self.assertEqual(approve_topic(stored["id"],path)["status"],"TOPIC_APPROVED")
            suggestion=suggest_topic(path)
            self.assertEqual(suggestion["status"],"FOUND")
            self.assertIn("Wikipedia",suggestion["answer"])
            self.assertFalse(suggestion["train_ready"])
    def test_no_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"memory.json"
            first=learn_candidate(WIKI,p)
            self.assertEqual(learn_candidate(WIKI,p)["status"],"EXISTS")
    def test_reject_untrusted_source(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"memory.json"
            self.assertEqual(learn_candidate(dict(WIKI,url="https://other.example/wiki"),p)["status"],"INVALID_SOURCE")
    def test_no_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"memory.json"
            self.assertEqual(learn_candidate(dict(WIKI,extract="短い。"),p)["status"],"NO_SAFE_EVIDENCE")

if __name__=="__main__":unittest.main()

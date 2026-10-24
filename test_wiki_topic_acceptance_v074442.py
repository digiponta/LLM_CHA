import tempfile
import unittest
from pathlib import Path
from wiki_topic_memory_v074441 import learn_candidate, approve_topic, suggest_topic, begin_topic

WIKI={"status":"FOUND","title":"量子ビット",
      "url":"https://ja.wikipedia.org/wiki/量子ビット",
      "extract":"量子ビットは量子情報科学および量子コンピュータにおいて情報を表現するための基本単位である。古典的なビットと異なり重ね合わせ状態をとることができる。"}
class TopicAcceptanceTests(unittest.TestCase):
    def test_suggest_accept(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"topics.json"
            item=learn_candidate(WIKI,path)
            self.assertEqual(item["status"],"CANDIDATE_STORED")
            self.assertEqual(suggest_topic(path)["status"],"NO_APPROVED_TOPIC")
            approve_topic(item["id"],path)
            offered=suggest_topic(path)
            self.assertEqual(offered["id"],item["id"])
            accepted=begin_topic(offered["id"],path)
            self.assertEqual(accepted["status"],"STARTED")
            self.assertIn("量子ビット",accepted["answer"])
            self.assertFalse(accepted["train_ready"])
    def test_unapproved_cannot_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"topics.json"
            item=learn_candidate(WIKI,path)
            self.assertEqual(begin_topic(item["id"],path)["status"],"NOT_APPROVED")
    def test_chat_wiring(self):
        source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn("pending_wiki_topic_offer = result.get(\"id\")",source)
        self.assertIn("WIKI_TOPIC_ACCEPTED",source)

if __name__=="__main__":unittest.main()

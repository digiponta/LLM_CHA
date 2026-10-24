import tempfile
import unittest
from pathlib import Path
from wiki_topic_memory_v074441 import observe_followup,suggest_topic,_load

WIKI={"status":"FOUND","title":"量子ビット","url":"https://ja.wikipedia.org/wiki/量子ビット",
      "extract":"量子ビットは量子情報科学および量子コンピュータにおいて情報を表現するための基本単位である。古典的なビットと異なり重ね合わせ状態をとることができる。"}
class WikiFollowupLearningTests(unittest.TestCase):
    def test_repeated_followup_promotes_topic_only(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"topics.json"
            first=observe_followup(WIKI,p)
            self.assertEqual(first["status"],"INTEREST_OBSERVED")
            self.assertEqual(suggest_topic(p)["status"],"NO_APPROVED_TOPIC")
            second=observe_followup(WIKI,p)
            self.assertEqual(second["status"],"TOPIC_LEARNED")
            self.assertEqual(suggest_topic(p)["status"],"FOUND")
            item=_load(p)["items"][0]
            self.assertFalse(item["train_ready"])
            self.assertFalse(item["weight_training"])
            self.assertEqual(item["truth_state"],"EXTERNAL_UNVERIFIED")
    def test_bad_source(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(observe_followup(dict(WIKI,status="NOT_FOUND"),Path(d)/"topics.json")["status"],"NO_SOURCE")
    def test_runtime_wiring(self):
        src=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn("observe_followup(cha_wiki_conversation.current)",src)
if __name__=="__main__":unittest.main()

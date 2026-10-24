import unittest
from unknown_wiki_fallback_v0557 import fallback

def lookup(term,context=None):
    return {"status":"FOUND","title":"量子ビット","url":"https://example.org/qubit","extract":"量子ビットの概要"}

def render(wiki,utterance,persona="nagato"):
    return {"answer":"article: "+wiki["title"],"source":wiki["url"]}

class TopicMatchedWikiTests(unittest.TestCase):
    def test_other_topic_rejected(self):
        result=fallback("古典ビット","古典ビットについて教えて","nagato",lookup,render)
        self.assertEqual(result["status"],"TOPIC_MISMATCH")
    def test_same_topic_accepted(self):
        result=fallback("量子ビット","量子ビットについて教えて","nagato",lookup,render)
        self.assertEqual(result["status"],"FOUND")
    def test_wrong_cache_rejected(self):
        cache={"古典ビット":lookup("量子ビット")}
        result=fallback("古典ビット","古典ビットについて教えて","nagato",lookup,render,cache=cache)
        self.assertEqual(result["status"],"TOPIC_MISMATCH")

if __name__=="__main__":unittest.main()

import tempfile
import unittest
from pathlib import Path
from wiki_topic_memory_v074441 import (
    learn_candidate,approve_topic,suggest_topic,record_used_evidence,_load)

A={"status":"FOUND","title":"量子ビット","url":"https://ja.wikipedia.org/wiki/量子ビット",
   "extract":"量子ビットは量子情報科学および量子コンピュータにおいて情報を表現するための基本単位である。古典的なビットと異なり重ね合わせ状態をとることができる。"}
B={"status":"FOUND","title":"量子力学","url":"https://ja.wikipedia.org/wiki/量子力学",
   "extract":"量子力学は微視的な物理現象を記述するために用いられる現代物理学の基本的な理論体系である。"}
class WikiEvidenceMemoryTests(unittest.TestCase):
    def test_source_matching(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"topics.json"
            result=record_used_evidence(A,"Wikipediaには、古典的なビットと異なり重ね合わせ状態をとることができる。とある。",p)
            self.assertEqual(result["status"],"EVIDENCE_RECORDED")
            self.assertEqual(result["added"],1)
            self.assertEqual(record_used_evidence(A,"無関係な内容。",p)["status"],"NO_SOURCE_MATCH")
            record_used_evidence(A,"Wikipediaには、古典的なビットと異なり重ね合わせ状態をとることができる。とある。",p)
            self.assertEqual(len(_load(p)["items"][0]["used_evidence"]),1)
            self.assertFalse(_load(p)["items"][0]["train_ready"])
    def test_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"topics.json"
            for wiki in (A,B):
                x=learn_candidate(wiki,p)
                approve_topic(x["id"],p)
            first=suggest_topic(p)["id"]
            second=suggest_topic(p)["id"]
            self.assertNotEqual(first,second)
            self.assertEqual(suggest_topic(p)["id"],first)
if __name__=="__main__":unittest.main()

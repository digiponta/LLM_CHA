import unittest
from urllib.parse import parse_qs, urlparse
from wiki_evidence_continuation_v0564 import EvidenceContinuation

W = {"status":"FOUND","title":"重ね合わせ",
     "url":"https://ja.wikipedia.org/wiki/%E9%87%8D%E3%81%AD%E5%90%88%E3%82%8F%E3%81%9B"}

def fetch(url):
    args = parse_qs(urlparse(url).query)
    if args.get("prop") == ["links"]:
        return {"query":{"pages":[{"title":"重ね合わせ",
            "links":[{"title":"量子力学"},{"title":"数学"}]}]}}
    title = args["titles"][0]
    sentences = {
       "数学":"数学では重ね合わせという語は異なる対象をまとめる方法として使用される。",
       "量子力学":"量子力学において重ね合わせは複数の状態の線形結合で記述される。"
    }
    return {"query":{"pages":[{"title":title,"extract":sentences[title]}]}}

class ContinuationTests(unittest.TestCase):
    def test_sequential_and_exhaustion(self):
        session = EvidenceContinuation()
        a = session.next(W,"もっと詳しく",fetch=fetch)
        b = session.next(W,"もっと詳しく",fetch=fetch)
        c = session.next(W,"もっと詳しく",fetch=fetch)
        self.assertEqual(a["status"],"FOUND")
        self.assertEqual(b["status"],"FOUND")
        self.assertNotEqual(a["source"],b["source"])
        self.assertEqual(c["status"],"EVIDENCE_EXHAUSTED")
        self.assertFalse(a["verified"])
        self.assertFalse(a["train_ready"])
        self.assertFalse(a["auto_promote"])

    def test_explicit_subject_required(self):
        def unrelated(url):
            args = parse_qs(urlparse(url).query)
            if args.get("prop") == ["links"]:
                return {"query":{"pages":[{"title":"重ね合わせ",
                    "links":[{"title":"量子力学"}]}]}}
            return {"query":{"pages":[{"title":"量子力学",
                "extract":"量子力学において波動関数は状態の記述に使用される。"}]}}
        r = EvidenceContinuation().next(W,"もっと詳しく",fetch=unrelated)
        self.assertEqual(r["status"],"EVIDENCE_EXHAUSTED")

    def test_network_failure(self):
        def fail(url):
            raise OSError("offline")
        self.assertEqual(EvidenceContinuation().next(W,"もっと詳しく",fetch=fail)["status"],"LOOKUP_FAILED")

    def test_non_followup(self):
        self.assertEqual(EvidenceContinuation().next(W,"散歩しよう",fetch=fetch)["status"],"NOT_APPLICABLE")

    def test_topic_change_resets_seen(self):
        s=EvidenceContinuation()
        first=s.next(W,"もっと詳しく",fetch=fetch)
        changed=dict(W,title="別の話題",url="https://ja.wikipedia.org/wiki/other")
        def new_fetch(url):
            args=parse_qs(urlparse(url).query)
            if args.get("prop")==["links"]:
                return {"query":{"pages":[{"title":"別の話題","links":[{"title":"参考文献"}]}]}}
            return {"query":{"pages":[{"title":"参考文献",
                "extract":"この資料では別の話題は十分な根拠に基づいて説明される。"}]}}
        second=s.next(changed,"もっと詳しく",fetch=new_fetch)
        self.assertEqual(first["status"],"FOUND")
        self.assertEqual(second["status"],"FOUND")

if __name__=="__main__":
    unittest.main()

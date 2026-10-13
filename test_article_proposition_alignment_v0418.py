import hashlib
import unittest
from article_proposition_alignment_v0418 import align
from wikipedia_retrieval_diagnostics_v0417 import diagnose

def evidence(topic,text):
    return {"version":"v0.4.9","candidate_id":"fixture","candidate_content_sha256":"0"*64,
       "concept":topic,"article_title":topic,
       "article_url":"https://ja.wikipedia.org/wiki/"+topic,"pageid":1,"revid":1,
       "lead_extract":text,"extract_sha256":hashlib.sha256(text.encode()).hexdigest(),
       "factual_truth":"UNVERIFIED","eligible_for_training":False,
       "revision_content_verified":False,"human_article_reviewed":False,"is_full_article":False}
class NominalDefinitionTests(unittest.TestCase):
    def test_chemistry_nominal(self):
        text="化学（かがく、英語: chemistry）とは、物質の構造と反応を扱う自然科学の一部門。"
        r=align(evidence("化学",text))
        self.assertEqual(r["proposition_count"],1)
        self.assertEqual(r["propositions"][0]["proposition_literal"],text)
    def test_no_property(self):
        self.assertEqual(align(evidence("宇宙","宇宙とは、とても広大。"))["proposition_count"],0)
    def test_no_unmarked_topic(self):
        self.assertEqual(align(evidence("化学","化学は自然科学の一部門。"))["proposition_count"],0)
    def test_no_attribution(self):
        self.assertEqual(align(evidence("化学","化学とは自然科学の一部門とされる。"))["proposition_count"],0)
    def test_no_quotation(self):
        self.assertEqual(align(evidence("化学","化学とは「自然科学の一部門」。"))["proposition_count"],0)
    def test_no_negative(self):
        self.assertEqual(align(evidence("化学","化学とは自然科学ではない分野の一部門。"))["proposition_count"],0)
    def test_existing_preserved(self):
        r=align(evidence("小説","小説は文学の形式の一つである。"))
        self.assertEqual(r["version"],"v0.4.12")
        self.assertEqual(r["v0418_nominal_added"],0)
    def test_readonly(self):
        p=align(evidence("化学","化学とは自然科学の一部門。"))["propositions"][0]
        self.assertEqual(p["factual_truth"],"UNVERIFIED")
        self.assertFalse(p["eligible_for_training"])
    def test_diagnostic_integration(self):
        def fetch(c,t):
            d=evidence(c["concept"],"化学とは自然科学の一部門。")
            d["article_url"]=c["url"]
            return d
        r=diagnose("化学とは",fetcher=fetch)
        self.assertEqual(r["reason"],"EXTRACTIVE_NOMINAL_DEFINITION")
        self.assertTrue(r["answer"].startswith("wiki>"))
    def test_source_span(self):
        text="説明文。化学とは自然科学の一部門。"
        p=align(evidence("化学",text))["propositions"][0]
        self.assertEqual(text[p["evidence_start"]:p["evidence_end"]],p["evidence_text"])
if __name__=="__main__":unittest.main()

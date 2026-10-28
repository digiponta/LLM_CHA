import unittest
from ingest_wikipedia_wikitext_v013588 import partition,process

class WikiWikitextTests(unittest.TestCase):
    def test_partition_stable(self):
        self.assertEqual(partition(1451936),partition(1451936))
    def test_markup_cleanup(self):
        from ingest_wikipedia_wikitext_v013588 import extract
        txt="'''量子力学'''は[[電子]]などを対象として、微視的な物理現象を扱う理論である。<ref>資料</ref>\n{{物理学}}\n== 参考文献 ==\nこれは除外される文章です。"
        r=extract(txt,min_chars=12)
        self.assertTrue(any("電子" in x and "物理現象" in x for x in r))
        self.assertTrue(all("資料" not in x and "除外" not in x for x in r))
    def test_disjoint_split(self):
        pages={str(i):{"id":i,"title":str(i),"source":"この文章は記事ごとに異なる学習素材として取り扱う。", "content_model":"wikitext"} for i in range(1,51)}
        train,ev,m=process(list(pages),lambda t:pages[t],min_chars=12)
        self.assertEqual(len(m),50)
        self.assertFalse({r["article_id"] for r in train}&{r["article_id"] for r in ev})
    def test_redirect_duplicate(self):
        item={"id":42,"title":"A","source":"これは十分な長さの日本語文章である。","content_model":"wikitext"}
        train,ev,manifest=process(["A","B"],lambda _:item,min_chars=12)
        self.assertEqual(len(manifest),1)
    def test_invalid_percent(self):
        with self.assertRaises(ValueError):partition(1,0)
if __name__=="__main__":unittest.main()

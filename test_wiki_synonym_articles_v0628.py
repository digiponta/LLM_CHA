import unittest
from wiki_synonym_articles_v0628 import exact_title, distinct_pages, render_pages

def fake_request(params):
    title=params["titles"]
    return {"query":{"pages":[{"title":title,"extract":title+"についての記事。",
         "fullurl":"https://ja.wikipedia.org/wiki/"+title}]}}

class WikiSynonymArticleTests(unittest.TestCase):
    def test_exact_title(self):
        page=exact_title("クルマ",request_fn=fake_request)
        self.assertEqual(page["title"],"クルマ")
    def test_two_articles(self):
        pages=distinct_pages([exact_title("クルマ",request_fn=fake_request),
                              exact_title("自動車",request_fn=fake_request)])
        answer=render_pages(pages)
        self.assertEqual(len(pages),2)
        self.assertIn("クルマ",answer)
        self.assertIn("自動車",answer)
    def test_duplicate_redirect(self):
        page=exact_title("自動車",request_fn=fake_request)
        self.assertEqual(len(distinct_pages([page,page])),1)
    def test_missing_article(self):
        def missing(params):
            return {"query":{"pages":[{"title":params["titles"],"missing":True}]}}
        self.assertIsNone(exact_title("不存在",request_fn=missing))
if __name__=="__main__":unittest.main()

import unittest
from wiki_full_article_v013588214 import find_attribute_line,resolve_full
def search(question,active=""):
 if "の硬度" in question or "の屈折率" in question:
  return {"status":"NO_ATTRIBUTE_EVIDENCE","topic":"スファレライト",
          "attribute":"硬度" if "硬度" in question else "屈折率","hits":[]}
 return {"status":"HIT","hits":[{"title":"閃亜鉛鉱","extract":"閃亜鉛鉱","url":"https://example.org"}]}
class FullTests(unittest.TestCase):
 def test_infobox(self):
  self.assertEqual(find_attribute_line("{{鉱物\n| モース硬度 = 3.5 - 4\n}}","硬度"),"| モース硬度 = 3.5 - 4")
 def test_nested_template_reject(self):
  self.assertIsNone(find_attribute_line("| 硬度 = {{convert|3.5|to|4}}","硬度"))
 def test_full(self):
  r=resolve_full("スファレライトの硬度は？",searcher=search,
                 fetcher=lambda title:{"title":title,"wikitext":"| モース硬度 = 3.5 - 4"})
  self.assertEqual(r["status"],"HIT")
 def test_absent(self):
  r=resolve_full("スファレライトの屈折率は？",searcher=search,
                 fetcher=lambda title:{"title":title,"wikitext":"本文に記載なし"})
  self.assertEqual(r["status"],"NO_ATTRIBUTE_EVIDENCE")
if __name__=="__main__":unittest.main()

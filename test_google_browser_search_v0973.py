import unittest
from google_browser_search_v0973 import search_intent, search_url, launch

class GoogleBrowserTests(unittest.TestCase):
    def test_starbucks(self):
        self.assertEqual(search_intent("スタバをググって"),"スタバ")
    def test_google_verb(self):
        self.assertEqual(search_intent("量子力学をGoogleで検索して"),"量子力学")
    def test_other_chat_unaffected(self):
        self.assertIsNone(search_intent("数学とは"))
    def test_url_encoded(self):
        self.assertIn("q=%E3%82%B9%E3%82%BF%E3%83%90",search_url("スタバ"))
    def test_opener_called_without_scraping(self):
        seen=[]
        r=launch("スタバ",opener=lambda url:seen.append(url) or True)
        self.assertTrue(r["opened"])
        self.assertFalse(r["results_collected"])
        self.assertFalse(r["train_ready"])
        self.assertEqual(len(seen),1)
    def test_reject_empty(self):
        with self.assertRaises(ValueError):
            search_url("")
if __name__=="__main__":
    unittest.main()

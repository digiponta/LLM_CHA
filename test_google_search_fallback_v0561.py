import unittest
from google_search_fallback_v0561 import search,render_leads
DATA={"organic_results":[
 {"title":"量子重ね合わせの解説","link":"https://example.org/quantum","snippet":"概要"},
 {"title":"不要なリンク","link":"javascript:alert(1)","snippet":"除外"},
 {"title":"量子力学入門","link":"https://example.edu/intro","snippet":"説明"}]}
class GoogleFallbackTests(unittest.TestCase):
 def test_not_configured(self):
  self.assertEqual(search("量子ビット",api_key="")["status"],"NOT_CONFIGURED")
 def test_mock_result(self):
  r=search("重ね合わせ",api_key="test",fetch=lambda p:DATA)
  self.assertEqual(r["status"],"FOUND");self.assertEqual(len(r["results"]),2)
 def test_provider(self):
  r=search("重ね合わせ",api_key="test",fetch=lambda p:DATA)
  self.assertEqual(r["provider"],"SERPAPI_GOOGLE")
  self.assertFalse(r["train_ready"]);self.assertFalse(r["auto_promote"])
 def test_search_parameters(self):
  captured=[]
  search("量子ビット",api_key="test",fetch=lambda p:(captured.append(p) or DATA))
  self.assertEqual(captured[0]["engine"],"google")
  self.assertEqual(captured[0]["hl"],"ja")
 def test_no_results(self):
  self.assertEqual(search("未知語",api_key="test",fetch=lambda p:{"organic_results":[]})["status"],"NO_RESULTS")
 def test_failure(self):
  def fail(p):raise OSError("network")
  self.assertEqual(search("未知語",api_key="test",fetch=fail)["status"],"SEARCH_FAILED")
 def test_render(self):
  a=render_leads(search("量子",api_key="test",fetch=lambda p:DATA))
  self.assertIn("https://example.org/quantum",a["answer"])
  self.assertFalse(a["train_ready"])
 def test_bad_key_provider_message(self):
  r=search("量子",api_key="test",fetch=lambda p:{"error":"Invalid API key"})
  self.assertEqual(r["reason"],"AUTH_OR_KEY")
 def test_quota_message(self):
  r=search("量子",api_key="test",fetch=lambda p:{"error":"Monthly quota exhausted"})
  self.assertEqual(r["reason"],"QUOTA_OR_PLAN")
 def test_no_raw_provider_message(self):
  r=search("量子",api_key="test",fetch=lambda p:{"error":"secret token exposed"})
  self.assertNotIn("secret",str(r))
 def test_no_leads_render(self):
  self.assertIsNone(render_leads({"status":"NOT_CONFIGURED"}))
if __name__=="__main__":unittest.main()

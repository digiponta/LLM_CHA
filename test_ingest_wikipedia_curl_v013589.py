import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from ingest_wikipedia_curl_v013589 import curl_article
class CurlTests(unittest.TestCase):
    def test_cache_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            with patch("ingest_wikipedia_curl_v013589.subprocess.run") as proc:
                def fake(cmd,**kw):
                    Path(cmd[cmd.index("-o")+1]).write_text(json.dumps(
                        {"id":1,"title":"量子力学","content_model":"wikitext","source":"本文。"}),encoding="utf-8")
                    class Result:returncode=0;stdout="200";stderr=""
                    return Result()
                proc.side_effect=fake
                a=curl_article("量子力学","LLM_CHA (https://example.org)",d)
                b=curl_article("量子力学","LLM_CHA (https://example.org)",d)
                self.assertEqual(a,b)
                self.assertEqual(proc.call_count,1)
    def test_bad_http_no_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("ingest_wikipedia_curl_v013589.subprocess.run") as proc:
                class Result:returncode=22;stdout="503";stderr="HTTP 503"
                proc.return_value=Result()
                with self.assertRaises(RuntimeError):
                    curl_article("量子力学","agent",Path(tmp))
                self.assertEqual(list(Path(tmp).glob("*.json")),[])
    def test_reject_invalid_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("ingest_wikipedia_curl_v013589.subprocess.run") as proc:
                def fake(cmd,**kw):
                    Path(cmd[cmd.index("-o")+1]).write_text('{"message":"not an article"}',encoding="utf-8")
                    class Result:returncode=0;stdout="200";stderr=""
                    return Result()
                proc.side_effect=fake
                with self.assertRaises(ValueError):curl_article("量子力学","agent",Path(tmp))
if __name__=="__main__":unittest.main()

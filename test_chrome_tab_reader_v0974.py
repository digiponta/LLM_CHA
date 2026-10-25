import json
import unittest
from chrome_tab_reader_v0974 import allowed_tab,read_tab

class FakeSocket:
    def __init__(self,payload):self.payload=payload;self.sent=None;self.closed=False
    def send(self,msg):self.sent=json.loads(msg)
    def recv(self):return json.dumps({"id":1,"result":{"result":{"value":self.payload}}})
    def close(self):self.closed=True

class ChromeTabTests(unittest.TestCase):
    def test_public_site_allowed(self):
        self.assertTrue(allowed_tab({"url":"https://example.org/"}))
    def test_google_search_not_scraped(self):
        self.assertFalse(allowed_tab({"url":"https://www.google.co.jp/search?q=x"}))
    def test_local_page_denied(self):
        self.assertFalse(allowed_tab({"url":"http://localhost:8000/"}))
    def test_explicit_read(self):
        tab={"id":"tab1","url":"https://example.org/a",
             "webSocketDebuggerUrl":"ws://127.0.0.1:9222/devtools/page/tab1"}
        ws=FakeSocket({"url":tab["url"],"title":"Example","text":"A publicly displayed page."})
        out=read_tab(tab,websocket_factory=lambda *args,**kwargs:ws)
        self.assertEqual(out["title"],"Example")
        self.assertFalse(out["train_ready"])
        self.assertEqual(ws.sent["method"],"Runtime.evaluate")
        self.assertTrue(ws.closed)
    def test_navigation_race_rejected(self):
        tab={"url":"https://example.org/a",
             "webSocketDebuggerUrl":"ws://127.0.0.1:9222/devtools/page/tab2"}
        ws=FakeSocket({"url":"https://example.org/b","title":"Other","text":"Hello"})
        with self.assertRaises(ValueError):
            read_tab(tab,websocket_factory=lambda *args,**kwargs:ws)
        self.assertTrue(ws.closed)
    def test_remote_cdp_denied(self):
        tab={"url":"https://example.org/",
             "webSocketDebuggerUrl":"ws://192.168.1.1:9222/devtools/page/x"}
        with self.assertRaises(ValueError):
            read_tab(tab)
if __name__=="__main__":unittest.main()

"""Read an explicitly selected non-search Chrome tab via localhost CDP.

Requires: pip install websocket-client
Use isolated Chrome profile with --remote-debugging-port=9222.
Do NOT treat a remote debugging connection as a security sandbox.
"""
import argparse
import json
import urllib.parse
import urllib.request
import uuid

HOST="127.0.0.1"
PORT=9222
MAX_TEXT=12000

def list_tabs():
    req=urllib.request.Request(f"http://{HOST}:{PORT}/json/list")
    with urllib.request.urlopen(req,timeout=3) as response:
        tabs=json.loads(response.read(1000000).decode("utf-8"))
    return [{"id":t.get("id"),"title":t.get("title",""),"url":t.get("url",""),
             "webSocketDebuggerUrl":t.get("webSocketDebuggerUrl")}
            for t in tabs if t.get("type")=="page"]

def allowed_tab(tab):
    url=urllib.parse.urlsplit(tab.get("url",""))
    if url.scheme not in ("http","https") or not url.hostname:
        return False
    domain=url.hostname.lower().rstrip(".")
    # Avoid automatic extraction of Google search result HTML.
    if domain in ("google.co.jp","www.google.co.jp","google.com","www.google.com") and url.path=="/search":
        return False
    if domain in ("localhost","127.0.0.1","::1") or domain.endswith((".local",".internal")):
        return False
    return True

def read_tab(tab, websocket_factory=None):
    if not allowed_tab(tab):
        raise ValueError("Select a normal public Web page, not a Google search page")
    ws_url=tab.get("webSocketDebuggerUrl","")
    u=urllib.parse.urlsplit(ws_url)
    if u.scheme!="ws" or u.hostname!=HOST or u.port!=PORT or u.path.startswith("/devtools/page/") is False:
        raise ValueError("Unexpected CDP WebSocket target")
    if websocket_factory is None:
        try:
            import websocket
        except ImportError as exc:
            raise RuntimeError("Install websocket-client: python -m pip install websocket-client") from exc
        websocket_factory=websocket.create_connection
    ws=websocket_factory(ws_url,timeout=5,origin=f"http://{HOST}:{PORT}")
    try:
        request_id=1
        expr="""(() => ({
            title: document.title,
            url: location.href,
            text: (document.body && document.body.innerText || '').slice(0, 12000)
        }))()"""
        ws.send(json.dumps({"id":request_id,"method":"Runtime.evaluate","params":{
            "expression":expr,"returnByValue":True,"awaitPromise":False}}))
        for _ in range(15):
            response=json.loads(ws.recv())
            if response.get("id")==request_id:
                if "error" in response or response.get("result",{}).get("exceptionDetails"):
                    raise ValueError("Chrome could not evaluate tab content")
                value=response.get("result",{}).get("result",{}).get("value",{})
                if not isinstance(value,dict):
                    raise ValueError("Invalid Chrome result")
                if value.get("url")!=tab["url"]:
                    raise ValueError("Tab navigated during read; select it again")
                result={"route":"CHROME_TAB_READ","title":str(value.get("title",""))[:250],
                        "url":value["url"],"text":str(value.get("text",""))[:MAX_TEXT],
                        "state":"EXTERNAL_UNVERIFIED","train_ready":False,
                        "auto_promote":False}
                return result
        raise TimeoutError("No CDP evaluation response")
    finally:
        ws.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--list",action="store_true")
    parser.add_argument("--tab",help="Exact CDP page target ID from --list")
    args=parser.parse_args()
    tabs=list_tabs()
    if args.list or not args.tab:
        print(json.dumps([{"id":t["id"],"title":t["title"],"url":t["url"],
                           "readable":allowed_tab(t)} for t in tabs],ensure_ascii=False,indent=2))
        return
    matched=[t for t in tabs if t["id"]==args.tab]
    if len(matched)!=1:
        raise ValueError("Tab ID not found; use --list")
    print(json.dumps(read_tab(matched[0]),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()

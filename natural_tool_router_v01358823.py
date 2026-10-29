"""Natural-language tool-intent parser. No network, I/O, or model changes."""
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class ToolIntent:
    action: str
    query: str = ""

def route(text: str):
    s=(text or "").strip()
    if not s or s.startswith("/"):
        return None
    if re.search(r"(?:クリップボード|クリップ)(?:の(?:テキスト|内容))?を?(?:読み込んで|読込|読んで|取得して)", s, re.I):
        return ToolIntent("CLIPBOARD")
    for pattern in (
        r"^(.*?)を(?:ググって|ぐぐって|ググる|ぐぐる|Googleで検索して|googleで検索して)$",
        r"^(?:Google|google)で(.+?)を?検索して$",
    ):
        m=re.match(pattern,s,re.I)
        if m:
            q=m.group(1).strip()
            return ToolIntent("GOOGLE",q) if q else None
    for pattern in (
        r"^(.*?)を(?:Wikiで調べて|wikiで調べて|Wikipediaで調べて|ウィキで調べて|Wiki検索して|Wikipediaで検索して)$",
        r"^(?:Wiki|Wikipedia|ウィキ)で(.+?)を?調べて$",
    ):
        m=re.match(pattern,s,re.I)
        if m:
            q=m.group(1).strip()
            return ToolIntent("WIKI",q) if q else None
    return None

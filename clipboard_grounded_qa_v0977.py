"""Generic-ish grounded extraction for manually copied menu pages.

The returned evidence consists only of text present in the clipboard.
No inferred product properties, model generation, approval, or training.
"""
import re

SECTIONS={"ビバレッジ":"ビバレッジ一覧へ","フード":"フード一覧へ"}
GENERIC={"メニュー","サービス","検索","店舗検索","アカウント","カート",
         "カテゴリー","季節のおすすめ","ビバレッジ","フード","Homeメニュー"}
def section_items(text):
    lines=[x.strip() for x in str(text).splitlines()]
    sections={}
    for start,end in SECTIONS.items():
        try:
            i=lines.index(start)+1
            j=lines.index(end,i)
        except ValueError:
            continue
        seen=set()
        items=[]
        for line in lines[i:j]:
            if line and line not in GENERIC and line not in seen:
                seen.add(line)
                items.append(line)
        sections[start]=items
    return sections

def answer_from_clipboard(text,question):
    q=str(question or "").strip().rstrip("。？！? ")
    sections=section_items(text)
    if not sections:
        return None
    if any(x in q for x in ("フード","食べ物","食事","スイーツ")) and any(x in q for x in ("何","教えて","一覧","ある","は")):
        items=sections.get("フード",[])
        if items:
            return {"answer":"コピーしたページのフードには、"+"、".join(items[:12])+"などが掲載されています（未検証）。",
                    "evidence":items[:12],"category":"フード"}
    if "フラペチーノ" in q:
        items=[x for x in sections.get("ビバレッジ",[]) if "フラペチーノ" in x]
        return {"answer":("コピーしたページのフラペチーノは、"+"、".join(items)+"（未検証）。")
                if items else "コピーした範囲にはフラペチーノの商品名が見つかりません。",
                "evidence":items,"category":"ビバレッジ"}
    if any(x in q for x in ("飲み物","ドリンク","ビバレッジ")) and any(x in q for x in ("何","教えて","一覧","ある","は")):
        items=sections.get("ビバレッジ",[])
        if items:
            return {"answer":"コピーしたページのビバレッジには、"+"、".join(items[:12])+"などが掲載されています（未検証）。",
                    "evidence":items[:12],"category":"ビバレッジ"}
    if any(x in q for x in ("おすすめ","お勧め")):
        return {"answer":"おすすめの根拠となる味や評価は、コピーしたページだけでは判断できません。掲載商品は確認できますが、好みを教えてください。",
                "evidence":[],"category":"OPINION_UNSUPPORTED"}
    return None

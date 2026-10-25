"""Temporary context for manually copied page text; no persistence/training."""
import re

class ClipboardContext:
    def __init__(self):
        self.text=""
    def set(self,text):
        self.text=str(text or "")[:12000]
    def clear(self):
        self.text=""
    def answer(self,utterance):
        q=str(utterance or "").strip().rstrip("。？！? ")
        if not self.text:
            return None
        if q in ("メニューは","メニューを教えて","メニューについて教えて"):
            lines=[line.strip() for line in self.text.splitlines()]
            categories=("ビバレッジ","フード","コーヒー豆","ティー・紅茶","タンブラー＆マグカップ")
            if not any(x in lines for x in ("メニュー","ビバレッジ","フード")):
                return None
            products=[]
            active=None
            skip={"メニュー","Homeメニュー","ビバレッジ一覧へ","フード一覧へ","カテゴリー"}
            for line in lines:
                if line in ("ビバレッジ","フード"):
                    active=line
                    continue
                if line in ("ビバレッジ一覧へ","フード一覧へ","カテゴリー"):
                    active=None
                    continue
                if active and line and line not in skip and line not in products:
                    products.append(line)
                if len(products)>=12:
                    break
            if not products:
                return "コピーしたページにはメニュー項目の記載がありますが、商品名を抽出できませんでした。"
            return "コピーしたページのメニューには、"+ "、".join(products)+"などが掲載されています（外部情報・未検証）。"
        if q in ("このページを要約して","この内容を要約して"):
            lines=[x.strip() for x in self.text.splitlines() if len(x.strip())>=10]
            return "コピーしたページの主な記載（抜粋・未検証）："+ " / ".join(dict.fromkeys(lines[:5]))
        return None

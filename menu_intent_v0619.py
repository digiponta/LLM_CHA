"""v0.6.19: bounded menu intent handler; never invent live product names or prices."""
import re

_MENU = re.compile(r"^(?:(スターバックス|スターバック)(?:の))?(メニュー|飲み物|フード|季節限定)(?:は|について|を教えて|って)?[？?。\s]*$")

def menu_request(text, current_topic=None):
    t=text.strip()
    match=_MENU.fullmatch(t)
    if not match: return None
    explicit,aspect=match.groups()
    if explicit == "スターバック":
        return {"status":"AMBIGUOUS","aspect":aspect}
    if explicit == "スターバックス":
        return {"status":"FOUND","topic":"スターバックス","aspect":aspect}
    if current_topic == "スターバックス":
        return {"status":"FOUND","topic":"スターバックス","aspect":aspect}
    return None

def menu_answer(request):
    if request["status"]=="AMBIGUOUS":
        return "『スターバックス』のメニューについてですか？"
    return ("スターバックスのメニューについてですね。"
            "ドリンク、フード、季節限定商品のどれを知りたい？"
            " 最新の商品や価格は公式メニューで確認する必要があります。")

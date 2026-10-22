"""v0.6.25 history evidence ranking, requiring source dates and readable prose."""
import re

DATE = re.compile(r"(?<!\d)(?:18\d{2}|19\d{2}|20\d{2})年")
EVENT = ("設立","創業","創立","発売","生産","開始","完成","発足","統合","設置","開業","進出","移転")

def history_events(lines, limit=3):
    ranked=[]
    for line in lines:
        text=line.strip()
        if not (15 <= len(text) <= 300):continue
        if any(x in text for x in ("<",">","{{","}}","[[","]]","|")):continue
        dates=DATE.findall(text)
        if not dates or not any(word in text for word in EVENT):continue
        ranked.append((int(dates[0][:-1]),text))
    ranked.sort(key=lambda row:row[0])
    result=[]
    for _,sentence in ranked:
        if sentence not in result:result.append(sentence)
        if len(result)>=limit:break
    return result

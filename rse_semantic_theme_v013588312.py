"""Experimental theme-aware RSE; fails closed with 未学習です.

No learned-model inference, automatic training, or chat.py integration.
Theme alone never authorizes an answer.
"""
import argparse,json,re
from pathlib import Path

UNLEARNED="未学習です"
def semantic_features(text):
    t=str(text).strip()
    if re.search(r"話(し|そう|せ|す)|お話|会話|話題",t):
        theme="話題"
        if re.search(r"何について|どんな話|話題(は|を|について)",t):
            act="REQUEST_TOPIC"
        elif re.search(r"話(しませんか|そう|せませんか|したい)|お話しし",t):
            act="INVITE_CONVERSATION"
        else: act="DISCUSS_TOPIC"
        return {"theme":theme,"intent":act,"time":None}
    if re.search(r"こんにちは|こんばんは|おはよう",t):
        return {"theme":"挨拶","intent":"GREETING","time":None}
    if re.search(r"何(を|して)|何して|している|してる|楽しい|好き",t):
        intent="CURRENT_ACTIVITY" if re.search(r"今|現在|今日.*何",t) else "ENJOYMENT" if re.search(r"楽しい|好き",t) else "ACTIVITY"
        return {"theme":"活動","intent":intent,"time":"NOW" if intent=="CURRENT_ACTIVITY" else None}
    return {"theme":None,"intent":"UNKNOWN","time":None}

def reply_role(response):
    t=str(response).strip()
    if re.search(r"^(もちろん|いいですよ|いいですね|喜んで)",t) and re.search(r"話|何について|どんな",t):
        return "ACCEPT_AND_REQUEST_TOPIC"
    if re.search(r"^(こんにちは|こんばんは|おはよう)[！!。\s]*$",t):
        return "RETURN_GREETING"
    return "OTHER"

def persona_risk(answer):
    # Conservative structural screen, not an exhaustive semantic classifier.
    return bool(re.search(r"私|僕|俺|うち|実家|家族|職場|昨日|先週|住んで|食べた|飲んだ|小説書いて|よく読み|好きです",answer))

def relation_ok(query,answer):
    f=semantic_features(query)
    role=reply_role(answer)
    if f["theme"]=="話題" and f["intent"]=="INVITE_CONVERSATION":
        return role=="ACCEPT_AND_REQUEST_TOPIC"
    if f["theme"]=="挨拶" and f["intent"]=="GREETING":
        return role=="RETURN_GREETING"
    return False

def select(query,candidates):
    f=semantic_features(query)
    trace=[];approved=[]
    for i,c in enumerate(candidates):
        question=str(c.get("question",""))
        answer=str(c.get("answer",""))
        source=semantic_features(question)
        why=[]
        if not f["theme"] or f["theme"]!=source["theme"]:why.append("THEME_MISMATCH")
        if f["intent"]!=source["intent"]:why.append("INTENT_MISMATCH")
        if f["time"]!=source["time"]:why.append("TIME_SLOT_MISMATCH")
        if not relation_ok(query,answer):why.append("RESPONSE_RELATION_MISMATCH")
        if persona_risk(answer):why.append("PERSONA_TRANSFER_RISK")
        record={"candidate_id":str(c.get("id",i)),"decision":"REJECT" if why else "MATCH","reasons":why}
        trace.append(record)
        if not why:approved.append((str(c.get("id",i)),answer))
    if len(approved)==1:
        return {"status":"ANSWER_SELECTED","answer":approved[0][1],"candidate_id":approved[0][0],
                "theme":f["theme"],"trace":trace,"auto_generation":False}
    return {"status":"UNLEARNED","answer":UNLEARNED,"candidate_id":None,
            "theme":f["theme"],"trace":trace,
            "reason":"NO_MATCH" if not approved else "MULTIPLE_MATCHES_REQUIRE_DISAMBIGUATION",
            "auto_generation":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--query",required=True)
    p.add_argument("--candidates",default="data/rse_theme_examples_v013588312.json")
    a=p.parse_args()
    data=json.loads(Path(a.candidates).read_text(encoding="utf-8-sig"))
    print(json.dumps(select(a.query,data["candidates"]),ensure_ascii=False,indent=2))
if __name__=="__main__":main()

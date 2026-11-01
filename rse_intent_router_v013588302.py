"""Intent-aware RSE diagnostic: routing only; no impersonation or automatic generation."""
import argparse,json,re
from pathlib import Path

PATTERNS=[
 ("CHAT_INVITATION",r"(少し|ちょっと)?話さない|お話ししよ|話そう"),
 ("STATUS_QUERY",r"最近どう|調子はどう|元気[？?]?"),
 ("ACTIVITY_QUERY",r"今何して|今日は何して|何をしてる|何してる"),
 ("GREETING",r"^(こんにちは|おはよう|こんばんは|やあ)[！!。\s]*$"),
]
FACTUAL=re.compile(r"(.+?)(とは|って何|の意味|の成分|の化学組成|について教えて)")
def route(question):
    q=question.strip()
    for intent,pattern in PATTERNS:
        if re.search(pattern,q):return {"route":"DIALOGUE_INTENT","intent":intent,"reason":"PATTERN_MATCH"}
    if FACTUAL.search(q):
        return {"route":"SEMANTIC_MEMORY_FIRST","intent":"FACTUAL","reason":"KNOWLEDGE_QUESTION"}
    return {"route":"RSE_CONTENT_RETRIEVAL","intent":"OTHER","reason":"NO_INTENT_RULE"}

# Safe responses describe only the assistant's conversational availability;
# never claim participant's biographical events or physical activities.
SAFE_TEMPLATES={
 "CHAT_INVITATION":"もちろん。どんな話をしましょうか？",
 "STATUS_QUERY":"こちらは会話できます。最近、何か気になることはありますか？",
 "ACTIVITY_QUERY":"今はあなたのメッセージに応答しています。何について話しましょうか？",
 "GREETING":"こんにちは。今日は何についてお話ししましょうか？",
}
def evaluate(question):
    routed=route(question)
    if routed["route"]=="DIALOGUE_INTENT":
        return {**routed,"status":"SAFE_TEMPLATE_CANDIDATE",
                "response":SAFE_TEMPLATES[routed["intent"]],
                "source":"ASSISTANT_SAFE_TEMPLATE",
                "persona_claims_from_real_persona_chat":False,
                "expansion_enabled":False}
    if routed["route"]=="SEMANTIC_MEMORY_FIRST":
        return {**routed,"status":"DEFER_TO_EXISTING_MEMORY","response":None,
                "expansion_enabled":False}
    return {**routed,"status":"DEFER_TO_CONTENT_RSE","response":None,
            "expansion_enabled":False}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--question",required=True)
    ap.add_argument("--report",default="results/rse_intent_v013588302.json")
    x=ap.parse_args()
    result=evaluate(x.question)
    target=Path(x.report);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()

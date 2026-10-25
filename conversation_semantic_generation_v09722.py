"""Diagnostic A/B/C grounded prompting with the loaded LLM checkpoint.

No persistent history, no candidate auto-selection, and no raw clipboard
dump. This experiment measures generation, not semantic truth.
"""
from clipboard_grounded_qa_v0977 import section_items
from difflib import SequenceMatcher

def semantic_text(state):
    if state.get("status")=="EMPTY" or not state.get("entity"):
        return ""
    parts=["会話対象（外部ページ記載・未検証）: "+state["entity"]]
    if state.get("event"):
        parts.append("ユーザー報告イベント: "+state["event"])
    names={"acidity":"酸味","sweetness":"甘さ","chocolate":"チョコレート","bitterness":"苦味"}
    values=[names.get(k,k) for k,v in state.get("attributes",{}).items() if v.get("provenance")=="USER_REPORTED"]
    if values:parts.append("ユーザーが言及した味の要素（評価の極性は不明）: "+"、".join(values))
    if state.get("evaluation",{}):
        parts.append("ユーザーの評価: "+state["evaluation"]["value"])
    return "\n".join(parts)

def evidence_text(state,clipboard):
    entity=state.get("entity")
    if not entity:return ""
    items=[item for entries in section_items(clipboard).values() for item in entries]
    return "コピーしたページの商品名（未検証）: "+entity if entity in items else ""

def compare_prompts(question,state,clipboard,model,tokenizer,generate,max_new_tokens=96):
    q=str(question).strip()
    if not q:raise ValueError("question required")
    sem=semantic_text(state)
    evidence=evidence_text(state,clipboard)
    if not sem:return {"status":"NO_SEMANTIC_STATE","train_ready":False}
    prompts={
        "A_BASELINE":f"人: {q}\nAI:",
        "B_SEMANTIC":f"文脈（ユーザー報告・未検証）:\n{sem}\n人: {q}\nAI:",
        "C_EVIDENCE_SEMANTIC":f"外部ページ根拠（未検証）:\n{evidence or '関連する根拠なし'}\n会話文脈:\n{sem}\n人: {q}\nAI:"
    }
    trials={}
    for name,prompt in prompts.items():
        generated=generate(model=model,tokenizer=tokenizer,prompt=prompt,
                           max_new_tokens=max_new_tokens,temperature=0.0,top_k=3,
                           repetition_penalty=1.08,seed=42)
        answer=str(generated.text or "")
        trials[name]={"answer":answer,"token_count":generated.token_count,
                      "topic_present":state["entity"] in answer,
                      "prompt_chars":len(prompt)}
    return {"status":"DIAGNOSTIC_ONLY","question":q,"trials":trials,
            "source_provenance":"CLIPBOARD_UNVERIFIED",
            "experience_provenance":"USER_REPORTED",
            "selected":None,"verified":False,"train_ready":False,
            "persisted":False,"auto_promote":False}

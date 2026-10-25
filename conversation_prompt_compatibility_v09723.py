"""v0.9.7.23 diagnostic-only prompt compatibility experiment.

Five formats, the same model, same question, same decoding parameters.
This does not assert fluency or evidence entailment from lexical overlap.
"""
from conversation_semantic_generation_v09722 import semantic_text,evidence_text

def natural_context(state):
    entity=state.get("entity")
    if not entity:return ""
    fragments=["ユーザーは「"+entity+"」について話している。"]
    if state.get("event")=="consumption":
        fragments.append("ユーザーはこの商品を飲んだと報告した。")
    mapping={"acidity":"酸味","sweetness":"甘さ","chocolate":"チョコレート","bitterness":"苦味"}
    names=[mapping.get(key,key) for key,v in state.get("attributes",{}).items()
           if v.get("provenance")=="USER_REPORTED"]
    if names:fragments.append("味について"+ "、".join(names)+"に言及した。評価の強弱や因果関係は不明。")
    evaluation=state.get("evaluation")
    if evaluation and evaluation.get("provenance")=="USER_REPORTED":
        fragments.append("ユーザーは「"+str(evaluation["value"])+"」と述べた。")
    fragments.append("商品名はコピーした外部ページに由来し未検証である。")
    return "".join(fragments)

def prompts(question,state,clipboard):
    question=str(question or "").strip()
    if not question:raise ValueError("question is required")
    structured=semantic_text(state)
    if not structured:raise ValueError("semantic state is empty")
    natural=natural_context(state)
    source=evidence_text(state,clipboard)
    dialogue=("人: "+state["entity"]+"を飲んだ\n"
              "AI: どんな味だった？\n"
              "人: 酸味と甘さ、チョコレートについて話した。\n"
              "AI: なるほど。\n"
              "人: "+str((state.get("evaluation") or {}).get("value","満足した"))+"\n"
              "AI: そうなのね。\n")
    return {
        "A_BASELINE":f"人: {question}\nAI:",
        "B_STRUCTURED":f"文脈（未検証）:\n{structured}\n人: {question}\nAI:",
        "C_NATURAL":f"{natural}\n人: {question}\nAI:",
        "D_DIALOGUE_RECONSTRUCTION":dialogue+f"人: {question}\nAI:",
        "E_NAGATO_CHAT_STYLE":f"人: {natural}\nAI: そう。\n人: {question}\nAI:",
    }

def compare(question,state,clipboard,model,tokenizer,generate,max_new_tokens=96):
    if not state.get("entity"):
        return {"status":"NO_SEMANTIC_STATE","trials":{},"train_ready":False}
    variants=prompts(question,state,clipboard)
    result={}
    for name,prompt in variants.items():
        generated=generate(model=model,tokenizer=tokenizer,prompt=prompt,
                           max_new_tokens=max_new_tokens,temperature=0.0,
                           top_k=3,repetition_penalty=1.08,seed=42)
        answer=str(generated.text or "")
        result[name]={"answer":answer,"tokens":generated.token_count,
                      "chars":len(answer),"prompt_chars":len(prompt),
                      "entity_exact_match":state["entity"] in answer}
    return {"status":"DIAGNOSTIC_ONLY","question":question,"trials":result,
            "prompt_style_e_is_hypothesis":True,
            "selected":None,"train_ready":False,"persisted":False,
            "auto_promote":False,"verified":False}

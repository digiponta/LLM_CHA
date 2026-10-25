"""v0.9.7.27: ephemeral semantic-to-dialogue adapter ablation.

No answers are adopted; all generated candidates remain diagnostic.
"""
import re

def alias_for(state):
    name=str(state.get("entity") or "")
    for marker in ("黒耳","白耳"):
        if marker in name:return marker
    return name[:16] if name else ""

def prompt_variants(state,question):
    from chat import USER_PREFIX,AI_PREFIX
    alias=alias_for(state)
    if not alias:raise ValueError("semantic entity missing")
    q=str(question or "").strip()
    if not q:raise ValueError("question missing")
    inline=f"{USER_PREFIX}会話対象: {alias}。体験: 飲んだ。 {q}\n{AI_PREFIX}"
    dialogue=(f"{USER_PREFIX}{alias}を飲んだ\n{AI_PREFIX}そうなのね。\n"
              f"{USER_PREFIX}{q}\n{AI_PREFIX}")
    short=(f"{USER_PREFIX}{alias}について話している。{q}\n{AI_PREFIX}")
    taste=[]
    attrs=state.get("attributes") or {}
    for key,label in (("acidity","酸味"),("sweetness","甘さ"),("chocolate","チョコレート")):
        if attrs.get(key,{}).get("provenance")=="USER_REPORTED":taste.append(label)
    selected=("、".join(taste[:2]) if taste else "味")
    retrieved=(f"{USER_PREFIX}{alias}の{selected}について話した。{q}\n{AI_PREFIX}")
    hybrid=(f"{USER_PREFIX}{alias}を飲んだ\n{AI_PREFIX}どんな味だった？\n"
            f"{USER_PREFIX}{selected}が印象に残った\n{AI_PREFIX}そうなのね。\n"
            f"{USER_PREFIX}{q}\n{AI_PREFIX}")
    return {"A_INLINE":inline,"B_DIALOGUE":dialogue,
            "C_SHORT_ALIAS":short,"D_RETRIEVED":retrieved,"E_HYBRID":hybrid}

def audit(state,model,tokenizer,generate,question="その体験についてどう思う？"):
    if not state.get("entity"):
        return {"status":"NO_SEMANTIC_STATE","trials":{},"train_ready":False}
    cases=prompt_variants(state,question)
    out={}
    for name,prompt in cases.items():
        result=generate(model=model,tokenizer=tokenizer,prompt=prompt,
                        max_new_tokens=64,temperature=0.0,top_k=3,
                        repetition_penalty=1.08,seed=42)
        answer=str(result.text or "")
        out[name]={"prompt":prompt,"prompt_tokens":len(tokenizer.encode(prompt,add_bos=True)),
                   "answer":answer,"generated_tokens":result.token_count,
                   "mean_confidence":result.mean_confidence,
                   "min_token_confidence":result.min_confidence,
                   "alias_present":alias_for(state) in answer}
    return {"status":"DIAGNOSTIC_ONLY","question":question,"trials":out,
            "synthetic_dialogue":True,"truth_verified":False,
            "selected":None,"train_ready":False,"persisted":False,
            "auto_promote":False}

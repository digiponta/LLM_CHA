"""v0.9.7.26: isolate which semantic-context component derails known QA.

Seven deterministic probes, full prompts and token diagnostics included.
No training, promotion, or response selection.
"""
def prompts():
    from chat import build_prompt,USER_PREFIX,AI_PREFIX
    question="あなたは誰ですか"
    inline={
        "A_BASELINE":"",
        "B_EXPERIENCE":"商品を飲んだ。",
        "C_CATEGORY":"フラペチーノを飲んだ。",
        "D_ALIAS":"黒耳を飲んだ。",
        "E_FULL_NAME":"ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.を飲んだ。",
        "F_SEMANTIC_SYNTAX":"会話対象: 黒耳。体験: 飲んだ。",
    }
    result={name:build_prompt([],prefix+" "+question if prefix else question,0)[0]
            for name,prefix in inline.items()}
    # Deliberately do NOT use select_relevant_history: force a real
    # multi-turn prompt to prevent the v0.9.7.25 D false positive.
    result["G_FORCED_QA_HISTORY"]=(
        f"{USER_PREFIX}こんにちは\n{AI_PREFIX}こんにちは。\n"
        f"{USER_PREFIX}{question}\n{AI_PREFIX}"
    )
    return result

def audit(model,tokenizer,generate):
    p=prompts()
    results={}
    for name,prompt in p.items():
        out=generate(model=model,tokenizer=tokenizer,prompt=prompt,
                     max_new_tokens=64,temperature=0.0,top_k=3,
                     repetition_penalty=1.08,seed=42)
        answer=str(out.text or "")
        ids=tokenizer.encode(prompt,add_bos=True)
        results[name]={
            "prompt":prompt,
            "prompt_tokens":len(ids),
            "answer":answer,
            "generated_tokens":out.token_count,
            "mean_confidence":out.mean_confidence,
            "min_token_confidence":out.min_confidence,
            "identity_exact":answer.strip() in ("長門有希","長門有希。"),
        }
    return {"status":"DIAGNOSTIC_ONLY",
            "study":"SEMANTIC_CONTEXT_FAILURE_ISOLATION",
            "trials":results,"fixed_decode":True,
            "forced_history_verified":"こんにちは。\n" in p["G_FORCED_QA_HISTORY"],
            "selected":None,"train_ready":False,"persisted":False,
            "auto_promote":False}

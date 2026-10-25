"""v0.9.7.25 — six-condition context robustness probe, diagnostic only.

A-E share exactly the same final identity question; F is a paraphrase.
This is not held-out evaluation and does not change runtime routing.
"""
def make_prompts():
    from chat import build_prompt
    q="あなたは誰ですか"
    return {
        "A_CANONICAL":build_prompt([],q,0)[0],
        "B_UNRELATED_CONTEXT":build_prompt([],"今日は雨が降っています。 "+q,0)[0],
        "C_RELATED_CONTEXT":build_prompt([],"長門有希という名前について質問します。 "+q,0)[0],
        "D_QA_HISTORY":build_prompt([("こんにちは","こんにちは。")],q,1)[0],
        "E_SEMANTIC_CONTEXT":build_prompt([],"会話対象: ブラックベリー ヨーグルト フラペチーノ。体験: 飲んだ。 "+q,0)[0],
        "F_PARAPHRASE":build_prompt([],"名前を教えてください",0)[0],
    }

def run(model,tokenizer,generate):
    prompts=make_prompts()
    results={}
    for key,prompt in prompts.items():
        out=generate(model=model,tokenizer=tokenizer,prompt=prompt,
                     max_new_tokens=64,temperature=0.0,top_k=3,
                     repetition_penalty=1.08,seed=42)
        text=str(out.text or "")
        results[key]={"answer":text,"token_count":out.token_count,
                      "prompt_tokens":len(tokenizer.encode(prompt,add_bos=True)),
                      "mean_confidence":out.mean_confidence,
                      "min_token_confidence":out.min_confidence,
                      "identity_exact":"長門有希" in text}
    return {"status":"DIAGNOSTIC_ONLY","results":results,
            "same_final_question_except_F":True,
            "benchmark_type":"CONTROLLED_PROBES_NOT_HELD_OUT",
            "selected":None,"train_ready":False,"persisted":False}

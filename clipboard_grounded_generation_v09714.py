"""Opt-in actual LLM generation from clipboard evidence, diagnostic-only.

Uses the *already-loaded* chat model via injected generate_reply callable.
Model answers do not replace the source quotation baseline, get approved,
or enter training. The legacy lexical gate is only a heuristic diagnostic.
"""
from clipboard_context_expansion_v09712 import expand,answer as quote_answer
from grounded_generation_gate_v096 import compare

def experiment(question,source_text,model,tokenizer,generate,max_new_tokens=96):
    baseline=quote_answer(question,source_text)
    if not baseline:
        return {"status":"NO_EVIDENCE","selected":None,"train_ready":False}
    matched=expand(question,source_text,max_items=2)
    evidence=[]
    for item in matched:
        if item.get("description"):
            evidence.append(item["description"])
        else:
            evidence.append(item["topic"])
    if not evidence:
        return {"status":"NO_EVIDENCE","selected":baseline,"train_ready":False}
    topic=matched[0]["topic"]
    prompt=("以下は外部サイトからユーザーがコピーした未検証の引用です。"
            "引用に書かれていないことは断言せず、質問に日本語で短く答えてください。\n"
            "質問："+question+"\n"
            "引用：\n"+"\n".join(evidence[:2])+"\n"
            "AI: ")
    generated=generate(model=model,tokenizer=tokenizer,prompt=prompt,
                       max_new_tokens=max_new_tokens,temperature=0.0,
                       top_k=3,repetition_penalty=1.08,seed=42)
    candidate=str(generated.text or "")
    audit=compare(baseline,candidate,question,topic,evidence)
    # The existing gate can accept unsupported statements. Never deploy the
    # model text automatically merely because this gate says ACCEPT.
    return {"status":"DIAGNOSTIC_ONLY","baseline":baseline,
            "candidate":candidate,"generation_origin":"REAL_CHECKPOINT",
            "token_count":generated.token_count,"topic":topic,
            "evidence":evidence,"gate":audit["candidate_gate"],
            "selected":baseline,"candidate_auto_selected":False,
            "truth_state":"EXTERNAL_UNVERIFIED",
            "train_ready":False,"auto_promote":False}

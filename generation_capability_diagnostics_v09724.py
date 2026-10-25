"""Generation capability audit: tokenizer roundtrip, known prompts and context load.

Read-only, diagnosis only. Known prompts are probes, not validated QA labels.
"""
from difflib import SequenceMatcher

PROBES=("あなたは誰ですか","名前を教えてください","こんにちは")
def tokenizer_audit(tokenizer,samples):
    rows=[]
    for sample in samples:
        ids=tokenizer.encode(sample,add_bos=False)
        decoded=tokenizer.decode(ids,skip_special_tokens=True)
        rows.append({"sample":sample,"tokens":len(ids),"roundtrip":decoded,
                     "exact":sample==decoded,"similarity":round(SequenceMatcher(None,sample,decoded).ratio(),4)})
    return rows

def run(model,tokenizer,generate,question="あなたは誰ですか",context="ユーザーは商品を飲んだと述べた。",
        max_new_tokens=64):
    from chat import build_prompt,USER_PREFIX,AI_PREFIX
    variants={
      "A_CANONICAL":build_prompt([],question,0)[0],
      "B_SHORT_CONTEXT":build_prompt([],context+" "+question,0)[0],
      "C_LONG_CONTEXT":build_prompt([],context*6+" "+question,0)[0],
    }
    results={}
    for name,prompt in variants.items():
        response=generate(model=model,tokenizer=tokenizer,prompt=prompt,
            max_new_tokens=max_new_tokens,temperature=0.0,top_k=3,
            repetition_penalty=1.08,seed=42)
        results[name]={"answer":response.text,"token_count":response.token_count,
                       "prompt_tokens":len(tokenizer.encode(prompt,add_bos=True)),
                       "min_token_confidence":response.min_confidence,
                       "mean_confidence":response.mean_confidence}
    return {"status":"DIAGNOSTIC_ONLY",
            "runtime_prefixes":{"user":USER_PREFIX,"assistant":AI_PREFIX},
            "tokenizer":tokenizer_audit(tokenizer,[question,context,"黒耳を飲んだ","満足した"]),
            "generation":results,"training_format_verified":False,
            "auto_select":False,"train_ready":False,"persisted":False}

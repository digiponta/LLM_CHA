"""Model-only greedy generation probe; no retrieval, chat router or training.

Direct prompts reuse existing memory questions and are NOT independent holdout.
A separate externally reviewed paraphrase set may be supplied by --holdout.
"""
import argparse
import json
import re
from pathlib import Path

def generate_answer(model,tokenizer,question,max_tokens=96):
    import torch
    prompt=tokenizer.encode("ユーザー: "+question+"\nAI: ",add_bos=True)
    if not prompt:raise ValueError("Prompt tokenization returned empty tokens")
    with torch.inference_mode():
        tokens=model.generate(prompt,max_new_tokens=max_tokens,eos_id=tokenizer.eos_id,
                              temperature=0.0,top_k=None,repetition_penalty=1.05)
    output=tokenizer.decode(tokens[len(prompt):]).strip()
    return re.split(r"\n(?:ユーザー|User|AI)\s*:",output,maxsplit=1)[0].strip()

def normalize(s):
    return re.sub(r"\s+","",str(s or "")).strip("。．.!！?？ ")

def score(generated,reference):
    generated=normalize(generated); reference=normalize(reference)
    return {"nonempty":bool(generated),"exact":bool(generated) and generated==reference,
            "reference_contained":bool(reference) and reference in generated}

def load_cases(memory,holdout=None,limit=56):
    if holdout:
        data=json.loads(Path(holdout).read_text(encoding="utf-8-sig"))
        if not isinstance(data,list):raise ValueError("Holdout must be a JSON array")
        cases=[{"concept":r.get("concept"),"question":r["question"],"answer":r["answer"]} for r in data]
        source="USER_SUPPLIED_HOLDOUT_UNATTESTED"
    else:
        from semantic_sleep_learning_v10131 import load_nagato_semantic_memory
        rows=load_nagato_semantic_memory(Path(memory))
        cases=[{"concept":r.get("concept"),"question":r["question"],"answer":r["assistant"]} for r in rows]
        source="TRAIN_ASSOCIATED_DIRECT"
    return cases[:limit],source

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--memory",default="data/nagato_semantic_memory_v10131.jsonl")
    p.add_argument("--holdout",default=None,help="JSON array of reviewed {question,answer,concept}; independence not assumed")
    p.add_argument("--tokenizer",default="../LLM_GPU/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--base",default="model/model-llm-try-nagato-chat-v94.pt")
    p.add_argument("--online",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--limit",type=int,default=56)
    p.add_argument("--max-new-tokens",type=int,default=96)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--output",default="results/semantic_generation_v0100.json")
    args=p.parse_args()
    if args.limit<=0 or args.max_new_tokens<=0:p.error("limits must be positive")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    device="cuda" if args.device=="auto" and torch.cuda.is_available() else ("cpu" if args.device=="auto" else args.device)
    tok=Tokenizer.load(args.tokenizer)
    models={}
    for key,path in (("base",args.base),("online",args.online)):
        model,_=LanguageModel.load_checkpoint(path,device=torch.device(device))
        if model.vocab_size!=tok.vocab_size:raise ValueError("Vocab mismatch: "+key)
        model.eval();models[key]=model
    cases,source=load_cases(args.memory,args.holdout,args.limit)
    rows=[]
    for case in cases:
        outcome={}
        for key,model in models.items():
            answer=generate_answer(model,tok,case["question"],args.max_new_tokens)
            outcome[key]={"generated":answer,**score(answer,case["answer"])}
        rows.append({"concept":case["concept"],"question":case["question"],
                     "reference":case["answer"],**outcome})
    totals={key:{"nonempty":sum(r[key]["nonempty"] for r in rows),
                 "exact":sum(r[key]["exact"] for r in rows),
                 "reference_contained":sum(r[key]["reference_contained"] for r in rows)}
            for key in models}
    report={"method":"MODEL_ONLY_GREEDY_GENERATION","retrieval_used":False,
            "evaluation_source":source,"independence_attested":False,
            "cases":len(rows),"device":device,"totals":totals,"records":rows,
            "caution":"Exact match is strict; substring match can over-credit. Manual semantic correctness review required."}
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="records"},ensure_ascii=False,indent=2))
    print("report:",path)

if __name__=="__main__":main()

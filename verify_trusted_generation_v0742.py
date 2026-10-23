"""v0.7.42: read-only, unassisted Trusted LLM free-generation probe.

No chat.py runtime routing, Corpus Memory retrieval, Wikipedia, Experimental
adapter, or prompt answer seeding. This is not a factual truth validator.
"""
import argparse
import hashlib
import json
from pathlib import Path

DEFAULT_PROBES=[
    {"group":"approved_paraphrase","question":"真空管について説明して",
     "expected_terms":["真空管"]},
    {"group":"approved_paraphrase","question":"真空管の特性は",
     "expected_terms":["真空管"]},
    {"group":"stability","question":"あなたは誰ですか",
     "expected_terms":["長門有希"]},
    {"group":"stability","question":"AIとは",
     "expected_terms":["学習"]},
    {"group":"stability","question":"LLMとは",
     "expected_terms":["言語"]},
    {"group":"stability","question":"CUDAとは",
     "expected_terms":["GPU"]},
    {"group":"stability","question":"量子力学とは",
     "expected_terms":["状態"]},
]

def make_probes(ledger, include_defaults=True):
    probes=[]
    for r in ledger:
        probes.append({"group":"approved_exact","question":r["user"],
                       "expected_answer":r["assistant"],"approved_id":r["id"]})
    if include_defaults:probes.extend(DEFAULT_PROBES)
    return probes

def answer_match(output,expected):
    output="".join(output.split())
    expected="".join(expected.split())
    if not expected:return False
    return expected in output

def perform(model,tokenizer,probes,max_new_tokens=128):
    cases=[]
    for p in probes:
        prompt="人: "+p["question"]+"\nAI: "
        ids=tokenizer.encode(prompt,add_bos=True)
        generated=model.generate(ids,max_new_tokens=max_new_tokens,
                                 eos_id=tokenizer.eos_id,
                                 temperature=0.0,top_k=None,
                                 repetition_penalty=1.0)
        answer=tokenizer.decode(generated[len(ids):],skip_special_tokens=True).strip()
        expected=p.get("expected_answer")
        terms=p.get("expected_terms",[])
        case={"group":p["group"],"question":p["question"],"generated":answer,
              "generated_token_count":len(generated)-len(ids),
              "contains_expected_answer":answer_match(answer,expected) if expected is not None else None,
              "term_hits":{term:term in answer for term in terms}}
        if "approved_id" in p:case["approved_id"]=p["approved_id"]
        cases.append(case)
    return cases

def summarize(cases):
    result={}
    for group in sorted({c["group"] for c in cases}):
        subset=[x for x in cases if x["group"]==group]
        result[group]={"count":len(subset),
                       "answer_containment":sum(x["contains_expected_answer"] is True for x in subset),
                       "term_all":sum(bool(x["term_hits"]) and all(x["term_hits"].values()) for x in subset)}
    return result

def _sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    return h.hexdigest()

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--model",default="model/model-gpu-v1.6.2-online.pt")
    a.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    a.add_argument("--ledger",default="data/approved_semantic_memory_v0740.jsonl")
    a.add_argument("--output",default="results/trusted_generation_v0742.json")
    a.add_argument("--max-new-tokens",type=int,default=128)
    args=a.parse_args()
    if not 1<=args.max_new_tokens<=512:raise ValueError("invalid max new tokens")
    from approved_semantic_sleep_v0740 import _load_jsonl
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    import torch
    ledger=_load_jsonl(args.ledger)
    if not ledger:raise ValueError("Approved ledger empty")
    inputs=[Path(v).resolve() for v in (args.model,args.tokenizer,args.ledger)]
    if Path(args.output).resolve() in inputs:raise ValueError("output overlaps protected input")
    hashes={str(p):_sha(p) for p in inputs}
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model,_=LanguageModel.load_checkpoint(args.model,device=device)
    tokenizer=Tokenizer.load(args.tokenizer)
    cases=perform(model,tokenizer,make_probes(ledger),args.max_new_tokens)
    if hashes!={str(p):_sha(p) for p in inputs}:raise RuntimeError("protected input changed")
    report={"version":"v0.7.42","device":str(device),"route":"MODEL_ONLY",
            "sampling":"greedy","prompt":"人: {question}\\nAI: ",
            "external_memory_used":False,"approved_total":len(ledger),
            "summary":summarize(cases),"cases":cases,
            "protected_unchanged":True,
            "factual_truth_validation":"NOT_PERFORMED",
            "limitation":"Contains-answer and term-hit metrics are not semantic entailment or generalization proof."}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("version","device","route","approved_total","summary","protected_unchanged")},ensure_ascii=False,indent=2))
    print("report:",out)

if __name__=="__main__":main()

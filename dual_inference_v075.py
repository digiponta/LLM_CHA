"""v0.7.5: explicit-only experimental inference and free-generation comparison.

Never uses Experimental Adapter in normal mode. Does not change chat.py,
approved memory, candidate memory, or model checkpoints.
"""
import argparse
import json
from pathlib import Path

import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from dual_adapters_v073 import DualAdapterModel
from evaluate_dual_adapter_v074 import load_experimental
from dual_semantic_memory_v071 import DualMemory

def route(mode, experimental_authorized=False):
    if mode=="normal":
        return "trusted"
    if mode=="experiment" and experimental_authorized:
        return "experimental"
    raise ValueError("Experimental route requires explicit --allow-experimental")

@torch.no_grad()
def generate(model, tokenizer, question, route_name, max_new_tokens=32):
    if route_name not in ("base","trusted","experimental"):
        raise ValueError("invalid inference route")
    prompt="人: "+question+"\nAI: "
    ids=tokenizer.encode(prompt,add_bos=True)
    if not ids:raise ValueError("empty prompt")
    ids=ids[-model.base.context_length:]
    emitted=[]
    model.eval()
    for _ in range(max_new_tokens):
        window=torch.tensor([ids[-model.base.context_length:]],dtype=torch.long,
                            device=next(model.base.parameters()).device)
        logits=(model.base(window) if route_name=="base"
                else model(window,route=route_name))
        next_id=int(logits[0,-1].argmax().item())
        if next_id==tokenizer.eos_id:break
        emitted.append(next_id)
        ids.append(next_id)
    return tokenizer.decode(emitted).strip()

def run(base_path,tokenizer_path,approved_path,candidates_path,adapter_path,
        report_path,mode="normal",allow_experimental=False,max_new_tokens=32):
    selected_route=route(mode,allow_experimental)
    inputs=[Path(v).resolve() for v in
            (base_path,tokenizer_path,approved_path,candidates_path,adapter_path)]
    report=Path(report_path).resolve()
    if report in inputs:raise ValueError("report overlaps protected inputs")
    memory=DualMemory(approved_path,candidates_path)
    candidate=[r for r in memory.candidates() if r["status"]=="PENDING"]
    approved=memory.approved()
    if not candidate:raise ValueError("No PENDING candidate probes available")
    if max_new_tokens<1 or max_new_tokens>128:raise ValueError("invalid generation limit")
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(str(base_path),device=device)
    tokenizer=Tokenizer.load(str(tokenizer_path))
    if tokenizer.vocab_size!=base.vocab_size:raise ValueError("vocab mismatch")
    saved=torch.load(adapter_path,map_location="cpu",weights_only=True)
    model=DualAdapterModel(base,rank=int(saved["rank"])).to(device)
    load_experimental(model,adapter_path)
    # Explicit evaluation only: compare against reference answer without
    # treating any candidate response as approved knowledge.
    cases=[]
    for row in candidate[:10]:
        outputs={r:generate(model,tokenizer,row["question"],r,max_new_tokens)
                 for r in ("base","trusted","experimental")}
        cases.append({"candidate_id":row["id"],"source_id":row["source_id"],
                      "question":row["question"],"reference":row["answer"],
                      "outputs":outputs,
                      "exact_match":{r:(s==row["answer"]) for r,s in outputs.items()}})
    protected_cases=[]
    for row in approved[:10]:
        outputs={r:generate(model,tokenizer,row["question"],r,max_new_tokens)
                 for r in ("base","trusted","experimental")}
        protected_cases.append({"approved_id":row["id"],"question":row["question"],
              "reference":row["answer"],
              "outputs":outputs,
              "exact_match":{r:(s==row["answer"]) for r,s in outputs.items()}})
    def accuracy(rows,which):
        if not rows:return None
        return sum(x["exact_match"][which] for x in rows)/len(rows)
    result={"version":"v0.7.5","device":str(device),"selected_runtime_route":selected_route,
        "runtime_experimental_allowed":selected_route=="experimental",
        "evaluation_routes":["base","trusted","experimental"],
        "evaluation_mode":"deterministic greedy free generation; no semantic scoring",
        "candidate_probes":len(cases),"approved_probes":len(protected_cases),
        "candidate_exact_match":{r:accuracy(cases,r) for r in ("base","trusted","experimental")},
        "approved_exact_match":{r:accuracy(protected_cases,r) for r in ("base","trusted","experimental")},
        "quality_pass":None if not protected_cases else
             (accuracy(protected_cases,"experimental")>=accuracy(protected_cases,"base")
              and accuracy(cases,"experimental")>accuracy(cases,"base")),
        "cases":cases,"protected_cases":protected_cases,
        "automatic_promotion":False,"production_integration":False}
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--approved",default="data/approved_v071.jsonl")
    p.add_argument("--candidates",default="data/candidates_v071.jsonl")
    p.add_argument("--adapter",default="results/adapter_sandbox_v073/experimental-adapter.pt")
    p.add_argument("--report",default="results/dual_inference_v075.json")
    p.add_argument("--mode",choices=["normal","experiment"],default="normal")
    p.add_argument("--allow-experimental",action="store_true")
    p.add_argument("--max-new-tokens",type=int,default=32)
    a=p.parse_args()
    result=run(a.base,a.tokenizer,a.approved,a.candidates,a.adapter,a.report,
               a.mode,a.allow_experimental,a.max_new_tokens)
    print(json.dumps({k:v for k,v in result.items() if k not in ("cases","protected_cases")},
                     ensure_ascii=False,indent=2))
if __name__=="__main__":main()

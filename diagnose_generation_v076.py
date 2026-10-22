"""v0.7.6 candidate generation failure diagnostic (read-only).

Evaluate per-route greedy output, EOS behavior, first answer token rank,
and whether a candidate answer begins correctly. No training, promotion or
production runtime modification.
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

PREFIX="人: {question}\nAI: "
ROUTES=("base","trusted","experimental")

def next_logits(model,ids,which):
    x=torch.tensor([ids[-model.base.context_length:]],dtype=torch.long,
                   device=next(model.base.parameters()).device)
    return (model.base(x) if which=="base" else model(x,route=which))[0,-1]

@torch.no_grad()
def probe(model,tokenizer,question,reference,route,max_new_tokens=32):
    if route not in ROUTES:raise ValueError("invalid route")
    prompt_ids=tokenizer.encode(PREFIX.format(question=question),add_bos=True)
    answer_ids=tokenizer.encode(reference,add_eos=True)
    if not prompt_ids or not answer_ids:raise ValueError("empty token sequence")
    ids=prompt_ids[-model.base.context_length:]
    first=next_logits(model,ids,route)
    target=answer_ids[0]
    rank=int((first>first[target]).sum().item())+1
    probability=float(torch.softmax(first,dim=-1)[target].item())
    generated=[]
    stop="token_limit"
    for _ in range(max_new_tokens):
        logits=next_logits(model,ids,route)
        token=int(logits.argmax().item())
        if token==tokenizer.eos_id:
            stop="eos"
            break
        generated.append(token)
        ids.append(token)
    output=tokenizer.decode(generated).strip()
    return {"route":route,"output":output,"reference":reference,
            "exact_match":output==reference.strip(),
            "first_reference_token_rank":rank,
            "first_reference_token_probability":probability,
            "generated_tokens":len(generated),"stop_reason":stop,
            "starts_with_reference":output.startswith(reference.strip()),
            "empty_output":not output}

def run(base_path,tokenizer_path,approved_path,candidate_path,adapter_path,report_path,max_new_tokens=32):
    if not 1<=max_new_tokens<=128:raise ValueError("max_new_tokens must be 1..128")
    inputs={Path(x).resolve() for x in (base_path,tokenizer_path,approved_path,candidate_path,adapter_path)}
    if Path(report_path).resolve() in inputs:raise ValueError("report path overlaps protected input")
    memory=DualMemory(approved_path,candidate_path)
    pending=[r for r in memory.candidates() if r["status"]=="PENDING"]
    approved=memory.approved()
    if not pending:raise ValueError("no PENDING probes")
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(str(base_path),device=device)
    tokenizer=Tokenizer.load(str(tokenizer_path))
    if base.vocab_size!=tokenizer.vocab_size:raise ValueError("vocab mismatch")
    checkpoint=torch.load(adapter_path,map_location="cpu",weights_only=True)
    model=DualAdapterModel(base,rank=int(checkpoint["rank"])).to(device)
    load_experimental(model,adapter_path)
    model.eval()
    def evaluate(rows):
        return [{"id":r["id"],"question":r["question"],"source_id":r["source_id"],
                 "routes":{route:probe(model,tokenizer,r["question"],r["answer"],route,max_new_tokens)
                           for route in ROUTES}} for r in rows]
    result={"version":"v0.7.6","device":str(device),
            "candidate_count":len(pending),"approved_count":len(approved),
            "candidate":evaluate(pending[:10]),"approved":evaluate(approved[:10]),
            "approved_coverage_sufficient":bool(approved),
            "quality_pass":None,"auto_promote":False,
            "interpretation":"diagnostic only; candidate train-set evaluation is not independent generalization"}
    path=Path(report_path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--approved",default="data/approved_v071.jsonl")
    p.add_argument("--candidates",default="data/candidates_v071.jsonl")
    p.add_argument("--adapter",default="results/adapter_sandbox_v073/experimental-adapter.pt")
    p.add_argument("--report",default="results/generation_diagnostic_v076.json")
    p.add_argument("--max-new-tokens",type=int,default=32)
    a=p.parse_args()
    report=run(a.base,a.tokenizer,a.approved,a.candidates,a.adapter,a.report,a.max_new_tokens)
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()

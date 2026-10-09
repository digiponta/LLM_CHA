"""v0.2.16 EOS probability/rank and decoding comparison; no training.

Mirrors LanguageModel.generate temperature/top-k/repetition handling; records
pre-temperature EOS softmax as well as actual decoding-distribution probability.
"""
from __future__ import annotations
import argparse,json,random,statistics
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from conversation_diagnostics_v026 import classify_quality

def next_step(logits, token_ids, eos_id, temperature, top_k, penalty, generator):
    scores=logits.clone()
    if penalty!=1:
        for tid in set(token_ids):
            if scores[tid]>=0:scores[tid]/=penalty
            else:scores[tid]*=penalty
    base_probs=F.softmax(scores,dim=-1)
    eos_raw=float(base_probs[eos_id].item())
    rank=int((scores>scores[eos_id]).sum().item())+1
    if temperature<=0:
        chosen=int(scores.argmax().item())
        selected_eos_probability=float(chosen==eos_id)
    else:
        scaled=scores/temperature
        if top_k and 0<top_k<len(scaled):
            vals,ids=torch.topk(scaled,top_k)
            probs=F.softmax(vals,dim=-1)
            index=int(torch.multinomial(probs,1,generator=generator).item())
            chosen=int(ids[index].item())
            eos_membership=(ids==eos_id).nonzero()
            selected_eos_probability=float(probs[eos_membership[0,0]].item()) if eos_membership.numel() else 0.
        else:
            probs=F.softmax(scaled,dim=-1)
            chosen=int(torch.multinomial(probs,1,generator=generator).item())
            selected_eos_probability=float(probs[eos_id].item())
    return chosen,eos_raw,rank,selected_eos_probability

@torch.inference_mode()
def decode_trace(model,tok,prompt,*,temperature,top_k,seed,max_new_tokens,penalty=1.15):
    prefix=prompt+"\nAI: "
    prefix_ids=tok.encode(prefix)
    ids=prefix_ids[:]
    generator=torch.Generator(device=next(model.parameters()).device).manual_seed(seed)
    trace=[]
    for step in range(max_new_tokens):
        x=torch.tensor([ids[-model.context_length:]],device=next(model.parameters()).device,dtype=torch.long)
        logits=model(x)[0,-1]
        token,prob,rank,decoding_prob=next_step(logits,ids,tok.eos_id,temperature,top_k,penalty,generator)
        trace.append({"step":step+1,"eos_probability":round(prob,6),"eos_rank":rank,
                      "eos_decoding_probability":round(decoding_prob,6),"chosen_eos":token==tok.eos_id})
        ids.append(token)
        if token==tok.eos_id:break
    generated_ids=ids[len(prefix_ids):]
    text=tok.decode(generated_ids,skip_special_tokens=True).strip()
    return {"generated":text,"tokens":len(generated_ids),
            "terminated_by_eos":bool(trace and trace[-1]["chosen_eos"]),
            "eos_first_step_probability":trace[0]["eos_probability"] if trace else None,
            "eos_first_step_rank":trace[0]["eos_rank"] if trace else None,
            "trace":trace}
def aggregate(records):
    n=len(records)
    return {"examples":n,
            "mean_generated_tokens":round(statistics.mean(r["tokens"] for r in records),3),
            "median_generated_tokens":statistics.median(r["tokens"] for r in records),
            "eos_termination_fraction":round(sum(r["terminated_by_eos"] for r in records)/n,4),
            "generic_fraction":round(sum(classify_quality(r["prompt"],r["generated"])["generic"] for r in records)/n,4),
            "short_under_8_chars_fraction":round(sum(len(r["generated"].rstrip("。!?！？ "))<8 for r in records)/n,4),
            "mean_initial_eos_probability":round(statistics.mean(r["eos_first_step_probability"] for r in records),6),
            "initial_eos_rank_1_fraction":round(sum(r["eos_first_step_rank"]==1 for r in records)/n,4)}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--models",nargs="+",default=["model/model-llm-cha-quality-v028.pt","model/model-llm-cha-dialogue-v0211.pt","model/model-llm-cha-generalization-v0212.pt"])
    p.add_argument("--dataset",default="data/dialogue_generalization_v0212/test.jsonl")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--max-rows",type=int,default=30)
    p.add_argument("--max-new-tokens",type=int,default=60)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--output",default="results/eos_decoding_v0216.json")
    a=p.parse_args()
    rows=[json.loads(line) for line in Path(a.dataset).read_text(encoding="utf-8").splitlines() if line.strip()][:a.max_rows]
    if not rows:raise ValueError("No evaluation rows")
    tok=Tokenizer.load(a.tokenizer)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    configs=[("greedy",0,40),("sampling_t07",.7,40),("sampling_t10",1.,40)]
    report={}
    for path in a.models:
        model,_=LanguageModel.load_checkpoint(path,device);model.eval()
        entries={}
        for label,temperature,k in configs:
            records=[]
            for i,row in enumerate(rows):
                item=decode_trace(model,tok,row["user"],temperature=temperature,top_k=k,
                    seed=a.seed+i,max_new_tokens=a.max_new_tokens)
                records.append({"prompt":row["user"],"reference":row["assistant"],**item})
            entries[label]={"summary":aggregate(records),"records":records}
        report[path]=entries
        del model
        if device.type=="cuda":torch.cuda.empty_cache()
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps({"seed":a.seed,"dataset":a.dataset,"models":report},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({m:{k:v["summary"] for k,v in x.items()} for m,x in report.items()},ensure_ascii=False,indent=2))
    print("Full per-step EOS trace:",dest)
if __name__=="__main__":main()

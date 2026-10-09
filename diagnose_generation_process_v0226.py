"""v0.2.26: inspect next-token distributions and greedy trajectories (no training)."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from diagnose_eos_decoding_v0216 import decode_trace
from diagnose_models_v0213 import score_answer
from prepare_context_generalization_v0225 import TRAIN,HOLDOUT,make

ACKS=("そう。","そうですね。","はい。")
def candidate_nll(model,tok,prompt,answer):
    scored=score_answer(model,tok,prompt,answer)
    return round(scored[0]/scored[1],5) if scored else None

@torch.inference_mode()
def trajectory(model,tok,prompt,max_new_tokens=48,top_n=8,penalty=1.15):
    prefix=tok.encode(prompt+"\nAI: ");ids=list(prefix);steps=[]
    device=next(model.parameters()).device
    for step in range(max_new_tokens):
        x=torch.tensor([ids[-model.context_length:]],dtype=torch.long,device=device)
        logits=model(x)[0,-1].clone()
        for tid in set(ids):
            if penalty!=1:
                if logits[tid]>=0:logits[tid]/=penalty
                else:logits[tid]*=penalty
        probs=F.softmax(logits,dim=-1)
        values,indices=torch.topk(probs,min(top_n,probs.shape[-1]))
        next_id=int(indices[0].item())
        steps.append({"step":step+1,"selected_id":next_id,
                      "selected_token":tok.decode([next_id],skip_special_tokens=False),
                      "selected_probability":round(float(values[0].item()),6),
                      "top_tokens":[{"id":int(idx),"token":tok.decode([int(idx)],skip_special_tokens=False),"probability":round(float(prob),6)} for idx,prob in zip(indices.tolist(),values.tolist())],
                      "eos_probability":round(float(probs[tok.eos_id].item()),7)})
        ids.append(next_id)
        if next_id==tok.eos_id:break
    return {"text":tok.decode(ids[len(prefix):],skip_special_tokens=True).strip(),
            "steps":steps,"eos_terminated":bool(steps and steps[-1]["selected_id"]==tok.eos_id)}
def evaluate(model,tok,topics,limit,max_tokens):
    results=[]
    for topic in topics[:limit]:
        row=make(topic);prompt=row["user"];reference=row["assistant"]
        t=trajectory(model,tok,prompt,max_new_tokens=max_tokens)
        alt=[{"text":v,"nll":candidate_nll(model,tok,prompt,v)} for v in (*ACKS,reference)]
        records={"topic":topic[0],"focus":topic[1],"prompt":prompt,"reference":reference,
                 "greedy":t["text"],"trajectory":t["steps"],"eos_terminated":t["eos_terminated"],
                 "teacher_forced_candidates":alt,
                 "reference_vs_short_ack_nll_gain":round(alt[0]["nll"]-alt[-1]["nll"],5) if alt[0]["nll"] is not None and alt[-1]["nll"] is not None else None}
        results.append(records)
    return results
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--models",nargs="+",default=["model/model-llm-cha-context-weighted-v0224.pt","model/model-llm-cha-context-generalization-v0225.pt"])
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="results/generation_process_v0226.json")
    p.add_argument("--max-new-tokens",type=int,default=48)
    p.add_argument("--train-limit",type=int,default=6)
    p.add_argument("--unseen-limit",type=int,default=6)
    a=p.parse_args()
    if min(a.max_new_tokens,a.train_limit,a.unseen_limit)<1:p.error("All limits must be positive")
    tok=Tokenizer.load(a.tokenizer);device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    report={"device":str(device),"description":"Greedy step trace with repetition penalty 1.15; per-token cross entropy of full reference vs generic replies.","models":{}}
    for path in a.models:
        model,_=LanguageModel.load_checkpoint(path,device);model.eval()
        report["models"][path]={"train":evaluate(model,tok,TRAIN,a.train_limit,a.max_new_tokens),
                                "unseen":evaluate(model,tok,HOLDOUT,a.unseen_limit,a.max_new_tokens)}
        del model
        if device.type=="cuda":torch.cuda.empty_cache()
    dst=Path(a.output);dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for model,sets in report["models"].items():
        print("\nMODEL",model)
        for split,rows in sets.items():
            print(" ",split)
            for r in rows:
                top=r["trajectory"][0]["top_tokens"][:3] if r["trajectory"] else []
                print(f"  {r['focus']}: greedy={r['greedy']!r} gain={r['reference_vs_short_ack_nll_gain']} initial_top3={top}")
    print("Detailed step-by-step token probabilities:",dst)
if __name__=="__main__":main()

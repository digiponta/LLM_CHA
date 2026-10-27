"""v0.13.27 B_RAW answer-boundary diagnostics; read-only, no promotion."""
import argparse
import json
from pathlib import Path
import torch
import torch.nn.functional as F

def inspect_boundary(model,tokenizer,question,answer,top_k=10):
    from online_train import USER_PREFIX,AI_PREFIX
    prompt_text=f"{USER_PREFIX}{question}\n{AI_PREFIX}"
    prompt=tokenizer.encode(prompt_text,add_bos=True)
    target=tokenizer.encode(answer,add_eos=True)
    boundary=tokenizer.encode(prompt_text+answer,add_bos=True)
    # BPE encodes pieces independently at train time; concatenation can tokenize differently.
    joint_equals_split=(boundary==prompt+tokenizer.encode(answer))
    device=next(model.parameters()).device
    with torch.no_grad():
        logits=model(torch.tensor([prompt[-model.context_length:]],device=device))[0,-1]
        probs=F.softmax(logits,dim=-1)
        values,indices=probs.topk(min(top_k,len(probs)))
        desired=target[0]
        rank=int((probs>probs[desired]).sum().item()+1)
    return {
        "prompt_text":prompt_text,
        "prompt_last_ids":prompt[-10:],
        "prompt_last_tokens":[tokenizer.decode([x]) for x in prompt[-10:]],
        "bos_at_start":bool(prompt and prompt[0]==tokenizer.bos_id),
        "eos_inside_prompt":tokenizer.eos_id in prompt,
        "answer_first_id":desired,
        "answer_first_decoded":tokenizer.decode([desired]),
        "answer_first_rank":rank,
        "answer_first_probability":float(probs[desired].item()),
        "top_k":[{"id":int(i),"text":tokenizer.decode([int(i)]),"prob":float(v)}
                 for v,i in zip(values.tolist(),indices.tolist())],
        "separate_vs_joint_bpe_equal":joint_equals_split,
        "split_token_count":len(prompt)+len(target)-1,
        "joint_token_count":len(boundary),
        "prompt_token_count":len(prompt),
        "answer_token_count":len(target),
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",type=Path,default=Path("results/prefix_ablation_v01325_B_RAW.pt"))
    p.add_argument("--data",type=Path,default=Path("results/prefix_ablation_v01325_B_RAW.jsonl"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/first_token_boundary_v01327.json"))
    p.add_argument("--limit",type=int,default=16)
    p.add_argument("--top-k",type=int,default=10)
    a=p.parse_args()
    if a.limit<1 or a.top_k<1:p.error("limit and top-k must be positive")
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from unapproved_corpus_learning_v0139 import load_jsonl
    for path in (a.model,a.data,a.tokenizer):
        if not path.exists():p.error(f"missing {path}")
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model,_=LanguageModel.load_checkpoint(str(a.model),device=device)
    model.eval()
    tokenizer=Tokenizer.load(str(a.tokenizer))
    rows=load_jsonl(a.data)[:a.limit]
    results=[]
    for row in rows:
        d=inspect_boundary(model,tokenizer,row["user"],row["assistant"],a.top_k)
        results.append({"subject":row.get("subject"),"knowledge_id":row.get("knowledge_id"),**d})
    summary={"cases":len(results),
             "first_token_rank1":sum(r["answer_first_rank"]==1 for r in results),
             "joint_bpe_mismatch":sum(not r["separate_vs_joint_bpe_equal"] for r in results),
             "bos_missing":sum(not r["bos_at_start"] for r in results),
             "eos_inside_prompt":sum(r["eos_inside_prompt"] for r in results)}
    report={"version":"v0.13.27","evaluation":"TRAINING_PAIRS_NOT_INDEPENDENT",
            "model":str(a.model),"summary":summary,"details":results,
            "production_unchanged":True}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("report:",a.output)

if __name__=="__main__":main()

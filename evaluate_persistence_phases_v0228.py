"""v0.2.28: teacher-forced response phase NLL across checkpoints.

Uses synthetic training-format prompts and teacher responses from v0.2.27.2.
This is a diagnostic, not independent evidence of generalization.
"""
import argparse
import json
from pathlib import Path
import torch
import torch.nn.functional as F
from analyze_initiation_distribution_v02272 import MODELS, CASES, prompts
from model import LanguageModel
from tokenizer_bpe import Tokenizer

def evaluate(model, tokenizer, prompt, response, k=8):
    prompt_ids=tokenizer.encode(prompt,add_bos=True)
    response_ids=tokenizer.encode(response,add_eos=True)
    seq=prompt_ids+response_ids
    if len(seq)>model.context_length+1:
        raise ValueError("sequence truncated; cannot evaluate phases")
    ids=torch.tensor([seq[:-1]],device=next(model.parameters()).device)
    y=torch.tensor(seq[1:],device=ids.device)
    with torch.no_grad():
        logits=model(ids)[0].float()
        losses=F.cross_entropy(logits,y,reduction="none")
    # y predicts seq[position + 1]; first answer occurs at y index len(prompt_ids)-1
    answer_losses=losses[len(prompt_ids)-1:]
    early=answer_losses[:k]
    late=answer_losses[k:]
    return {"first_k_nll":float(early.mean()) if early.numel() else None,
            "later_nll":float(late.mean()) if late.numel() else None,
            "answer_nll":float(answer_losses.mean()),
            "answer_tokens":int(answer_losses.numel())}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--out",default="results/persistence_phases_v0228.jsonl")
    p.add_argument("--k",type=int,default=8)
    p.add_argument("--model",action="append",help="Name=checkpoint")
    a=p.parse_args()
    models=dict(MODELS)
    if a.model:
        models={}
        for x in a.model:
            name,sep,path=x.partition("=")
            if not sep: p.error("use NAME=CHECKPOINT")
            models[name]=path
    tok=Tokenizer.load(a.tokenizer)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows=[]
    for name,path in models.items():
        model,_=LanguageModel.load_checkpoint(path,device=device)
        model.eval()
        if model.vocab_size!=tok.vocab_size:raise ValueError("vocab mismatch")
        for case in CASES:
            for form,pr in prompts(case).items():
                stats=evaluate(model,tok,pr,case["target"],a.k)
                row={"model":name,"topic":case["topic"],"format":form,**stats}
                rows.append(row);print(json.dumps(row,ensure_ascii=False))
    dst=Path(a.out);dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
    print("Saved:",dst)
if __name__=="__main__":main()

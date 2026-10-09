"""v0.2.28.2 raw EOS / continuation probability diagnostic.

No checkpoint changes. Four decoding arms; token-level EOS probability is
reported BEFORE EOS suppression, with argmax rank and actual chosen ID.
"""
import argparse,json
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from analyze_initiation_distribution_v02272 import CASES,prompts
from diagnose_generation_trajectory_v02281 import MODELS

ARMS=("greedy","no_eos_16","no_eos_32","sample_topk")
def select_token(logits, arm, step, eos_id, top_k=40):
    raw_probs=F.softmax(logits.float(),dim=-1)
    eos_prob=float(raw_probs[eos_id].item())
    eos_rank=int((raw_probs>raw_probs[eos_id]).sum().item())+1
    top1=int(raw_probs.argmax().item())
    modified=logits.float().clone()
    forbidden=arm=="no_eos_16" and step<16 or arm=="no_eos_32" and step<32
    if forbidden: modified[eos_id]=-float("inf")
    if arm=="sample_topk":
        ids=torch.topk(modified,min(top_k,modified.numel())).indices
        probs=F.softmax(modified[ids]/0.8,dim=-1)
        chosen=int(ids[torch.multinomial(probs,1)].item())
    else:
        chosen=int(modified.argmax().item())
    return chosen,{"step":step,"eos_probability":eos_prob,"eos_rank":eos_rank,
                    "top1_id":top1,"chosen_id":chosen,"eos_suppressed":forbidden}

@torch.no_grad()
def run(model,tok,prompt,arm,max_new_tokens=64,seed=42):
    torch.manual_seed(seed)
    ids=tok.encode(prompt,add_bos=True)
    generated=[]
    traces=[]
    device=next(model.parameters()).device
    for step in range(max_new_tokens):
        x=torch.tensor([ids[-model.context_length:]],device=device)
        logits=model(x)[0,-1,:].clone()
        # Match existing LanguageModel.generate repetition penalty.
        for token in set(ids):
            if 0<=token<logits.numel():
                if logits[token]>=0: logits[token]/=1.15
                else: logits[token]*=1.15
        chosen,trace=select_token(logits,arm,step,tok.eos_id)
        trace["chosen_text"]=tok.decode([chosen],skip_special_tokens=False)
        trace["top1_text"]=tok.decode([trace["top1_id"]],skip_special_tokens=False)
        traces.append(trace);generated.append(chosen);ids.append(chosen)
        if chosen==tok.eos_id:break
    return {"answer":tok.decode(generated),"generated_tokens":len(generated),
            "eos_generated":bool(generated and generated[-1]==tok.eos_id),
            "trace":traces}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",action="append",help="NAME=CHECKPOINT (repeatable)")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--out",default="results/eos_continuation_v02282.jsonl")
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--seed",type=int,default=42)
    a=p.parse_args()
    if a.max_new_tokens<1:p.error("max-new-tokens must be positive")
    models=dict(MODELS)
    if a.model:
        models={}
        for pair in a.model:
            name,sep,path=pair.partition("=")
            if not sep or not name or not path:p.error("expected NAME=CHECKPOINT")
            models[name]=path
    tok=Tokenizer.load(a.tokenizer)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8") as f:
        for name,path in models.items():
            model,_=LanguageModel.load_checkpoint(path,device=device)
            model.eval()
            if model.vocab_size!=tok.vocab_size:raise ValueError("vocabulary mismatch")
            for case in CASES:
                for form,prompt in prompts(case).items():
                    for arm in ARMS:
                        res=run(model,tok,prompt,arm,a.max_new_tokens,a.seed)
                        rec={"model":name,"case":case["id"],"format":form,
                             "arm":arm,"checkpoint":path,"seed":a.seed,**res}
                        f.write(json.dumps(rec,ensure_ascii=False)+"\n")
                        print(f'{name:12} {case["id"]:6} {form:15} {arm:12} '
                              f'tokens={res["generated_tokens"]:2} eos={res["eos_generated"]} '
                              f'answer={res["answer"]!r}')
    print("Saved:",out)
if __name__=="__main__":main()

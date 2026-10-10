"""v0.2.33.1 controlled response-initiation / continuation curriculum SFT.

Matched optimizer steps across baseline and curriculum arms, starting from
identical frozen checkpoint. Teacher response is never synthesized as truth.
"""
import argparse,copy,json,math,random
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from semantic_memory_expansion_v02328 import load_rows
from prepare_purpose_sft_v02324 import REPLAY
from train_purpose_sft_v02324 import encode_row,loss_rows

def approved_rows(path):
    rows=load_rows(path)
    result=[r for r in rows if r["review_status"]=="APPROVED"]
    if not result:raise ValueError("No approved examples")
    if len({r["prompt"] for r in result})!=len(result):raise ValueError("Duplicate prompts")
    return result

def tokenized(tok,rows,limit):
    out=[]
    for r in rows:
        p=tok.encode(r["prompt"],add_bos=True)
        a=tok.encode(r["answer"],add_eos=True)
        if len(p)+len(a)>limit:raise ValueError(f"Sequence too long: {r['id']}")
        if len(a)<3:raise ValueError(f"Response too short for curriculum: {r['id']}")
        out.append((p,a))
    return out

def masked_lm(model,p,a,device,start=0,stop=None):
    """Only score selected answer target positions; prefix uses gold tokens.

    start=0 targets first answer token. start=k masks first k answer tokens,
    giving the correct k-token prefix as teacher-forced context.
    """
    stop=len(a) if stop is None else stop
    if not 0<=start<stop<=len(a):raise ValueError("Invalid answer target slice")
    ids=p+a
    x=torch.tensor([ids[:-1]],device=device,dtype=torch.long)
    targets=torch.tensor(ids[1:],device=device,dtype=torch.long)
    targets[:len(p)-1+start]=-100
    targets[len(p)-1+stop:]=-100
    logits=model(x)
    return F.cross_entropy(logits.reshape(-1,logits.shape[-1]),targets.reshape(-1),ignore_index=-100)

def learning_objective(model,sample,stage,device):
    p,a=sample
    if stage=="baseline":
        return masked_lm(model,p,a,device)
    if stage=="initiation":
        # First 25% (at least one) and a light full-response anchor.
        n=max(1,math.ceil((len(a)-1)*.25))
        return masked_lm(model,p,a,device,0,n)+.2*masked_lm(model,p,a,device)
    if stage=="continuation":
        # Full answer supervision is retained; also emphasize suffix after gold prefix.
        k=max(1,min(len(a)-2,math.ceil((len(a)-1)*.25)))
        return masked_lm(model,p,a,device,k)+.4*masked_lm(model,p,a,device)
    if stage=="full":
        return masked_lm(model,p,a,device)
    raise ValueError(stage)

def stage_for(step,total):
    ratio=step/total
    if ratio<.30:return "initiation"
    if ratio<.65:return "continuation"
    return "full"

def train_arm(model_path,tok,examples,replay,output,device,steps,seed,lr,head_lr,replay_weight,mode):
    random.seed(seed);torch.manual_seed(seed)
    model,_=LanguageModel.load_checkpoint(model_path,device)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Tokenizer/checkpoint vocab mismatch")
    samples=tokenized(tok,examples,model.context_length)
    replay_pairs=[encode_row(tok,{**r,"id":"replay"},model.context_length) for r in replay]
    opt=torch.optim.AdamW([
      {"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":lr},
      {"params":[model.lm_head.weight],"lr":head_lr}],weight_decay=.01)
    history=[]
    for i in range(steps):
        model.train()
        sample=samples[i%len(samples)]
        stage=stage_for(i,steps) if mode=="curriculum" else "baseline"
        opt.zero_grad(set_to_none=True)
        task=learning_objective(model,sample,stage,device)
        if replay_weight:
            objective=task+replay_weight*loss_rows(model,[replay_pairs[i%len(replay_pairs)]],device)
        else:objective=task
        objective.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
        opt.step()
        history.append({"step":i+1,"stage":stage,"objective_nll":float(task.detach().item())})
        if i==0 or (i+1)%max(1,steps//8)==0:
            print(f"{mode} step={i+1}/{steps} stage={stage} objective={history[-1]['objective_nll']:.4f}")
    # Shared reference diagnostic on full target tokens, NOT a held-out measure.
    model.eval()
    with torch.inference_mode():
        reference=float(torch.stack([masked_lm(model,p,a,device) for p,a in samples]).mean().item())
    model.save_checkpoint(output,epoch=steps,loss=reference,
                          metadata={"version":"v0.2.33.1","mode":mode,"steps":steps,
                                    "base":model_path,"examples":len(examples)})
    return {"steps":steps,"examples":len(examples),"train_reference_nll":reference,"trace":history,"checkpoint":output}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--expansion",default="data/semantic_expansion_v02328.jsonl")
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--baseline-out",default="model/model-llm-cha-curriculum-baseline-v02331.pt")
    p.add_argument("--curriculum-out",default="model/model-llm-cha-curriculum-staged-v02331.pt")
    p.add_argument("--report",default="results/semantic_curriculum_train_v02331.json")
    p.add_argument("--steps",type=int,default=48)
    p.add_argument("--lr",type=float,default=5e-6)
    p.add_argument("--head-lr",type=float,default=1e-6)
    p.add_argument("--replay-weight",type=float,default=.25)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--seed",type=int,default=42)
    a=p.parse_args()
    if a.steps<3 or min(a.lr,a.head_lr)<=0 or a.replay_weight<0:raise ValueError("Invalid training options")
    output_paths=[Path(a.base).resolve(),Path(a.baseline_out).resolve(),Path(a.curriculum_out).resolve()]
    if len(set(output_paths))!=3:raise ValueError("All model paths must differ")
    if any(x.exists() for x in output_paths[1:]) or Path(a.report).exists():
        raise FileExistsError("Refusing to overwrite experiment outputs")
    data=approved_rows(a.expansion)
    tok=Tokenizer.load(a.tokenizer)
    device=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    report={}
    for mode,out in (("baseline",a.baseline_out),("curriculum",a.curriculum_out)):
        Path(out).parent.mkdir(parents=True,exist_ok=True)
        report[mode]=train_arm(a.base,tok,data,REPLAY,out,device,a.steps,a.seed,a.lr,a.head_lr,a.replay_weight,mode)
    dest=Path(a.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",dest,"; no INTERNALIZED promotion")
if __name__=="__main__":main()

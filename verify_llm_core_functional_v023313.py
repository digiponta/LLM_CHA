"""v0.2.33.13: core functional verification without changing model.py.

Checks causal isolation, forward-vs-generate, training gradients, checkpoint
roundtrip, and independent tiny-copy overfit using the original tokenizer.
"""
import argparse,json,random,tempfile
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_purpose_sft_v02324 import encode_row
from input_output_copy_learning_v02339 import prompt

def causal_isolation(model,ids):
    model.eval();device=next(model.parameters()).device
    a=torch.tensor([ids],dtype=torch.long,device=device)
    b=a.clone();mid=len(ids)//2;b[0,-1]=(int(b[0,-1])+17)%model.vocab_size
    with torch.inference_mode():aa=model(a);bb=model(b)
    return float((aa[:,:-1]-bb[:,:-1]).abs().max())

def next_token_consistency(model,ids):
    model.eval();device=next(model.parameters()).device
    x=torch.tensor([ids],dtype=torch.long,device=device)
    with torch.inference_mode():
        full=model(x)[0,-1]
        single=model(torch.tensor([ids[-model.context_length:]],dtype=torch.long,device=device))[0,-1]
        predicted=int(full.argmax())
        generated=model.generate(ids,max_new_tokens=1,temperature=0,eos_id=None,repetition_penalty=1.)
    return {"max_logit_delta":float((full-single).abs().max()),
            "greedy_matches_forward":generated[-1]==predicted}

def gradient_health(model,tok):
    pair=encode_row(tok,{"prompt":prompt("赤い本を机に置きます。"),"answer":"赤い本を机に置きます。"},
                    model.context_length)
    model.train();model.zero_grad(set_to_none=True)
    x,y=pair
    device=next(model.parameters()).device
    logits=model(x[None].to(device))
    loss=F.cross_entropy(logits.reshape(-1,logits.shape[-1]),y.to(device).reshape(-1))
    loss.backward()
    def grad(p):
        if p.grad is None:return None
        return float(p.grad.float().norm().item())
    return {"loss":float(loss.detach()),"embedding_grad":grad(model.embedding.weight),
            "q_grad":grad(model.blocks[0].attention.q_proj.weight),
            "k_grad":grad(model.blocks[0].attention.k_proj.weight),
            "v_grad":grad(model.blocks[0].attention.v_proj.weight),
            "lm_head_grad":grad(model.lm_head.weight)}

def checkpoint_roundtrip(model,ids):
    model.eval()
    device=next(model.parameters()).device
    with torch.inference_mode():before=model(torch.tensor([ids],device=device))
    with tempfile.TemporaryDirectory() as d:
        p=str(Path(d)/"test.pt")
        model.save_checkpoint(p,epoch=1,loss=0.)
        loaded,_=LanguageModel.load_checkpoint(p,device)
        loaded.eval()
        with torch.inference_mode():after=loaded(torch.tensor([ids],device=device))
    return float((before-after).abs().max())

def tiny_overfit(model,tok,steps=150,lr=2e-4,log_every=25):
    if steps<1:raise ValueError("steps")
    # One intentionally tiny example; do not generalize this outcome.
    sample="赤い本を机に置きます。"
    x,y=encode_row(tok,{"prompt":prompt(sample),"answer":sample},model.context_length)
    dev=next(model.parameters()).device;x=x[None].to(dev);y=y.to(dev)
    opt=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=0.)
    records=[]
    for i in range(1,steps+1):
        model.train();opt.zero_grad(set_to_none=True)
        out=model(x)[0]
        loss=F.cross_entropy(out,y)
        loss.backward();opt.step()
        if i==1 or i%log_every==0 or i==steps:
            model.eval()
            with torch.inference_mode():
                logits=model(x)[0]
                mask=y!=-100
                rate=float((logits.argmax(dim=-1)[mask]==y[mask]).float().mean())
                input_ids=tok.encode(prompt(sample),add_bos=True)
                generated=model.generate(input_ids,max_new_tokens=60,temperature=0,
                                         repetition_penalty=1.,eos_id=tok.eos_id)
                actual=tok.decode(generated[len(input_ids):]).strip()
            records.append({"step":i,"teacher_top1":rate,
                            "train_nll":float(F.cross_entropy(logits,y)),
                            "free_text":actual,"exact_copy":actual==sample})
            print(f"step={i} nll={records[-1]['train_nll']:.4f} top1={rate:.3f} copy={actual==sample} text={actual!r}")
            if actual==sample and rate>=.999:break
    return records

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkpoint",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--steps",type=int,default=150)
    p.add_argument("--lr",type=float,default=2e-4)
    p.add_argument("--out",default="results/core_functional_verification_v023313.json")
    a=p.parse_args()
    output=Path(a.out)
    if output.exists():raise FileExistsError(output)
    device=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    torch.manual_seed(42);random.seed(42)
    tok=Tokenizer.load(a.tokenizer)
    model,_=LanguageModel.load_checkpoint(a.checkpoint,device)
    if tok.vocab_size!=model.vocab_size:raise ValueError("vocabulary mismatch")
    ids=tok.encode("文章: 赤い本を机に置きます。\nAI: ",add_bos=True)
    if len(ids)>model.context_length:raise ValueError("too long")
    checks={"causal_max_earlier_logit_delta":causal_isolation(model,ids),
            "incremental_next_token":next_token_consistency(model,ids),
            "gradient":gradient_health(model,tok),
            "checkpoint_max_logit_delta":checkpoint_roundtrip(model,ids)}
    # Gradient inspection does not change parameters; overfit changes this
    # in-memory instance ONLY. The original checkpoint file stays untouched.
    trace=tiny_overfit(model,tok,steps=a.steps,lr=a.lr)
    report={"version":"v0.2.33.13","base":a.checkpoint,"checks":checks,"tiny_overfit":trace,
            "checkpoint_modified":False,"semantic_components_modified":False,
            "limitations":["Single-sample overfit is a pipeline integrity check, not language understanding",
                           "No KV cache is used; generation recomputes full context per token"]}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Checks:",json.dumps(checks,indent=2))
    print("Saved",output)
if __name__=="__main__":main()

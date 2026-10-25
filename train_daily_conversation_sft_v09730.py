"""v0.9.7.30 — opt-in isolated daily-conversation SFT experiment.

Existing checkpoints and Semantic Memory are NEVER overwritten. This is a
small controlled experiment, not a validated production fine-tuning recipe.
"""
import argparse
import json
import random
from pathlib import Path
import torch
import torch.nn.functional as F

from daily_conversation_foundation_v09728 import dataset, audit
from model import LanguageModel
from tokenizer_bpe import Tokenizer

PROTECTED=[
    {"input":"あなたは誰ですか","target":"長門有希。"},
    {"input":"名前を教えてください","target":"長門有希。"},
    {"input":"貴方は誰","target":"長門有希"},
]
def encode_sample(tok, question, answer, context_length):
    prefix=tok.encode("人: "+question+"\nAI: ",add_bos=True)
    response=tok.encode(answer,add_eos=True)
    seq=prefix+response
    if len(seq)>context_length:
        raise ValueError("example exceeds model context length")
    # Next-token CE: prediction for first response token is at len(prefix)-1.
    x=torch.tensor(seq[:-1],dtype=torch.long)
    targets=torch.tensor(seq[1:],dtype=torch.long)
    targets[:len(prefix)-1]=-100
    return x,targets

def example_loss(model,x,y,device):
    logits=model(x.unsqueeze(0).to(device))
    return F.cross_entropy(logits.reshape(-1,logits.size(-1)),
                           y.unsqueeze(0).to(device).reshape(-1),ignore_index=-100)

@torch.no_grad()
def probe(model,tok,question,device,max_tokens=32):
    from chat import generate_reply
    out=generate_reply(model,tok,"人: "+question+"\nAI: ",
                       max_new_tokens=max_tokens,temperature=0.0,
                       top_k=3,repetition_penalty=1.08,seed=42)
    return out.text

def evaluate(model,tok,rows,device):
    model.eval()
    total=0.0
    with torch.no_grad():
        for row in rows:
            x,y=encode_sample(tok,row["input"],row["target"],model.context_length)
            total+=float(example_loss(model,x,y,device))
    return round(total/max(len(rows),1),6)

def run(args):
    data=dataset()
    integrity=audit(data)
    if not integrity["ready_for_controlled_training"]:
        raise ValueError("train / holdout leakage")
    if args.epochs<1 or args.lr<=0 or args.replay<1:
        raise ValueError("epochs and replay must be positive")
    source=Path(args.model).resolve()
    target=Path(args.output).resolve()
    if source==target:
        raise ValueError("output must differ from original checkpoint")
    if target.exists():
        raise FileExistsError("output checkpoint exists; refusing overwrite: "+str(target))
    device=torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    tokenizer=Tokenizer.load(args.tokenizer)
    model,checkpoint=LanguageModel.load_checkpoint(str(source),device=device)
    if model.vocab_size!=tokenizer.vocab_size:
        raise ValueError("checkpoint/tokenizer vocab mismatch")
    train=list(data["train"])+PROTECTED*args.replay
    for r in train+data["holdout"]:
        encode_sample(tokenizer,r["input"],r["target"],model.context_length)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    baselines={q:probe(model,tokenizer,q,device) for q in ("あなたは誰ですか","こんにちは","今日は楽しかった","期待外れだった")}
    before={"holdout_loss":evaluate(model,tokenizer,data["holdout"],device),
            "protected_loss":evaluate(model,tokenizer,PROTECTED,device),
            "generation":baselines}
    report={"status":"DRY_RUN","source":str(source),"output":str(target),
            "device":str(device),"samples":len(train),
            "train_count":len(data["train"]),"holdout_count":len(data["holdout"]),
            "before":before,"training_started":False,
            "source_checkpoint_unchanged":True}
    if not args.train:
        return report
    optimizer=torch.optim.AdamW(model.parameters(),lr=args.lr)
    losses=[]
    for epoch in range(args.epochs):
        model.train()
        random.shuffle(train)
        running=0.0
        for row in train:
            x,y=encode_sample(tokenizer,row["input"],row["target"],model.context_length)
            optimizer.zero_grad(set_to_none=True)
            loss=example_loss(model,x,y,device)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            optimizer.step()
            running+=float(loss.detach())
        losses.append(round(running/len(train),6))
        print(json.dumps({"epoch":epoch+1,"train_loss":losses[-1]},ensure_ascii=False),flush=True)
    after={"holdout_loss":evaluate(model,tokenizer,data["holdout"],device),
           "protected_loss":evaluate(model,tokenizer,PROTECTED,device),
           "generation":{q:probe(model,tokenizer,q,device)
                         for q in ("あなたは誰ですか","こんにちは","今日は楽しかった","期待外れだった")}}
    report.update({"status":"EXPERIMENT_COMPLETE","training_started":True,
                   "epoch_losses":losses,"after":after,
                   "holdout_used_for_training":False})
    target.parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(str(target),epoch=args.epochs,loss=losses[-1],
        metadata={"experiment":"daily-conversation-sft-v0.9.7.30",
                  "source":str(source),"replay":args.replay,
                  "holdout_used_for_training":False})
    return report

def cli():
    p=argparse.ArgumentParser()
    p.add_argument("--model",required=True,help="Existing, untouched model checkpoint")
    p.add_argument("--tokenizer",required=True,help="Matching tokenizer JSON")
    p.add_argument("--output",default="model/model-llm-cha-daily-sft-v09730-experimental.pt")
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--lr",type=float,default=2e-5)
    p.add_argument("--replay",type=int,default=3)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--cpu",action="store_true")
    p.add_argument("--train",action="store_true",help="Explicitly enable training; default is dry-run")
    args=p.parse_args()
    print(json.dumps(run(args),ensure_ascii=False,indent=2))

if __name__=="__main__":
    cli()

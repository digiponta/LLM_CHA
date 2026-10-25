"""Matched four-arm Semantic condition SFT; separate frozen-source checkpoints."""
import argparse, json, random
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_emotion_conditioned_v09735 import training_rows, encode
from train_daily_conversation_sft_v09730 import example_loss, PROTECTED

ARMS=("plain","emotion","strategy","both")
def prompt(q,emotion,strategy,arm):
    fields=[]
    if arm in ("emotion","both"):fields.append("[EMOTION="+emotion+"]")
    if arm in ("strategy","both"):fields.append("[RESPONSE_STRATEGY="+strategy+"]")
    return "\n".join(fields+["人: "+q,"AI: "]) if fields else "人: "+q+"\nAI: "

def examples(data,replay,arm):
    train=[(prompt(r["input"],r["semantic"]["emotion"],r["semantic"]["response_strategy"],arm),r["target"]) for r in data["train"]]
    # Identical protected replay in every arm.
    replay_rows=[("人: "+r["input"]+"\nAI: ",r["target"]) for r in PROTECTED*replay]
    return train+replay_rows

def loss_on(model,tok,rows,arm,device):
    model.eval()
    total=0.0
    with torch.no_grad():
        for r in rows:
            sem=r["semantic"]
            x,y=encode(tok,prompt(r["input"],sem["emotion"],sem["response_strategy"],arm),r["target"],model.context_length)
            total+=float(example_loss(model,x,y,device))
    return round(total/len(rows),6)

def run(a):
    if a.arm not in ARMS:raise ValueError("Unknown arm")
    if a.epochs<1 or a.lr<=0 or a.replay<1:raise ValueError("invalid hyperparameters")
    source=Path(a.model).resolve();dest=Path(a.output).resolve()
    if source==dest or dest.exists():raise ValueError("source/output collision or destination exists")
    data=training_rows()
    device=torch.device("cpu" if a.cpu or not torch.cuda.is_available() else "cuda")
    tok=Tokenizer.load(a.tokenizer)
    model,_=LanguageModel.load_checkpoint(str(source),device=device)
    if tok.vocab_size!=model.vocab_size:raise ValueError("vocabulary mismatch")
    train=examples(data,a.replay,a.arm)
    for p,t in train:encode(tok,p,t,model.context_length)
    before=loss_on(model,tok,data["holdout"],a.arm,device)
    info={"status":"DRY_RUN","arm":a.arm,"train_count":len(data["train"]),
          "holdout_count":len(data["holdout"]),"gradient_examples":len(train),
          "holdout_loss_before":before,"train_ready":False,
          "holdout_used_for_training":False,"source_unchanged":True}
    if not a.train:return info
    random.seed(a.seed);torch.manual_seed(a.seed)
    opt=torch.optim.AdamW(model.parameters(),lr=a.lr)
    losses=[]
    for epoch in range(a.epochs):
        indices=list(range(len(train)))
        random.shuffle(indices)
        model.train();total=0.0
        for i in indices:
            p,t=train[i];x,y=encode(tok,p,t,model.context_length)
            opt.zero_grad(set_to_none=True)
            loss=example_loss(model,x,y,device);loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            opt.step();total+=float(loss.detach())
        losses.append(round(total/len(indices),6))
        print(json.dumps({"arm":a.arm,"epoch":epoch+1,"train_loss":losses[-1]}),flush=True)
    after=loss_on(model,tok,data["holdout"],a.arm,device)
    dest.parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(str(dest),epoch=a.epochs,loss=losses[-1],
      metadata={"experiment":"emotion-factorial-v09738","arm":a.arm,
                "holdout_used_for_training":False,"source":str(source)})
    info.update(status="EXPERIMENT_COMPLETE",training_started=True,
      holdout_loss_after=after,epoch_losses=losses,checkpoint=str(dest))
    return info

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--arm",choices=ARMS,required=True)
    p.add_argument("--model",required=True)
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--lr",type=float,default=2e-5)
    p.add_argument("--replay",type=int,default=3)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--cpu",action="store_true")
    p.add_argument("--train",action="store_true")
    a=p.parse_args()
    print(json.dumps(run(a),ensure_ascii=False,indent=2))
if __name__=="__main__":main()

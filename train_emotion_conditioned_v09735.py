"""Isolated explicit emotion-conditioned SFT experiment.

Unlike v0.9.7.32, semantic labels and strategy appear in actual model
training prompts. Training samples only; holdout stays untouched.
"""
import argparse,json,random
from pathlib import Path
import torch
from daily_conversation_foundation_v09728 import dataset as original
from semantic_daily_conversation_v09732 import build
from emotion_aware_dialogue_v09733 import detect
from train_daily_conversation_sft_v09730 import example_loss,probe,evaluate,PROTECTED

def semantic_prompt(question,emotion,strategy):
    return f"[EMOTION={emotion}]\n[DIALOGUE_ACT=EMOTION_REPORT]\n[RESPONSE_STRATEGY={strategy}]\n人: {question}\nAI: "

def training_rows():
    d=build()
    original_holdout={r["input"] for r in original()["holdout"]}
    assert not original_holdout.intersection(r["input"] for r in d["train"])
    assert not {r["input"] for r in d["train"]}.intersection(r["input"] for r in d["holdout"])
    return d

def encode(tok,prompt,completion,context):
    prefix=tok.encode(prompt,add_bos=True)
    seq=prefix+tok.encode(completion,add_eos=True)
    if len(seq)>context:raise ValueError("sequence exceeds context length")
    x=torch.tensor(seq[:-1],dtype=torch.long)
    y=torch.tensor(seq[1:],dtype=torch.long)
    y[:len(prefix)-1]=-100
    return x,y

def run(a):
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    source=Path(a.model).resolve()
    target=Path(a.output).resolve()
    if source==target or target.exists():raise ValueError("original/output path collision or output already exists")
    if a.epochs<1 or a.lr<=0 or a.replay<1:raise ValueError("invalid training hyperparameters")
    d=training_rows()
    device=torch.device("cpu" if a.cpu or not torch.cuda.is_available() else "cuda")
    tok=Tokenizer.load(a.tokenizer)
    model,_=LanguageModel.load_checkpoint(str(source),device=device)
    if tok.vocab_size!=model.vocab_size:raise ValueError("tokenizer/model vocabulary mismatch")
    examples=[]
    for r in d["train"]:
        sem=r["semantic"]
        examples.append((semantic_prompt(r["input"],sem["emotion"],sem["response_strategy"]),r["target"]))
    for r in PROTECTED*a.replay:
        examples.append(("人: "+r["input"]+"\nAI: ",r["target"]))
    for prompt,completion in examples:
        encode(tok,prompt,completion,model.context_length)
    before=evaluate(model,tok,d["holdout"],device)
    result={"status":"DRY_RUN","device":str(device),"train_count":len(d["train"]),
            "holdout_count":len(d["holdout"]),"total_gradient_examples":len(examples),
            "baseline_holdout_loss":before,"training_started":False,
            "holdout_used_for_training":False,"source_unchanged":True}
    if not a.train:return result
    random.seed(a.seed)
    torch.manual_seed(a.seed)
    optimizer=torch.optim.AdamW(model.parameters(),lr=a.lr)
    losses=[]
    for epoch in range(a.epochs):
        random.shuffle(examples)
        model.train()
        epoch_loss=0.0
        for prompt,completion in examples:
            x,y=encode(tok,prompt,completion,model.context_length)
            optimizer.zero_grad(set_to_none=True)
            loss=example_loss(model,x,y,device)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            optimizer.step()
            epoch_loss+=float(loss.detach())
        losses.append(round(epoch_loss/len(examples),6))
        print(json.dumps({"epoch":epoch+1,"loss":losses[-1]}),flush=True)
    model.eval()
    # Holdout loss is measured in the same conditioned format as training;
    # old v09730 unconditioned NLL is not directly comparable.
    conditional_total=0.0
    with torch.no_grad():
        for r in d["holdout"]:
            sem=r["semantic"]
            x,y=encode(tok,semantic_prompt(r["input"],sem["emotion"],sem["response_strategy"]),r["target"],model.context_length)
            conditional_total+=float(example_loss(model,x,y,device))
    result.update({"status":"EXPERIMENT_COMPLETE","training_started":True,
                   "epoch_losses":losses,
                   "conditioned_holdout_loss":round(conditional_total/len(d["holdout"]),6)})
    target.parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(str(target),epoch=a.epochs,loss=losses[-1],
        metadata={"experiment":"emotion-conditioned-sft-v09735",
                  "holdout_used_for_training":False,"source":str(source)})
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",required=True)
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--output",default="model/model-llm-cha-emotion-conditioned-v09735.pt")
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--lr",type=float,default=2e-5)
    p.add_argument("--replay",type=int,default=3)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--cpu",action="store_true")
    p.add_argument("--train",action="store_true")
    a=p.parse_args()
    print(json.dumps(run(a),ensure_ascii=False,indent=2))
if __name__=="__main__":main()

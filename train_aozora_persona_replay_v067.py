#!/usr/bin/env python3
"""v0.6.7: Persona replay + Aozora next-token training from the original v94.
Never modifies the original checkpoint, Semantic Memory or chat runtime.
"""
import argparse
import json
import random
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_aozora_continued_v065 import read_corpus, split_by_work, make_dataset
from train_nagato_full import lm_loss, evaluate as evaluate_lm
from online_train import ConversationDataset, masked_loss, load_replay_pairs

def guard(base, output, report):
    locations=[Path(x).resolve() for x in (base, output, report)]
    if len(set(locations)) != 3: raise ValueError("source/output/report must differ")
    for dest in locations[1:]:
        if dest.exists(): raise FileExistsError(dest)

def load_persona(path):
    p=Path(path)
    if not p.exists(): raise FileNotFoundError(p)
    if p.suffix.lower()==".jsonl":
        pairs=[]
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            item=json.loads(line)
            u, a=item.get("user"), item.get("assistant")
            if isinstance(u,str) and u.strip() and isinstance(a,str) and a.strip():
                pairs.append((u.strip(),a.strip()))
    else:
        pairs=load_replay_pairs(p)
    pairs=list(dict.fromkeys(pairs))
    if not pairs: raise ValueError("persona replay file has no valid conversations")
    return pairs

@torch.no_grad()
def persona_nll(model, loader, device):
    model.eval()
    total=0.0; count=0
    for x,y,mask in loader:
        x,y,mask=x.to(device),y.to(device),mask.to(device)
        logits=model(x)
        losses=torch.nn.functional.cross_entropy(logits.reshape(-1,logits.size(-1)),
               y.reshape(-1),reduction="none").reshape_as(y)
        total+=float((losses*mask).sum().item())
        count+=int(mask.sum().item())
    return total/max(count,1)

def identity_answer(model, tok):
    prompt=tok.encode("人: あなたは誰ですか？\nAI: ")
    predicted=model.generate(prompt,max_new_tokens=32,temperature=0,top_k=None,
                              repetition_penalty=1.0,eos_id=tok.eos_id)
    return tok.decode(predicted[len(prompt):])

def train(args):
    if not 0 < args.persona_ratio < 1 or args.epochs < 1 or args.max_steps < 1:
        raise ValueError("persona_ratio must be (0,1); epochs and max_steps > 0")
    if not args.dry_run:
        guard(args.base_model,args.output,args.report)
    random.seed(42);torch.manual_seed(42)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(args.tokenizer)
    model,_=LanguageModel.load_checkpoint(args.base_model,device=device)
    if model.vocab_size!=tok.vocab_size: raise ValueError("tokenizer/model mismatch")
    literature, heldout, held=split_by_work(read_corpus(args.corpus), args.validation_work)
    block=min(args.block_size,model.context_length)
    lit_ds,_=make_dataset(literature,tok,block,block)
    val_ds,_=make_dataset(heldout,tok,block,block)
    persona=load_persona(args.persona_data)
    random.shuffle(persona)
    # Keep some replay pairs unseen in training for an independent replay check.
    split=max(1,min(len(persona)-1,int(len(persona)*0.15)))
    if len(persona)<8: raise ValueError("at least 8 unique persona pairs required")
    persona_val=persona[:split];persona_train=persona[split:]
    persona_ds=ConversationDataset(persona_train,tok,block)
    pval_ds=ConversationDataset(persona_val,tok,block)
    liter_loader=DataLoader(lit_ds,batch_size=args.batch_size,shuffle=True)
    held_loader=DataLoader(val_ds,batch_size=args.batch_size)
    persona_loader=DataLoader(persona_ds,batch_size=args.batch_size,shuffle=True)
    pval_loader=DataLoader(pval_ds,batch_size=args.batch_size)
    baseline={"heldout_nll":evaluate_lm(model,held_loader,device)[0],
              "persona_holdout_nll":persona_nll(model,pval_loader,device),
              "identity_answer":identity_answer(model,tok)}
    print("Before:",json.dumps(baseline,ensure_ascii=False))
    if args.dry_run:
        print(f"DRY RUN: GPU={device}, literature_windows={len(lit_ds)}, persona_train={len(persona_train)}, persona_holdout={len(persona_val)}")
        return
    optimizer=torch.optim.AdamW(model.parameters(),lr=args.learning_rate)
    history=[]
    for epoch in range(1,args.epochs+1):
        li=iter(liter_loader); pi=iter(persona_loader)
        total_p=0;total_l=0
        for step in range(args.max_steps):
            use_p=random.random()<args.persona_ratio
            if use_p:
                try: batch=next(pi)
                except StopIteration: pi=iter(persona_loader);batch=next(pi)
                x,y,mask=(t.to(device) for t in batch)
            else:
                try: batch=next(li)
                except StopIteration: li=iter(liter_loader);batch=next(li)
                x,y=(t.to(device) for t in batch)
            model.train();optimizer.zero_grad(set_to_none=True)
            loss=masked_loss(model,x,y,mask) if use_p else lm_loss(model,x,y)
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            optimizer.step()
            if use_p:total_p+=1
            else:total_l+=1
        metrics={"epoch":epoch,"persona_steps":total_p,"literature_steps":total_l,
                 "heldout_nll":evaluate_lm(model,held_loader,device)[0],
                 "persona_holdout_nll":persona_nll(model,pval_loader,device),
                 "identity_answer":identity_answer(model,tok)}
        history.append(metrics);print(json.dumps(metrics,ensure_ascii=False))
    report={"version":"v0.6.7","base_model":args.base_model,"model_output":args.output,
            "validation_work":held,"persona_ratio":args.persona_ratio,
            "persona_train_pairs":len(persona_train),"persona_val_pairs":len(persona_val),
            "before":baseline,"epochs":history,"persona_regression_verified":False,
            "semantic_memory_modified":False}
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(str(dest),optimizer=optimizer,epoch=args.epochs,
                          loss=history[-1]["heldout_nll"],
                          metadata={"experiment":"v0.6.7","replay_ratio":args.persona_ratio})
    target=Path(args.report);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-model",default="model/model-llm-try-nagato-chat-v94.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--corpus",default="data/aozora_v064/aozora_semantic_corpus.jsonl")
    p.add_argument("--persona-data",default="data/nagato_chat.jsonl")
    p.add_argument("--validation-work",default="1567")
    p.add_argument("--output",default="model/model-llm-cha-aozora-replay-v067.pt")
    p.add_argument("--report",default="results/aozora_replay_v067.json")
    p.add_argument("--persona-ratio",type=float,default=0.5)
    p.add_argument("--epochs",type=int,default=2)
    p.add_argument("--max-steps",type=int,default=160)
    p.add_argument("--batch-size",type=int,default=4)
    p.add_argument("--block-size",type=int,default=128)
    p.add_argument("--learning-rate",type=float,default=5e-6)
    p.add_argument("--dry-run",action="store_true")
    args=p.parse_args()
    if args.batch_size<1 or args.block_size<8 or args.learning_rate<=0:p.error("invalid training settings")
    train(args)
if __name__=="__main__":main()

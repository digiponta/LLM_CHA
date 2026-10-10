"""v0.2.33.14 controlled 2x2 LR x replay ablation for copy learning.

All arms start from the same checkpoint and get identical training sample
order and 20*epochs copy updates. Outputs are isolated. No DSS/Bridge edits.
"""
import argparse,json,random
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_purpose_sft_v02324 import encode_row,loss_rows
from prepare_purpose_sft_v02324 import REPLAY
from input_output_copy_learning_v02339 import TRAIN_TEXTS,VAL_TEXTS,TESTS,prompt,rows,validate_splits

ARMS=(("low_replay",5e-6,True),("high_replay",2e-4,True),
      ("low_no_replay",5e-6,False),("high_no_replay",2e-4,False))
def plan(epochs,seed):
    rng=random.Random(seed)
    orders=[]
    for _ in range(epochs):
        order=list(range(len(TRAIN_TEXTS)));rng.shuffle(order)
        # Replay draw is made regardless of arm, to keep plan identical.
        orders.append([(idx,rng.randrange(len(REPLAY))) for idx in order])
    return orders

def summarize_copy(model,tok,texts,max_new_tokens):
    model.eval();data=[]
    for kind,text in texts:
        ids=tok.encode(prompt(text),add_bos=True)
        with torch.inference_mode():
            out=model.generate(ids,max_new_tokens=max_new_tokens,eos_id=tok.eos_id,
                               temperature=0,repetition_penalty=1.)
        candidate=tok.decode(out[len(ids):]).strip()
        data.append({"kind":kind,"input":text,"generated":candidate,
                     "exact_match":candidate==text})
    return data

def train_arm(base,tok,pairs,replay,validation,orders,device,arm,lr,enable_replay,args):
    model,_=LanguageModel.load_checkpoint(base,device)
    model.train()
    opt=torch.optim.AdamW([
      {"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":lr},
      {"params":[model.lm_head.weight],"lr":lr*args.head_scale}],
      weight_decay=args.weight_decay)
    trace=[];candidate=None;best=float("inf");best_epoch=0
    for ep,order in enumerate(orders,1):
        model.train()
        for idx,rep_idx in order:
            opt.zero_grad(set_to_none=True)
            objective=loss_rows(model,[pairs[idx]],device)
            if enable_replay:
                objective=objective+args.replay_weight*loss_rows(model,[replay[rep_idx]],device)
            objective.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            opt.step()
        model.eval()
        with torch.inference_mode():
            train_nll=float(loss_rows(model,pairs,device))
            val_nll=float(loss_rows(model,validation,device))
            replay_nll=float(loss_rows(model,replay,device))
        trace.append({"epoch":ep,"train_nll":train_nll,"val_nll":val_nll,
                      "replay_nll":replay_nll})
        print(f"{arm} epoch={ep} train={train_nll:.4f} val={val_nll:.4f} replay={replay_nll:.4f}")
        if val_nll<best:
            best=val_nll;best_epoch=ep
            candidate={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    model.load_state_dict(candidate)
    subset=[("seen",t) for t in TRAIN_TEXTS[:4]]+TESTS
    free=summarize_copy(model,tok,subset,args.max_new_tokens)
    # Also explicitly verify whether replayed greeting answers survived.
    from dialogue_guided_generation_v02322 import CheckpointGenerator
    greetings=[]
    for user in ("こんにちは","ありがとう","あなたは誰ですか"):
        ids=tok.encode(f"人: {user}\nAI: ",add_bos=True)
        with torch.inference_mode():
            generated=model.generate(ids,max_new_tokens=30,temperature=0,
                                     repetition_penalty=1.05,eos_id=tok.eos_id)
        greetings.append({"prompt":user,"response":tok.decode(generated[len(ids):]).strip()})
    return model,{"arm":arm,"lr":lr,"replay":enable_replay,"best_epoch":best_epoch,
                  "best_val_nll":best,"history":trace,"copy":free,"retention":greetings,
                  "copy_exact_by_kind":{k:sum(x["exact_match"] for x in free if x["kind"]==k)
                                        for k in ("seen","unseen","novel_combination","length")}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--epochs",type=int,default=8)
    p.add_argument("--head-scale",type=float,default=.2)
    p.add_argument("--replay-weight",type=float,default=.25)
    p.add_argument("--weight-decay",type=float,default=.01)
    p.add_argument("--max-new-tokens",type=int,default=110)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--out-dir",default="results/copy_ablation_v023314")
    p.add_argument("--model-dir",default="model/copy_ablation_v023314")
    a=p.parse_args()
    if a.epochs<1 or a.head_scale<=0 or a.replay_weight<0 or a.weight_decay<0 or a.max_new_tokens<1:
        raise ValueError("Invalid parameters")
    validate_splits()
    out_dir=Path(a.out_dir);model_dir=Path(a.model_dir)
    if out_dir.exists() or model_dir.exists():raise FileExistsError("Refusing to overwrite experiment directories")
    random.seed(a.seed);torch.manual_seed(a.seed)
    dev=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    tok=Tokenizer.load(a.tokenizer)
    baseline,_=LanguageModel.load_checkpoint(a.base,dev)
    if tok.vocab_size!=baseline.vocab_size:raise ValueError("vocabulary mismatch")
    training=[encode_row(tok,row,baseline.context_length) for row in rows(TRAIN_TEXTS)]
    validation=[encode_row(tok,row,baseline.context_length) for row in rows(VAL_TEXTS)]
    replay=[encode_row(tok,{**r,"id":"replay"},baseline.context_length) for r in REPLAY]
    orders=plan(a.epochs,a.seed)
    out_dir.mkdir(parents=True);model_dir.mkdir(parents=True)
    summaries=[]
    for name,lr,has_replay in ARMS:
        torch.manual_seed(a.seed)
        model,result=train_arm(a.base,tok,training,replay,validation,orders,dev,name,lr,has_replay,a)
        target=model_dir/(name+".pt")
        model.save_checkpoint(str(target),epoch=result["best_epoch"],loss=result["best_val_nll"],
            metadata={"experiment":"v0.2.33.14","arm":name})
        (out_dir/(name+".json")).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        summaries.append({key:result[key] for key in ("arm","lr","replay","best_epoch","best_val_nll","copy_exact_by_kind","retention")})
        print(name,"copy_exact_by_kind",result["copy_exact_by_kind"])
    (out_dir/"summary.json").write_text(json.dumps({"version":"v0.2.33.14",
       "controlled":"same checkpoint, sample orders, epoch count; only LR and Replay changed",
       "limitations":["4 arms on 1 seed; no statistical confidence or independent holdout",
                       "Best checkpoint selected by validation NLL, not copying success",
                       "Replay provides additional computation in replay arms",
                       "Different learning rates do not imply equivalent optimization paths"],
       "results":summaries,"promotion_eligible":False},ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",out_dir/"summary.json")
if __name__=="__main__":main()

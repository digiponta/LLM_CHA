"""v0.2.33.15: checkpoint-selection comparison on the SAME training trajectory.

Compare best-validation, final-epoch, and best-seen-copy checkpoints.
No changes to DSS, memory, bridge or existing checkpoints.
"""
import argparse,copy,json,random
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_purpose_sft_v02324 import encode_row,loss_rows
from prepare_purpose_sft_v02324 import REPLAY
from input_output_copy_learning_v02339 import TRAIN_TEXTS,VAL_TEXTS,TESTS,prompt,rows,validate_splits

def snapshot(model):
    return {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}

def generate_copy(model,tok,s,max_new_tokens=120):
    ids=tok.encode(prompt(s),add_bos=True)
    with torch.inference_mode():
        result=model.generate(ids,max_new_tokens=max_new_tokens,eos_id=tok.eos_id,
                              temperature=0,top_k=20,repetition_penalty=1.)
    tail=result[len(ids):]
    # Record both exact token copy (including EOS) and exact string copy.
    expected=tok.encode(s,add_eos=True)
    return {"text":tok.decode(tail).strip(),"exact_text":tok.decode(tail).strip()==s,
            "exact_tokens":tail==expected,"generated_ids":len(tail)}

def select_checkpoint_records(trace):
    if not trace:raise ValueError("No epoch records")
    best_val=min(trace,key=lambda r:(r["val_nll"],r["epoch"]))
    best_seen=min(trace,key=lambda r:(-r["seen_copy_count"],r["val_nll"],r["epoch"]))
    return {"best_validation":best_val["epoch"],
            "best_seen_copy":best_seen["epoch"],
            "final_epoch":trace[-1]["epoch"]}

def run(args):
    validate_splits()
    result_dir=Path(args.result_dir);model_dir=Path(args.model_dir)
    if result_dir.exists() or model_dir.exists():
        raise FileExistsError("Output directory already exists; supply fresh paths")
    if not 0<=args.replay_weight or args.epochs<=0 or args.lr<=0 or args.head_lr<=0:
        raise ValueError("Invalid learning parameters")
    random.seed(args.seed);torch.manual_seed(args.seed)
    dev=torch.device("cuda" if args.device=="auto" and torch.cuda.is_available() else
                     "cpu" if args.device=="auto" else args.device)
    tok=Tokenizer.load(args.tokenizer)
    model,checkpoint=LanguageModel.load_checkpoint(args.base,dev)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Tokenizer mismatch")
    train=[encode_row(tok,r,model.context_length) for r in rows(TRAIN_TEXTS)]
    val=[encode_row(tok,r,model.context_length) for r in rows(VAL_TEXTS)]
    replay=[encode_row(tok,{**r,"id":"replay"},model.context_length) for r in REPLAY]
    opt=torch.optim.AdamW([
        {"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":args.lr},
        {"params":[model.lm_head.weight],"lr":args.head_lr}],weight_decay=args.weight_decay)
    seen=[("seen",s) for s in TRAIN_TEXTS[:4]]
    snapshots={};history=[]
    for epoch in range(1,args.epochs+1):
        model.train()
        idxs=list(range(len(train)));random.shuffle(idxs)
        for i in idxs:
            opt.zero_grad(set_to_none=True)
            loss=loss_rows(model,[train[i]],dev)
            if replay and args.replay_weight:
                loss=loss+args.replay_weight*loss_rows(model,[random.choice(replay)],dev)
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            opt.step()
        model.eval()
        with torch.inference_mode():
            train_nll=float(loss_rows(model,train,dev))
            val_nll=float(loss_rows(model,val,dev))
            replay_nll=float(loss_rows(model,replay,dev))
        seen_results=[generate_copy(model,tok,s,args.max_new_tokens) for _,s in seen]
        count=sum(int(x["exact_text"]) for x in seen_results)
        history.append({"epoch":epoch,"train_nll":train_nll,"val_nll":val_nll,
                        "replay_nll":replay_nll,"seen_copy_count":count})
        snapshots[epoch]=snapshot(model)
        print(f"epoch={epoch:02d} train={train_nll:.4f} val={val_nll:.4f} replay={replay_nll:.4f} seen={count}/4")
    selected=select_checkpoint_records(history)
    cases=seen+TESTS
    result_dir.mkdir(parents=True);model_dir.mkdir(parents=True)
    comparisons={}
    for label,epoch in selected.items():
        model.load_state_dict(snapshots[epoch])
        model.eval()
        answers=[]
        for kind,text in cases:
            answers.append({"kind":kind,"input":text,**generate_copy(model,tok,text,args.max_new_tokens)})
        by_kind={}
        for kind in ("seen","unseen","novel_combination","length"):
            group=[x for x in answers if x["kind"]==kind]
            by_kind[kind]={"exact_text":sum(x["exact_text"] for x in group),
                           "total":len(group),"exact_tokens":sum(x["exact_tokens"] for x in group)}
        model_path=model_dir/(label+".pt")
        model.save_checkpoint(str(model_path),epoch=epoch,loss=history[epoch-1]["val_nll"],
            metadata={"experiment":"v0.2.33.15","selection":label,"selected_epoch":epoch,
                      "experimental_only":True})
        comparisons[label]={"epoch":epoch,"metrics":history[epoch-1],
                            "copy_by_kind":by_kind,"cases":answers,
                            "checkpoint":str(model_path)}
        print(label,"epoch=",epoch,"copy=",by_kind)
    report={"version":"v0.2.33.15","base":args.base,"lr":args.lr,
            "head_lr":args.head_lr,"replay_weight":args.replay_weight,
            "epochs":args.epochs,"history":history,"selected":selected,
            "comparisons":comparisons,
            "notes":["best_seen_copy selection uses four training examples and must not be treated as holdout performance",
                     "best_validation is chosen by validation teacher-forced NLL",
                     "same optimization run for all three checkpoint choices",
                     "no promotion to production runtime"]}
    (result_dir/"summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",result_dir/"summary.json")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--epochs",type=int,default=8)
    p.add_argument("--lr",type=float,default=2e-4)
    p.add_argument("--head-lr",type=float,default=4e-5)
    p.add_argument("--replay-weight",type=float,default=0.)
    p.add_argument("--weight-decay",type=float,default=.01)
    p.add_argument("--max-new-tokens",type=int,default=110)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--result-dir",default="results/checkpoint_selection_v023315")
    p.add_argument("--model-dir",default="model/checkpoint_selection_v023315")
    run(p.parse_args())
if __name__=="__main__":main()

"""v0.2.33.16 generalized copy: deterministic compositional splits.

No semantic component changes. Validation selects checkpoint; test evaluated once.
"""
import argparse,hashlib,json,random
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_purpose_sft_v02324 import encode_row,loss_rows
from input_output_copy_learning_v02339 import prompt

COLORS=["赤い","青い","白い","黒い","黄色い","緑の","紫の","茶色い"]
ITEMS=["本","箱","紙","袋","傘","冊子","ノート","封筒"]
PLACES=["机","棚","玄関","入口","窓際","台","引き出し","かご"]
VERBS=["置きます","運びます","入れます","移します"]
def corpus():
    # Fixed lexical blocks, full combinations generated without randomness.
    return [f"{c}{x}を{p}に{v}。" for c in COLORS for x in ITEMS for p in PLACES for v in VERBS]

def split_corpus(seed=42,train_count=480,val_count=80,test_count=80):
    entries=corpus();rng=random.Random(seed);rng.shuffle(entries)
    if min(train_count,val_count,test_count)<1 or sum((train_count,val_count,test_count))>len(entries):
        raise ValueError("Invalid split sizes")
    tr=entries[:train_count];va=entries[train_count:train_count+val_count]
    te=entries[train_count+val_count:train_count+val_count+test_count]
    assert not(set(tr)&set(va) or set(tr)&set(te) or set(va)&set(te))
    return tr,va,te

def rows(texts):
    return [{"id":hashlib.sha256(s.encode("utf8")).hexdigest()[:12],
             "prompt":prompt(s),"answer":s} for s in texts]

def exact_generate(model,tok,text,max_tokens=80):
    ids=tok.encode(prompt(text),add_bos=True)
    with torch.inference_mode():
        out=model.generate(ids,max_new_tokens=max_tokens,eos_id=tok.eos_id,
                           temperature=0,repetition_penalty=1.)
    got=tok.decode(out[len(ids):]).strip()
    return got==text,got

def measure(model,tok,samples,max_tokens):
    model.eval()
    matches=[]
    for text in samples:
        passed,generated=exact_generate(model,tok,text,max_tokens)
        matches.append({"input":text,"generated":generated,"exact":passed})
    return {"exact":sum(x["exact"] for x in matches),"total":len(matches),
            "accuracy":sum(x["exact"] for x in matches)/len(matches),"samples":matches}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="model/model-llm-cha-general-copy-v023316.pt")
    p.add_argument("--report",default="results/generalized_copy_v023316.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--train-count",type=int,default=480)
    p.add_argument("--val-count",type=int,default=80)
    p.add_argument("--test-count",type=int,default=80)
    p.add_argument("--epochs",type=int,default=8)
    p.add_argument("--lr",type=float,default=5e-5)
    p.add_argument("--head-lr",type=float,default=1e-5)
    p.add_argument("--max-new-tokens",type=int,default=80)
    a=p.parse_args()
    if a.epochs<1 or a.lr<=0 or a.head_lr<=0 or a.max_new_tokens<1:
        raise ValueError("Invalid training parameters")
    if Path(a.output).exists() or Path(a.report).exists():
        raise FileExistsError("Experiment output already exists")
    tr,va,te=split_corpus(a.seed,a.train_count,a.val_count,a.test_count)
    random.seed(a.seed);torch.manual_seed(a.seed)
    device=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else
                        "cpu" if a.device=="auto" else a.device)
    tok=Tokenizer.load(a.tokenizer)
    model,_=LanguageModel.load_checkpoint(a.base,device)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Tokenizer mismatch")
    training=[encode_row(tok,row,model.context_length) for row in rows(tr)]
    validation=[encode_row(tok,row,model.context_length) for row in rows(va)]
    optimizer=torch.optim.AdamW([
        {"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":a.lr},
        {"params":[model.lm_head.weight],"lr":a.head_lr}],weight_decay=.01)
    best=float("inf");best_epoch=None;best_state=None;history=[]
    # Held-out test is never used for selection, tuning or early stopping.
    for epoch in range(1,a.epochs+1):
        order=list(range(len(training)));random.shuffle(order)
        model.train();total=0.
        for j in order:
            optimizer.zero_grad(set_to_none=True)
            loss=loss_rows(model,[training[j]],device)
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            optimizer.step();total+=float(loss.detach())
        model.eval()
        with torch.inference_mode():val_nll=float(loss_rows(model,validation,device))
        # Select by validation NLL, not by test outcomes.
        if val_nll<best:
            best=val_nll;best_epoch=epoch
            best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
        print(f"epoch={epoch:02d} train_nll={total/len(order):.4f} val_nll={val_nll:.4f}")
        history.append({"epoch":epoch,"train_nll":total/len(order),"val_nll":val_nll})
    model.load_state_dict(best_state);model.eval()
    val_metrics=measure(model,tok,va,a.max_new_tokens)
    test_metrics=measure(model,tok,te,a.max_new_tokens)
    train_probe=measure(model,tok,tr[:40],a.max_new_tokens)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(a.output,epoch=best_epoch,loss=best,
       metadata={"experiment":"v0.2.33.16","task":"compositional_copy","experimental_only":True})
    report={"version":"v0.2.33.16","seed":a.seed,"counts":{"train":len(tr),"val":len(va),"test":len(te)},
            "best_epoch":best_epoch,"best_val_nll":best,"history":history,
            "train_probe":train_probe,"validation":val_metrics,"test":test_metrics,
            "limitations":["Test sentences are unseen combinations of seen vocabulary and templates",
                           "Model selection is solely by validation teacher-forced NLL",
                           "No unconstrained prose or wholly unseen vocabulary in this test",
                           "Single seed; requires repetition for confidence"],
            "promotion_eligible":False}
    r=Path(a.report);r.parent.mkdir(parents=True,exist_ok=True)
    r.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Best epoch={best_epoch} validation_copy={val_metrics['exact']}/{len(va)} "
          f"test_copy={test_metrics['exact']}/{len(te)} "
          f"train_probe={train_probe['exact']}/40")
    print("Saved",a.output,a.report)
if __name__=="__main__":main()

"""v0.13.58.30: isolated corrective SFT; dry-run by default.

Requires assistant-reviewed 8-item v0.13.58.29 dataset, verifies digest,
never changes base checkpoint, never treats training prompts as a holdout.
Explicit --run --acknowledge-experiment is needed to train.
"""
import argparse,hashlib,json,random
from pathlib import Path
from audit_offline_replay_v0135810 import read_file
from aligned_replay_examples_v0135816 import make_aligned_examples
from train_japanese_foundation_v01344 import masked_ce

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def preflight(source,audit_path,base,tokenizer,output_dir,steps,batch_size,lr):
    if output_dir.exists():raise FileExistsError(output_dir)
    if steps<1 or batch_size<1 or not 0<lr<=0.001:raise ValueError("invalid hyperparameters")
    audit=json.loads(audit_path.read_text(encoding="utf-8-sig"))
    if audit.get("version")!="v0.13.58.29" or audit.get("status")!="ASSISTANT_CONTENT_REVIEW_RECORDED" or not audit.get("approved_for_candidate_dataset"):
        raise ValueError("review audit missing or invalid")
    if sha(source)!=audit.get("source_sha256"):raise ValueError("reviewed source sha mismatch")
    if audit.get("training_performed") is not False or audit.get("human_reviewer_attested") is not False:
        raise ValueError("audit state unexpected")
    rows=[json.loads(line) for line in source.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if len(rows)!=8 or len({x["user"] for x in rows})!=8:raise ValueError("expected eight unique questions")
    for row in rows:
        if row.get("approved") is not True or row.get("reviewer")!="ChatGPT GPT-6" or row.get("approval_scope")!="candidate_corrective_sft_only":
            raise ValueError("unreviewed row")
        if row.get("training_authorized") is not False or row.get("production_promotion_allowed") is not False:
            raise ValueError("invalid record authorization")
    lines=read_file(source)
    if not base.is_file() or not tokenizer.is_file():raise FileNotFoundError("model/tokenizer missing")
    report={"version":"v0.13.58.30","status":"DRY_RUN_ONLY","source_sha256":sha(source),
       "review_audit_sha256":sha(audit_path),"base_sha256":sha(base),"tokenizer_sha256":sha(tokenizer),
       "reviewed_dialogues":len(lines),"steps":steps,"batch_size":batch_size,"lr":lr,
       "assistant_only_loss":True,"train_prompts_are_evaluation_exposed":True,
       "training_performed":False,"human_review_approved":False,"independent_holdout_verified":False,
       "production_promotion_allowed":False}
    return lines,report

def run(args):
    lines,report=preflight(args.source,args.audit,args.base,args.tokenizer,args.output_dir,args.steps,args.batch_size,args.lr)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not args.run:return report
    if not args.acknowledge_experiment:raise ValueError("--acknowledge-experiment is required")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    random.seed(args.seed);torch.manual_seed(args.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(args.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer=Tokenizer.load(str(args.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(args.base),device=device)
    if tokenizer.vocab_size!=model.vocab_size:raise ValueError("tokenizer/model vocab mismatch")
    dataset=make_aligned_examples([("conversation",s) for s in lines],tokenizer,model.context_length,assistant_only=True)
    gen=torch.Generator().manual_seed(args.seed)
    loader=torch.utils.data.DataLoader(dataset,batch_size=args.batch_size,shuffle=True,generator=gen)
    optimizer=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=0.01)
    history=[];iteration=iter(loader)
    for step in range(1,args.steps+1):
        try: x,y,mask=next(iteration)
        except StopIteration:
            iteration=iter(loader);x,y,mask=next(iteration)
        model.train()
        x,y,mask=x.to(device),y.to(device),mask.to(device)
        optimizer.zero_grad(set_to_none=True)
        loss=masked_ce(model,x,y,mask);loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
        optimizer.step()
        history.append({"step":step,"loss":float(loss.detach().cpu()),"supervised_tokens":int(mask.sum().item())})
        if step==1 or step==args.steps or step%20==0:
            print(json.dumps(history[-1],ensure_ascii=False))
    args.output_dir.mkdir(parents=True,exist_ok=False)
    candidate=args.output_dir/"candidate_corrective.pt"
    model.save_checkpoint(str(candidate),epoch=1,loss=history[-1]["loss"],
        metadata={"experiment":"CORRECTIVE_SFT_V0135830","approval":"EXPERIMENTAL_ONLY","production_unchanged":True})
    report.update({"status":"EXPLORATORY_CORRECTIVE_TRAINING_COMPLETE","training_performed":True,
       "checkpoint_sha256":sha(candidate),"history":history,
       "observed_supervised_tokens":sum(h["supervised_tokens"] for h in history)})
    (args.output_dir/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("report:",args.output_dir/"report.json")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/corrective_sft_reviewed_v0135829.jsonl"))
    p.add_argument("--audit",type=Path,default=Path("results/corrective_review_v0135829.json"))
    p.add_argument("--base",type=Path,default=Path("model/model-llm-try-nagato-chat-v94.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output-dir",type=Path,default=Path("results/corrective_sft_v0135830"))
    p.add_argument("--steps",type=int,default=40)
    p.add_argument("--batch-size",type=int,default=4)
    p.add_argument("--lr",type=float,default=3e-6)
    p.add_argument("--seed",type=int,default=135830)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-experiment",action="store_true")
    a=p.parse_args();run(a)
if __name__=="__main__":main()

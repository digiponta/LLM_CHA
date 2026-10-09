"""v0.2.32.6: run real SFT on approved Semantic Memory records.

One-shot foreground worker; each invocation produces a separate candidate,
never overwrites the baseline. TRAINING->VALIDATING is NOT INTERNALIZED.
"""
import argparse,datetime,json,random,uuid
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_purpose_sft_v02324 import encode_row,loss_rows
from prepare_purpose_sft_v02324 import REPLAY,PURPOSE_JA
from staged_semantic_internalization_v02325 import (
    read_memory,training_queue,transition,approve,
)

def make_pair(record):
    if record["teacher_status"]!="APPROVED" or not record.get("approved_answer"):
        raise ValueError("Approved answer required")
    c=record["context"];topic=c.get("topic") or "未確定"
    purposes=c.get("purposes") or []
    purpose=" → ".join(PURPOSE_JA.get(p,p) for p in purposes) if purposes else "未確定"
    utterance=c["user_input"]
    return {"id":record["id"],"prompt":f"話題: {topic}\n目的: {purpose}\n人: {utterance}\nAI: ",
            "answer":record["approved_answer"]}

def write_json(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    tmp.replace(p)

def run(args):
    if args.epochs<1 or args.lr<=0 or args.head_lr<=0 or args.replay_weight<0:
        raise ValueError("Invalid training parameters")
    queued=training_queue(args.memory)
    if not queued:raise ValueError("No approved MEMORIZED records. Review teacher answers first.")
    # No mutation until the tokenizer, base model and all dataset rows are validated.
    for asset in (args.model,args.tokenizer):
        if not Path(asset).is_file():raise FileNotFoundError(asset)
    device=torch.device("cuda" if args.device=="auto" and torch.cuda.is_available() else
                        "cpu" if args.device=="auto" else args.device)
    random.seed(args.seed);torch.manual_seed(args.seed)
    tok=Tokenizer.load(args.tokenizer)
    model,_=LanguageModel.load_checkpoint(args.model,device)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Checkpoint/tokenizer mismatch")
    examples=[make_pair(r) for r in queued]
    train=[encode_row(tok,x,model.context_length) for x in examples]
    replay=[encode_row(tok,{**r,"id":"replay"},model.context_length) for r in REPLAY]
    dest=Path(args.output)
    if dest.resolve()==Path(args.model).resolve():raise ValueError("Refusing to overwrite base checkpoint")
    if dest.exists():raise FileExistsError(f"Candidate already exists: {dest}")
    job_path=Path(args.job_report)
    if job_path.exists():raise FileExistsError(f"Job report already exists: {job_path}")
    ids=[r["id"] for r in queued]
    job={"job_id":uuid.uuid4().hex,"status":"RUNNING","started_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "source_checkpoint":args.model,"candidate_checkpoint":str(dest),"memory_ids":ids,
         "examples":len(train),"epochs_requested":args.epochs,"metrics":[]}
    write_json(job_path,job)
    # Each record transition is persisted. If error occurs, mark participating
    # records FAILED; failed checkpoint is not promoted.
    try:
        for key in ids:transition(args.memory,key,"TRAINING")
        opt=torch.optim.AdamW([
            {"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":args.lr},
            {"params":[model.lm_head.weight],"lr":args.head_lr}],weight_decay=0.01)
        for epoch in range(1,args.epochs+1):
            model.train();order=list(train);random.shuffle(order);total=0.0
            for pair in order:
                opt.zero_grad(set_to_none=True)
                task=loss_rows(model,[pair],device)
                if args.replay_weight:
                    objective=task+args.replay_weight*loss_rows(model,[random.choice(replay)],device)
                else:objective=task
                objective.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
                opt.step();total+=float(task.detach().item())
            job["metrics"].append({"epoch":epoch,"train_nll":total/len(order)})
            print(f"epoch={epoch:02d} train_nll={total/len(order):.4f}")
            write_json(job_path,job)
        # Save once after requested epochs; validation is intentionally separate.
        model.save_checkpoint(str(dest),epoch=args.epochs,loss=job["metrics"][-1]["train_nll"],
            metadata={"version":"v0.2.32.6","job_id":job["job_id"],
                      "semantic_memory_ids":ids,"training_type":"reviewed_response_only",
                      "base_checkpoint":args.model})
        for key in ids:transition(args.memory,key,"VALIDATING",checkpoint=str(dest))
        job["status"]="AWAITING_VALIDATION"
        job["finished_at"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
        write_json(job_path,job)
        print("Candidate:",dest,"Job:",job_path,"Status: AWAITING_VALIDATION")
        return job
    except BaseException as e:
        job["status"]="FAILED";job["error"]=repr(e)
        write_json(job_path,job)
        for key in ids:
            try:
                record=read_memory(args.memory)[key]
                if record["lifecycle"]=="TRAINING":
                    transition(args.memory,key,"FAILED",evidence={"reason":repr(e)})
            except Exception:pass
        raise

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="command",required=True)
    review=sub.add_parser("review",help="Approve a reviewed teacher answer")
    review.add_argument("--memory",default="data/dss_semantic_memory_v02325.jsonl")
    review.add_argument("--id",required=True)
    review.add_argument("--answer",required=True)
    queue=sub.add_parser("queue",help="Show approved pending rows")
    queue.add_argument("--memory",default="data/dss_semantic_memory_v02325.jsonl")
    work=sub.add_parser("train",help="Synchronous backend training of candidate model")
    work.add_argument("--memory",default="data/dss_semantic_memory_v02325.jsonl")
    work.add_argument("--model",default="model/model-llm-cha-response-quality-v0221.pt")
    work.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    work.add_argument("--output",default="model/model-llm-cha-semantic-candidate-v02326.pt")
    work.add_argument("--job-report",default="results/semantic_backend_job_v02326.json")
    work.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    work.add_argument("--epochs",type=int,default=8)
    work.add_argument("--lr",type=float,default=5e-6)
    work.add_argument("--head-lr",type=float,default=1e-6)
    work.add_argument("--replay-weight",type=float,default=.25)
    work.add_argument("--seed",type=int,default=42)
    args=p.parse_args()
    if args.command=="review":
        r=approve(args.memory,args.id,args.answer)
        print(f"APPROVED id={r['id']} answer={r['approved_answer']}")
    elif args.command=="queue":
        print(json.dumps([{"id":r["id"],"topic":r["context"].get("topic"),
                           "answer":r["approved_answer"]} for r in training_queue(args.memory)],
                         ensure_ascii=False,indent=2))
    else:run(args)
if __name__=="__main__":main()

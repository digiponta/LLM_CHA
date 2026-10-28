"""v0.13.58.34: stage one literature answer, then expand it.

Uses immutable last-accepted v0.13.58.33 checkpoint and checks all 7
previously accepted prompt/answer pairs every round. Each stage is bounded.
Only exact matches pass; this is NOT a semantic correctness metric.
"""
import argparse,hashlib,json,random
from pathlib import Path
from dialogue_format_v0135817 import dialogue_for
from aligned_replay_examples_v0135816 import make_aligned_examples
from train_japanese_foundation_v01344 import masked_ce
from train_iterative_corrective_v0135832 import generate,exact_match
from train_corrective_sft_v0135830 import preflight as reviewed_preflight

START_SHA="29611e29db7c1d56b09c297468a7f79e8855b992447a9ba0ae6b674eaf00e6c7"
SEVEN=("correct-talk-001","correct-cpu-002","correct-persona-003","correct-tired-008",
       "protect-identity-005","protect-greeting-006","protect-quantum-007")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(stages,reviewed,previous_report,start,output,max_rounds,steps_per_round):
    if output.exists():raise FileExistsError(output)
    if not (1<=max_rounds<=20 and 1<=steps_per_round<=100):raise ValueError("invalid budget")
    old=json.loads(previous_report.read_text(encoding="utf-8-sig"))
    if old.get("version")!="v0.13.58.33" or old.get("status")!="PARTIAL_TARGETS_UNMET":
        raise ValueError("expected v0.13.58.33 partial result")
    if sha(start)!=START_SHA or sha(start)!=old.get("latest_accepted_sha256"):
        raise ValueError("start checkpoint provenance mismatch")
    accepted=old.get("accepted_checkpoints",[])
    if not accepted or accepted[-1].get("sha256")!=sha(start):raise ValueError("not latest accepted checkpoint")
    if set(SEVEN)!=set(accepted[-1].get("verified_ids",[])):raise ValueError("seven protected/exact records not verified")
    rows=[json.loads(s) for s in reviewed.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    refs={r["id"]:r for r in rows}
    if not set(SEVEN).issubset(refs):raise ValueError("missing protected records")
    if sha(reviewed)!=old.get("source_sha256"):raise ValueError("reviewed source changed")
    st=[json.loads(s) for s in stages.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    if [x.get("id") for x in st]!=["literature-stage-1","literature-stage-2"]:raise ValueError("stage order")
    for s in st:
        if s.get("approved") is not True or s.get("reviewer")!="ChatGPT GPT-6" or s.get("review_type")!="assistant_content_review":raise ValueError("not reviewed")
        if s.get("user")!="吾輩は猫であるについて教えて":raise ValueError("unexpected stage prompt")
    if not st[1]["assistant"].startswith(st[0]["assistant"]):raise ValueError("stage2 must extend stage1")
    return st,[refs[k] for k in SEVEN]

def run(a):
    stages,protected=validate(a.stages,a.reviewed,a.previous_report,a.start,a.output_dir,a.max_rounds,a.steps_per_round)
    report={"version":"v0.13.58.34","status":"DRY_RUN_ONLY","start_sha256":sha(a.start),
            "stages_sha256":sha(a.stages),"stages":[x["id"] for x in stages],
            "protected_ids":list(SEVEN),"rounds_per_stage":a.max_rounds,
            "steps_per_round":a.steps_per_round,"quality_rule":"EXACT_STRING",
            "training_performed":False,"production_promotion_allowed":False,
            "independent_holdout_verified":False,"semantic_quality_verified":False}
    if not a.run:
        print(json.dumps(report,ensure_ascii=False,indent=2));return report
    if not a.acknowledge_experiment:raise ValueError("explicit experiment acknowledgement required")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    random.seed(a.seed);torch.manual_seed(a.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(a.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(a.start),device=device)
    if tok.vocab_size!=model.vocab_size:raise ValueError("vocabulary mismatch")
    baseline={r["id"]:r["assistant"] for r in protected}
    def regressions():
        return [r["id"] for r in protected if not exact_match(generate(model,tok,r,a.max_new_tokens),baseline[r["id"]])]
    if regressions():raise ValueError("starting checkpoint failed previous seven answers")
    a.output_dir.mkdir(parents=True,exist_ok=False)
    last_checkpoint=a.start;events=[];accepted=[];updates=0;status="ALL_STAGES_EXACT"
    for stage in stages:
        before=generate(model,tok,stage,a.max_new_tokens)
        success=exact_match(before,stage["assistant"])
        for round_no in range(0 if success else 1,a.max_rounds+1):
            if round_no:
                # Every step includes the active literature stage and all 7 protected records.
                dialogue=[dialogue_for(stage["user"],stage["assistant"])]
                dialogue += [dialogue_for(r["user"],r["assistant"]) for r in protected]
                data=make_aligned_examples([("conversation",d) for d in dialogue],tok,model.context_length,assistant_only=True)
                x,y,m=data.tensors
                opt=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=0.01) if round_no==1 else opt
                for _ in range(a.steps_per_round):
                    model.train();opt.zero_grad(set_to_none=True)
                    for j in range(len(x)):
                        loss=masked_ce(model,x[j:j+1].to(device),y[j:j+1].to(device),m[j:j+1].to(device))
                        (loss/len(x)).backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step();updates+=1
            answer=generate(model,tok,stage,a.max_new_tokens)
            fails=regressions()
            event={"stage":stage["id"],"round":round_no,"answer":answer,
                "exact":exact_match(answer,stage["assistant"]),"regressions":fails,"updates":updates}
            events.append(event);print(json.dumps(event,ensure_ascii=False))
            if fails:
                status="STOPPED_REGRESSION";break
            if event["exact"]:
                checkpoint=a.output_dir/(stage["id"]+".pt")
                model.save_checkpoint(str(checkpoint),epoch=1,
                    metadata={"experiment":"STAGED_LITERATURE_V0135834","production_promotion_allowed":False})
                accepted.append({"stage":stage["id"],"path":str(checkpoint),"sha256":sha(checkpoint)})
                last_checkpoint=checkpoint;success=True;break
        if status=="STOPPED_REGRESSION":break
        if not success:
            status="STOPPED_STAGE_LIMIT";break
    report.update({"status":status,"training_performed":updates>0,"updates":updates,
                   "events":events,"accepted_checkpoints":accepted,
                   "latest_accepted_checkpoint":str(last_checkpoint),
                   "latest_accepted_sha256":sha(last_checkpoint)})
    (a.output_dir/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":status,"updates":updates,"accepted_stages":[s["stage"] for s in accepted]},ensure_ascii=False))
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stages",type=Path,default=Path("data/literature_stages_reviewed_v0135834.jsonl"))
    p.add_argument("--reviewed",type=Path,default=Path("data/corrective_sft_reviewed_v0135829.jsonl"))
    p.add_argument("--previous-report",type=Path,default=Path("results/iterative_corrective_v0135833/report.json"))
    p.add_argument("--start",type=Path,default=Path("results/iterative_corrective_v0135833/accepted_correct-tired-008.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output-dir",type=Path,default=Path("results/staged_literature_v0135834"))
    p.add_argument("--max-rounds",type=int,default=5)
    p.add_argument("--steps-per-round",type=int,default=10)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--lr",type=float,default=2e-6)
    p.add_argument("--seed",type=int,default=135834)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-experiment",action="store_true")
    run(p.parse_args())
if __name__=="__main__":main()

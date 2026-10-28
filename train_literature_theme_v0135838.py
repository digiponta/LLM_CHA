"""v0.13.58.38 — isolated, sequential literary-theme corrective training.
No promotion, strict text-integrity checks, rollback on failed stage,
SHA provenance, all previously accepted answers protected.
"""
import argparse,hashlib,json,random
from pathlib import Path
from dialogue_format_v0135817 import dialogue_for
from aligned_replay_examples_v0135816 import make_aligned_examples
from train_japanese_foundation_v01344 import masked_ce
from train_iterative_corrective_v0135832 import generate,exact_match
from text_integrity_gate_v0135837 import defects,validate_training_records

START_SHA="308ea13fbb6b57bafb056d203a215d7a0a932f75321ce8ce1603a095616e0529"
ORDER=("theme-stage-1","theme-stage-2","theme-stage-3")
FACT_IDS=("lit-author","lit-narrator","lit-title")
PREVIOUS_IDS=("correct-talk-001","correct-cpu-002","correct-persona-003",
              "correct-tired-008","protect-identity-005","protect-greeting-006",
              "protect-quantum-007")
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load_jsonl(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8-sig",errors="strict").splitlines() if s.strip()]
def validate(a):
    if a.output_dir.exists():raise FileExistsError(a.output_dir)
    if not (1<=a.rounds<=20 and 1<=a.steps_per_round<=100 and 1<=a.max_new_tokens<=256):
        raise ValueError("invalid budget")
    report=json.loads(a.previous_report.read_text(encoding="utf-8-sig"))
    if report.get("version")!="v0.13.58.36" or report.get("status")!="PARTIAL_FACTS_UNMET":
        raise ValueError("unexpected previous report")
    if sha(a.start)!=START_SHA or report.get("latest_sha256")!=START_SHA:
        raise ValueError("start checkpoint SHA mismatch")
    if sha(a.facts)!=report.get("facts_sha256"):raise ValueError("fact source hash mismatch")
    if set(x["id"] for x in report.get("accepted",[]))!=set(FACT_IDS):
        raise ValueError("accepted fact set mismatch")
    reviewed={x["id"]:x for x in load_jsonl(a.reviewed)}
    facts={x["id"]:x for x in load_jsonl(a.facts)}
    if not set(PREVIOUS_IDS).issubset(reviewed) or not set(FACT_IDS).issubset(facts):
        raise ValueError("missing protected sources")
    history=json.loads(a.stage1_report.read_text(encoding="utf-8-sig"))
    if history.get("version")!="v0.13.58.34" or history.get("status")!="STOPPED_STAGE_LIMIT":
        raise ValueError("invalid stage-1 report")
    prior_stages=load_jsonl(a.prior_stages)
    if sha(a.prior_stages)!=history.get("stages_sha256") or prior_stages[0].get("id")!="literature-stage-1":
        raise ValueError("stage-1 provenance mismatch")
    protected=[reviewed[i] for i in PREVIOUS_IDS]+[{"id":"literature-stage-1",
       "user":prior_stages[0]["user"],"assistant":prior_stages[0]["assistant"]}]+[facts[i] for i in FACT_IDS]
    stages=load_jsonl(a.stages)
    if [s.get("id") for s in stages]!=list(ORDER):raise ValueError("invalid stage order")
    if any(s.get("user")!="『吾輩は猫である』はどんな作品？" or
        s.get("approved") is not True or s.get("reviewer")!="ChatGPT GPT-6" or
        s.get("training_scope")!="experimental_only" for s in stages):
        raise ValueError("invalid stage review")
    clean,bad=validate_training_records(protected+stages)
    if bad:raise ValueError("unsafe text: "+repr(bad))
    return stages,protected

def run(a):
    stages,protected=validate(a)
    result={"version":"v0.13.58.38","status":"DRY_RUN_ONLY",
        "start_sha256":sha(a.start),"stages_sha256":sha(a.stages),
        "protected_ids":[p["id"] for p in protected],"stages":[s["id"] for s in stages],
        "round_limit":a.rounds,"steps_per_round":a.steps_per_round,
        "training_performed":False,"semantic_quality_verified":False,
        "independent_holdout_verified":False,"production_promotion_allowed":False}
    if not a.run:
        print(json.dumps(result,ensure_ascii=False,indent=2));return result
    if not a.acknowledge_experiment:raise ValueError("--acknowledge-experiment required")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    random.seed(a.seed);torch.manual_seed(a.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(a.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(a.tokenizer));model,_=LanguageModel.load_checkpoint(str(a.start),device=device)
    if tok.vocab_size!=model.vocab_size:raise ValueError("vocab mismatch")
    def regressions():
        return [p["id"] for p in protected if not exact_match(generate(model,tok,p,a.max_new_tokens),p["assistant"])]
    bad=regressions()
    if bad:raise ValueError("starting checkpoint fails protected answers: "+repr(bad))
    a.output_dir.mkdir(parents=True,exist_ok=False)
    last=a.start;events=[];accepted=[];total=0;failed=None;status="ALL_STAGES_EXACT"
    for stage in stages:
        success=False
        for rnd in range(a.rounds+1):
            if rnd:
                dialogues=[dialogue_for(stage["user"],stage["assistant"])]
                dialogues += [dialogue_for(p["user"],p["assistant"]) for p in protected]
                samples=make_aligned_examples([("conversation",x) for x in dialogues],tok,model.context_length,assistant_only=True)
                xs,ys,ms=samples.tensors
                if rnd==1:optimizer=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=.01)
                for _ in range(a.steps_per_round):
                    model.train();optimizer.zero_grad(set_to_none=True)
                    for j in range(len(xs)):
                        loss=masked_ce(model,xs[j:j+1].to(device),ys[j:j+1].to(device),ms[j:j+1].to(device))
                        (loss/len(xs)).backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
                    optimizer.step();total+=1
            answer=generate(model,tok,stage,a.max_new_tokens)
            issues=defects(answer)
            regression=regressions()
            event={"stage":stage["id"],"round":rnd,"answer":answer,"text_issues":issues,
                   "exact":not issues and exact_match(answer,stage["assistant"]),
                   "regressions":regression,"total_steps":total}
            events.append(event);print(json.dumps(event,ensure_ascii=False))
            if regression:
                status="STOPPED_PROTECTED_REGRESSION";failed=stage["id"];break
            if event["exact"]:
                target=a.output_dir/(stage["id"]+".pt")
                model.save_checkpoint(str(target),epoch=1,
                   metadata={"experiment":"LITERATURE_THEME_V0135838","production_promotion_allowed":False})
                accepted.append({"id":stage["id"],"path":str(target),"sha256":sha(target)})
                last=target;success=True;break
        if not success:
            if status=="ALL_STAGES_EXACT":status="STOPPED_STAGE_LIMIT"
            failed=stage["id"];break
    result.update({"status":status,"training_performed":total>0,"total_steps":total,
       "events":events,"accepted":accepted,"failed_stage":failed,
       "latest_accepted":str(last),"latest_sha256":sha(last)})
    (a.output_dir/"report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":status,"accepted":[r["id"] for r in accepted],"failed":failed,"total_steps":total},ensure_ascii=False))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stages",type=Path,default=Path("data/literature_theme_stages_v0135838.jsonl"))
    p.add_argument("--reviewed",type=Path,default=Path("data/corrective_sft_reviewed_v0135829.jsonl"))
    p.add_argument("--facts",type=Path,default=Path("data/literature_fact_corrections_v0135836.jsonl"))
    p.add_argument("--previous-report",type=Path,default=Path("results/literature_facts_v0135836/report.json"))
    p.add_argument("--stage1-report",type=Path,default=Path("results/staged_literature_v0135834/report.json"))
    p.add_argument("--prior-stages",type=Path,default=Path("data/literature_stages_reviewed_v0135834.jsonl"))
    p.add_argument("--start",type=Path,default=Path("results/literature_facts_v0135836/lit-title.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output-dir",type=Path,default=Path("results/literature_theme_v0135838"))
    p.add_argument("--rounds",type=int,default=5)
    p.add_argument("--steps-per-round",type=int,default=10)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--lr",type=float,default=2e-6)
    p.add_argument("--seed",type=int,default=135838)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-experiment",action="store_true")
    run(p.parse_args())
if __name__=="__main__":main()

"""v0.13.58.36: sequential literature facts with checkpoint rollback.

Uses v0.13.58.34 Stage-1 success, protects prior seven answers and
the Stage-1 literature answer. Raw exact-match is a conservative proxy;
never claims independent generalization or human attestation.
"""
import argparse,hashlib,json,random
from pathlib import Path
from dialogue_format_v0135817 import dialogue_for
from aligned_replay_examples_v0135816 import make_aligned_examples
from train_japanese_foundation_v01344 import masked_ce
from train_iterative_corrective_v0135832 import generate,exact_match
from train_staged_literature_v0135834 import validate as validate_stage,SEVEN,sha as digest

START_SHA="7e23f8164ad8e8ed9b5dfcfb177a5244ecbcd51c956fb30787bd3d5bf8128469"
ORDER=("lit-author","lit-narrator","lit-theme","lit-title")
def validate(a):
    if a.output_dir.exists():raise FileExistsError(a.output_dir)
    if not 1<=a.rounds<=20 or not 1<=a.steps_per_round<=100 or not 1<=a.max_new_tokens<=256:raise ValueError("invalid budget")
    if digest(a.start)!=START_SHA:raise ValueError("start SHA mismatch")
    stages,protected=validate_stage(a.stages,a.reviewed,a.previous_report,a.start,a.output_dir,a.rounds,a.steps_per_round)
    candidates=[json.loads(x) for x in a.facts.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    if [r.get("id") for r in candidates]!=list(ORDER):raise ValueError("wrong order")
    for r in candidates:
        if r.get("approved") is not True or r.get("reviewer")!="ChatGPT GPT-6" or r.get("review_type")!="assistant_content_review" or r.get("approval_scope")!="experimental_sft_candidate_only":raise ValueError("unapproved fact")
        if r.get("human_reviewer_attested") is not False or r.get("production_promotion_allowed") is not False:raise ValueError("unsafe fact record")
    protected.append({"id":"literature-stage-1","user":stages[0]["user"],"assistant":stages[0]["assistant"]})
    return candidates,protected
def run(a):
    facts,protected=validate(a)
    result={"version":"v0.13.58.36","status":"DRY_RUN_ONLY",
       "start_sha256":digest(a.start),"facts_sha256":digest(a.facts),
       "targets":list(ORDER),"protected_ids":[x["id"] for x in protected],
       "steps_per_round":a.steps_per_round,"round_limit":a.rounds,
       "training_performed":False,"quality_rule":"EXACT_REVIEWED_TEXT",
       "human_review_attested":False,"independent_holdout_verified":False,
       "production_promotion_allowed":False}
    if not a.run:
        print(json.dumps(result,ensure_ascii=False,indent=2));return result
    if not a.acknowledge_experiment:raise ValueError("--acknowledge-experiment required")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    random.seed(a.seed);torch.manual_seed(a.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(a.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(a.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(a.start),device=device)
    if model.vocab_size!=tok.vocab_size:raise ValueError("vocab mismatch")
    def failures():
        return [r["id"] for r in protected if not exact_match(generate(model,tok,r,a.max_new_tokens),r["assistant"])]
    if failures():raise ValueError("starting model failed protected 8")
    a.output_dir.mkdir(parents=True,exist_ok=False)
    last=a.start;accepted=[];unmet=[];events=[];steps=0
    for fact in facts:
        accepted_this=exact_match(generate(model,tok,fact,a.max_new_tokens),fact["assistant"])
        for rnd in range(0 if accepted_this else 1,a.rounds+1):
            if rnd:
                dialogues=[dialogue_for(fact["user"],fact["assistant"])]
                dialogues += [dialogue_for(p["user"],p["assistant"]) for p in protected]
                samples=make_aligned_examples([("conversation",d) for d in dialogues],tok,model.context_length,assistant_only=True)
                xs,ys,ms=samples.tensors
                if rnd==1:opt=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=.01)
                for _ in range(a.steps_per_round):
                    model.train();opt.zero_grad(set_to_none=True)
                    for j in range(len(xs)):
                        loss=masked_ce(model,xs[j:j+1].to(device),ys[j:j+1].to(device),ms[j:j+1].to(device))
                        (loss/len(xs)).backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step();steps+=1
            answer=generate(model,tok,fact,a.max_new_tokens);bad=failures()
            event={"id":fact["id"],"round":rnd,"answer":answer,"exact":exact_match(answer,fact["assistant"]),
                   "regressions":bad,"total_steps":steps}
            events.append(event);print(json.dumps(event,ensure_ascii=False))
            if bad:
                result["status"]="STOPPED_PROTECTED_REGRESSION";break
            if event["exact"]:
                output=a.output_dir/(fact["id"]+".pt")
                model.save_checkpoint(str(output),epoch=1,
                    metadata={"experiment":"LITERATURE_FACTS_V0135836","production_promotion_allowed":False})
                accepted.append({"id":fact["id"],"path":str(output),"sha256":digest(output)})
                protected.append(fact);last=output;accepted_this=True;break
        if result["status"]=="STOPPED_PROTECTED_REGRESSION":break
        if not accepted_this:
            unmet.append(fact["id"])
            # restore the previous accepted weights, then continue to next item
            model,_=LanguageModel.load_checkpoint(str(last),device=device)
    if result["status"]!="STOPPED_PROTECTED_REGRESSION":
        result["status"]="ALL_FACTS_EXACT" if not unmet else "PARTIAL_FACTS_UNMET"
    result.update({"training_performed":steps>0,"total_steps":steps,"events":events,
       "accepted":accepted,"unmet":unmet,"latest_accepted":str(last),
       "latest_sha256":digest(last)})
    (a.output_dir/"report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"steps":steps,"accepted":[x["id"] for x in accepted],"unmet":unmet},ensure_ascii=False))
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--facts",type=Path,default=Path("data/literature_fact_corrections_v0135836.jsonl"))
    p.add_argument("--stages",type=Path,default=Path("data/literature_stages_reviewed_v0135834.jsonl"))
    p.add_argument("--reviewed",type=Path,default=Path("data/corrective_sft_reviewed_v0135829.jsonl"))
    p.add_argument("--previous-report",type=Path,default=Path("results/staged_literature_v0135834/report.json"))
    p.add_argument("--start",type=Path,default=Path("results/staged_literature_v0135834/literature-stage-1.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output-dir",type=Path,default=Path("results/literature_facts_v0135836"))
    p.add_argument("--rounds",type=int,default=5)
    p.add_argument("--steps-per-round",type=int,default=10)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--lr",type=float,default=2e-6)
    p.add_argument("--seed",type=int,default=135836)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-experiment",action="store_true")
    run(p.parse_args())
if __name__=="__main__":main()

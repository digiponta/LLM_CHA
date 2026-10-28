"""v0.13.58.32 iterative one-question-at-a-time experimental SFT.

A question passes only when its raw greedy output matches the reviewed
reference exactly (conservative proxy, not proof of semantic quality).
After each update, previously passed/protected questions must still pass.
Never trains on paraphrase evaluation prompts. Bounded retry; stop on
failure or regression. Never overwrite an existing output directory.
"""
import argparse,hashlib,json,random
from pathlib import Path
from dialogue_format_v0135817 import prompt_for,dialogue_for
from aligned_replay_examples_v0135816 import make_aligned_examples
from train_japanese_foundation_v01344 import masked_ce
from train_corrective_sft_v0135830 import preflight as reviewed_preflight

PROTECTED=("protect-identity-005","protect-greeting-006","protect-quantum-007")
ORDER=("correct-talk-001","correct-cpu-002","correct-persona-003",
       "correct-literature-004","correct-tired-008")
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def exact_match(actual,expected):return actual.strip()==expected.strip()
def verify_regressions(answers,ref,ids):
    return [i for i in ids if not exact_match(answers[i],ref[i])]
def schedule(rows):
    byid={r["id"]:r for r in rows}
    if len(byid)!=len(rows) or set(byid)!=set(PROTECTED)|set(ORDER):
        raise ValueError("unexpected reviewed records")
    return [byid[k] for k in ORDER], [byid[k] for k in PROTECTED]
def generate(model,tok,row,max_tokens):
    ids=tok.encode(prompt_for(row["user"]),add_bos=True)
    if len(ids)>=model.context_length:raise ValueError("prompt too long")
    import torch
    with torch.inference_mode():
        out=model.generate(ids,max_new_tokens=max_tokens,eos_id=tok.eos_id,
                           temperature=0.0,repetition_penalty=1.0)
    result=out[len(ids):]
    if result and result[-1]==tok.eos_id:result=result[:-1]
    return tok.decode(result)
def main_run(args):
    # Reuse reviewed-source integrity constraints with an output folder that doesn't exist.
    lines,meta=reviewed_preflight(args.source,args.audit,args.base,args.tokenizer,
                                   args.output_dir,args.max_steps,1,args.lr)
    if not 1<=args.steps_per_round<=args.max_steps or args.max_rounds<1 or args.max_rounds>100:
        raise ValueError("invalid round/step limits")
    if args.max_steps < args.steps_per_round*args.max_rounds:
        raise ValueError("total steps budget smaller than per-item maximum")
    rows=[json.loads(s) for s in args.source.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    targets,protected=schedule(rows)
    if sha(args.start)!=args.start_sha256:raise ValueError("starting checkpoint hash mismatch")
    result={"version":"v0.13.58.32","status":"DRY_RUN_ONLY",
            "start_checkpoint_sha256":sha(args.start),"source_sha256":sha(args.source),
            "planned_order":[r["id"] for r in targets],"protected":[r["id"] for r in protected],
            "max_rounds_per_item":args.max_rounds,"steps_per_round":args.steps_per_round,
            "stop_on_failed_item":True,"stop_on_protected_regression":True,
            "quality_rule":"EXACT_REVIEWED_ANSWER_ONLY","semantic_quality_verified":False,
            "training_performed":False,"production_promotion_allowed":False}
    if not args.run:
        print(json.dumps(result,ensure_ascii=False,indent=2));return result
    if not args.acknowledge_experiment:raise ValueError("--acknowledge-experiment required")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    random.seed(args.seed);torch.manual_seed(args.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(args.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(args.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(args.start),device=device)
    if model.vocab_size!=tok.vocab_size:raise ValueError("vocabulary mismatch")
    optimizer=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=0.01)
    reference={r["id"]:r["assistant"] for r in rows};byid={r["id"]:r for r in rows}
    events=[];passed=[];total_steps=0;last_loss=None
    def answers_for(ids):return {i:generate(model,tok,byid[i],args.max_new_tokens) for i in ids}
    initial=answers_for(list(PROTECTED))
    original_protected=[i for i in PROTECTED if exact_match(initial[i],reference[i])]
    # Checkpoint saving is allowed ONLY if the final state retains these.
    result["initial_protected_passed"]=original_protected
    status="ALL_TARGETS_EXACT"
    for target in targets:
        item=target["id"];before=generate(model,tok,target,args.max_new_tokens)
        if exact_match(before,reference[item]):
            passed.append(item)
            events.append({"id":item,"status":"ALREADY_EXACT","rounds":0,"before":before,"after":before})
            continue
        accepted=False
        for round_no in range(1,args.max_rounds+1):
            replay=[dialogue_for(target["user"],target["assistant"])]
            replay += [dialogue_for(byid[i]["user"],reference[i]) for i in PROTECTED]
            replay += [dialogue_for(byid[i]["user"],reference[i]) for i in passed]
            examples=make_aligned_examples([("conversation",s) for s in replay],
                                          tok,model.context_length,assistant_only=True)
            # Keep all available replay examples in each update, rather than dropping protected items.
            x,y,mask=examples.tensors
            if int(mask.sum())==0:raise ValueError("empty supervised tokens")
            for _ in range(args.steps_per_round):
                model.train();optimizer.zero_grad(set_to_none=True)
                # memory-safe per-example gradient accumulation
                for idx in range(len(x)):
                    loss=masked_ce(model,x[idx:idx+1].to(device),
                       y[idx:idx+1].to(device),mask[idx:idx+1].to(device))
                    (loss/len(x)).backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step()
                last_loss=float(loss.detach().cpu());total_steps+=1
            after=generate(model,tok,target,args.max_new_tokens)
            checks=answers_for(original_protected+passed)
            regress=verify_regressions(checks,reference,original_protected+passed)
            event={"id":item,"round":round_no,"before":before,"after":after,
                   "target_exact":exact_match(after,reference[item]),"regressed_ids":regress,
                   "steps_total":total_steps}
            events.append(event);print(json.dumps(event,ensure_ascii=False))
            if regress:
                status="STOPPED_PROTECTED_REGRESSION";break
            if event["target_exact"]:
                accepted=True;passed.append(item);break
        if status=="STOPPED_PROTECTED_REGRESSION":break
        if not accepted:
            status="STOPPED_ITEM_LIMIT";break
    args.output_dir.mkdir(parents=True,exist_ok=False)
    # Artifact is diagnostic only and not a model promotion.
    result.update({"status":status,"training_performed":total_steps>0,"steps_total":total_steps,
        "passed_target_ids":passed,"events":events,
        "last_loss":last_loss,"production_promotion_allowed":False})
    if status=="ALL_TARGETS_EXACT":
        candidate=args.output_dir/"candidate_iterative.pt"
        model.save_checkpoint(str(candidate),epoch=1,loss=last_loss,
           metadata={"experiment":"ITERATIVE_CORRECTIVE_V0135832",
                     "production_promotion_allowed":False})
        result["checkpoint_sha256"]=sha(candidate)
    else:
        result["checkpoint_saved"]=False
    (args.output_dir/"report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":status,"steps_total":total_steps,"passed_target_ids":passed},ensure_ascii=False))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/corrective_sft_reviewed_v0135829.jsonl"))
    p.add_argument("--audit",type=Path,default=Path("results/corrective_review_v0135829.json"))
    p.add_argument("--base",type=Path,default=Path("model/model-llm-try-nagato-chat-v94.pt"))
    p.add_argument("--start",type=Path,default=Path("results/corrective_sft_v0135830/candidate_corrective.pt"))
    p.add_argument("--start-sha256",default="66254e37a523b5fff9a7a9d2de6420b3b6a4188a1d0361dc29a9ba04044c131b")
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output-dir",type=Path,default=Path("results/iterative_corrective_v0135832"))
    p.add_argument("--max-rounds",type=int,default=5)
    p.add_argument("--steps-per-round",type=int,default=10)
    p.add_argument("--max-steps",type=int,default=50)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--lr",type=float,default=2e-6)
    p.add_argument("--seed",type=int,default=135832)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-experiment",action="store_true")
    main_run(p.parse_args())
if __name__=="__main__":main()

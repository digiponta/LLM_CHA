"""v0.9.7.36 — paired generation evaluation across three frozen checkpoints.

Compare common prompts plus true-label and deliberately swapped-label
conditions. Do not fit or tune on the evaluation results.
"""
import argparse,json
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from chat import generate_reply
from semantic_daily_conversation_v09732 import build
from train_emotion_conditioned_v09735 import semantic_prompt
from emotion_quality_gate_v09735 import assess
from emotion_aware_dialogue_v09733 import detect

CHALLENGE=[
 ("challenge-joy","今日は楽しかった","ENJOYMENT","SHARE_JOY"),
 ("challenge-negative","楽しくなかった","DISAPPOINTMENT","ACKNOWLEDGE_DISAPPOINTMENT"),
 ("challenge-negated-sadness","悲しくないよ","NEGATED_SADNESS","ACKNOWLEDGE_NEGATED_SADNESS"),
 ("challenge-mixed","楽しかったけど疲れた","MIXED","ACKNOWLEDGE_MIXED"),
 ("challenge-greeting","こんにちは","GREETING","GREET"),
 ("challenge-gratitude","本当に助かった","GRATITUDE","ACKNOWLEDGE_GRATITUDE"),
 ("challenge-identity","あなたは誰ですか","IDENTITY","IDENTITY_DIRECT"),
]
SWAP={"POSITIVE":"DISAPPOINTMENT","DISAPPOINTMENT":"POSITIVE",
 "SADNESS":"GRATITUDE","GRATITUDE":"SADNESS","FATIGUE":"POSITIVE",
 "UNCERTAINTY":"DISAPPOINTMENT","MIXED":"POSITIVE",
 "NEGATED_POSITIVE":"POSITIVE","NEGATED_SADNESS":"SADNESS",
 "GREETING":"DISAPPOINTMENT","ENJOYMENT":"DISAPPOINTMENT",
 "IDENTITY":"DISAPPOINTMENT"}
def load(path,device,tok):
    model,_=LanguageModel.load_checkpoint(str(path),device=device)
    model.eval()
    if model.vocab_size!=tok.vocab_size:raise ValueError("vocab mismatch for "+str(path))
    return model
def generate(model,tok,prompt,seed):
    r=generate_reply(model,tok,prompt,max_new_tokens=48,temperature=0.0,
                     top_k=3,repetition_penalty=1.08,seed=seed)
    return {"text":r.text,"mean_confidence":r.mean_confidence,
            "min_confidence":r.min_confidence,"tokens":r.token_count}
def build_cases():
    cases=[{"id":r["id"],"source":"holdout","input":r["input"],
            "emotion":r["semantic"]["emotion"],
            "strategy":r["semantic"]["response_strategy"],
            "reference":r["target"]} for r in build()["holdout"]]
    cases.extend({"id":ident,"source":"challenge","input":q,
                  "emotion":e,"strategy":strategy,"reference":None}
                 for ident,q,e,strategy in CHALLENGE)
    return cases
def evaluate(models,tok,cases,seed=42,runner=generate):
    results=[]
    for row in cases:
        q=row["input"]
        plain="人: "+q+"\nAI: "
        emotion=row["emotion"]
        correct=semantic_prompt(q,emotion,row["strategy"])
        wrong=semantic_prompt(q,SWAP.get(emotion,"DISAPPOINTMENT"),row["strategy"])
        outputs={
          "baseline_plain":runner(models["baseline"],tok,plain,seed),
          "daily_plain":runner(models["daily"],tok,plain,seed),
          "conditioned_plain":runner(models["conditioned"],tok,plain,seed),
          "conditioned_correct":runner(models["conditioned"],tok,correct,seed),
          "conditioned_swapped":runner(models["conditioned"],tok,wrong,seed),
        }
        decision=detect(q)
        for entry in outputs.values():
            entry["reference_exact"]=(entry["text"].strip()==row["reference"].strip()) if row["reference"] else None
            if decision:
                accepted,reason=assess(entry["text"],decision)
                entry["quality_gate_pass"]=accepted
                entry["quality_gate_reason"]=reason
            else:
                entry["quality_gate_pass"]=None
                entry["quality_gate_reason"]="emotion-detector-abstained"
        results.append({**row,"outputs":outputs,
                        "conditioning_response_changed":outputs["conditioned_correct"]["text"]!=outputs["conditioned_swapped"]["text"]})
    summary={}
    for key in ("baseline_plain","daily_plain","conditioned_plain","conditioned_correct","conditioned_swapped"):
        held=[r["outputs"][key] for r in results if r["source"]=="holdout"]
        summary[key]={"holdout_exact":sum(r["reference_exact"] for r in held),
                      "holdout_count":len(held),
                      "quality_gate_pass_holdout":sum(r["quality_gate_pass"] is True for r in held)}
    return {"status":"DIAGNOSTIC_ONLY","models_evaluated":list(models.keys()),
            "case_count":len(results),"summary":summary,
            "condition_change_count":sum(r["conditioning_response_changed"] for r in results),
            "note":"A response change under swapped labels does not prove semantic understanding. Quality gate is whitelist-based and conservative.",
            "rows":results,"train_ready":False,"auto_promote":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--baseline",required=True)
    p.add_argument("--daily",required=True)
    p.add_argument("--conditioned",required=True)
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--output",default="results/emotion_generation_v09736.json")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--cpu",action="store_true")
    a=p.parse_args()
    output=Path(a.output)
    if output.exists():raise FileExistsError("Output already exists: "+str(output))
    device=torch.device("cpu" if a.cpu or not torch.cuda.is_available() else "cuda")
    tok=Tokenizer.load(a.tokenizer)
    models={"baseline":load(a.baseline,device,tok),
            "daily":load(a.daily,device,tok),
            "conditioned":load(a.conditioned,device,tok)}
    result=evaluate(models,tok,build_cases(),a.seed)
    result["checkpoint_paths"]={"baseline":a.baseline,"daily":a.daily,"conditioned":a.conditioned}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False,indent=2))
    print("report:",output)
if __name__=="__main__":main()

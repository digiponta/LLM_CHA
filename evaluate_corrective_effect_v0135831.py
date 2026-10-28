"""v0.13.58.31: Base vs Corrective matched raw generation.
No training, no semantic memory, no model promotion; no automatic correctness claims.
"""
import argparse,hashlib,json
from pathlib import Path
from dialogue_format_v0135817 import prompt_for

PARAPHRASES=[
 {"id":"talk_p","category":"conversation","user":"何かお話ししませんか？","related_train_id":"correct-talk-001"},
 {"id":"cpu_p","category":"knowledge","user":"CPUはどんな役割を持っていますか？","related_train_id":"correct-cpu-002"},
 {"id":"persona_p","category":"persona","user":"あなたの好きなことは何ですか？","related_train_id":"correct-persona-003"},
 {"id":"literature_p","category":"literature","user":"夏目漱石の猫の小説について知りたい","related_train_id":"correct-literature-004"},
 {"id":"tired_p","category":"conversation","user":"今日は疲れ気味なんです","related_train_id":"correct-tired-008"},
 {"id":"quantum_p","category":"knowledge","user":"量子力学の基本を説明して","related_train_id":"protect-quantum-007"}
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def preflight(report_path,base,corrective,tokenizer,reviewed,output,max_tokens):
    if output.exists():raise FileExistsError(output)
    if not 1<=max_tokens<=256:raise ValueError("invalid token budget")
    report=json.loads(report_path.read_text(encoding="utf-8-sig"))
    if report.get("status")!="EXPLORATORY_CORRECTIVE_TRAINING_COMPLETE" or report.get("version")!="v0.13.58.30":
        raise ValueError("training incomplete")
    for p,key in ((base,"base_sha256"),(corrective,"checkpoint_sha256"),(tokenizer,"tokenizer_sha256"),(reviewed,"source_sha256")):
        if sha(p)!=report.get(key):raise ValueError("sha mismatch: "+key)
    rows=[json.loads(s) for s in reviewed.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    if len(rows)!=8 or any(r.get("approved") is not True for r in rows):raise ValueError("unexpected training dataset")
    train=[{"id":r["id"],"category":r["domain"],"user":r["user"],"reference":r["assistant"],"set":"exposed_train"} for r in rows]
    all_questions={r["user"] for r in train}
    if any(p["user"] in all_questions for p in PARAPHRASES):raise ValueError("paraphrase overlaps direct training question")
    hold=[{**p,"set":"untrained_paraphrase_not_independently_audited"} for p in PARAPHRASES]
    return train+hold,report

def evaluate(report_path,base,corrective,tokenizer,reviewed,output,max_tokens=64,device_name="auto"):
    probes,training=preflight(report_path,base,corrective,tokenizer,reviewed,output,max_tokens)
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    tok=Tokenizer.load(str(tokenizer))
    device=torch.device("cuda" if device_name=="auto" and torch.cuda.is_available() else ("cpu" if device_name=="auto" else device_name))
    if device.type=="cuda" and not torch.cuda.is_available():raise ValueError("CUDA unavailable")
    results={}
    for arm,path in (("Base",base),("Corrective",corrective)):
        model,_=LanguageModel.load_checkpoint(str(path),device=device)
        if model.vocab_size!=tok.vocab_size:raise ValueError("vocabulary mismatch")
        rows=[]
        for p in probes:
            ids=tok.encode(prompt_for(p["user"]),add_bos=True)
            if len(ids)>=model.context_length:raise ValueError("prompt exceeds context")
            with torch.inference_mode():
                out=model.generate(ids,max_new_tokens=max_tokens,eos_id=tok.eos_id,temperature=0.0,repetition_penalty=1.0)
            cont=out[len(ids):]
            if cont and cont[-1]==tok.eos_id:cont=cont[:-1]
            rows.append({"id":p["id"],"set":p["set"],"user":p["user"],
                "answer":tok.decode(cont),"tokens":len(out)-len(ids),
                "eos_reached":bool(out and out[-1]==tok.eos_id)})
        results[arm]=rows
        del model
        if torch.cuda.is_available():torch.cuda.empty_cache()
    merged=[]
    for p,b,c in zip(probes,results["Base"],results["Corrective"]):
        if b["id"]!=c["id"] or b["user"]!=c["user"]:raise ValueError("unpaired results")
        merged.append({**p,"base_answer":b["answer"],"corrective_answer":c["answer"],
                       "changed":b["answer"]!=c["answer"],"base_eos":b["eos_reached"],
                       "corrective_eos":c["eos_reached"],
                       "quality_judgment":"REQUIRES_HUMAN_OR_EXPLICIT_RUBRIC_REVIEW"})
    out={"version":"v0.13.58.31","status":"MATCHED_GENERATION_COMPARISON_COMPLETE",
         "models_sha256":{"Base":sha(base),"Corrective":sha(corrective)},
         "tokenizer_sha256":sha(tokenizer),"source_training_report_sha256":sha(report_path),
         "max_new_tokens":max_tokens,"decoder":"greedy_argmax","records":merged,
         "changed_responses":sum(x["changed"] for x in merged),
         "exposed_train_count":sum(x["set"]=="exposed_train" for x in merged),
         "paraphrase_count":sum(x["set"]=="untrained_paraphrase_not_independently_audited" for x in merged),
         "semantic_correctness_verified":False,"independent_holdout_verified":False,
         "training_performed":False,"production_promotion_allowed":False}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return out
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",type=Path,default=Path("results/corrective_sft_v0135830/report.json"))
    p.add_argument("--base",type=Path,default=Path("model/model-llm-try-nagato-chat-v94.pt"))
    p.add_argument("--corrective",type=Path,default=Path("results/corrective_sft_v0135830/candidate_corrective.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--reviewed",type=Path,default=Path("data/corrective_sft_reviewed_v0135829.jsonl"))
    p.add_argument("--output",type=Path,default=Path("results/corrective_effect_v0135831.json"))
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    args=p.parse_args()
    result=evaluate(args.report,args.base,args.corrective,args.tokenizer,args.reviewed,args.output,args.max_new_tokens,args.device)
    print(json.dumps({key:result[key] for key in ("status","changed_responses","exposed_train_count","paraphrase_count")},ensure_ascii=False))
    print("report:",args.output)
if __name__=="__main__":main()

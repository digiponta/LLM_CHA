"""v0.13.58.27 raw generation comparison for four immutable checkpoints.

Read-only; no Semantic Memory, retrieval, web, training or promotion.
Identical canonical prompts and deterministic argmax generation.
Outputs are qualitative probes, not automatic accuracy judgements.
"""
import argparse,hashlib,json
from pathlib import Path
from dialogue_format_v0135817 import prompt_for

PROBES=[
 {"id":"identity","category":"persona","user":"あなたは誰？"},
 {"id":"persona_name","category":"persona","user":"長門有希とは？"},
 {"id":"greeting","category":"conversation","user":"こんにちは"},
 {"id":"tired","category":"conversation","user":"今日は少し疲れました"},
 {"id":"talk","category":"conversation","user":"少し話そう"},
 {"id":"quantum","category":"knowledge","user":"量子力学とは？"},
 {"id":"cpu","category":"knowledge","user":"CPUとは？"},
 {"id":"literature","category":"literature","user":"吾輩は猫であるについて教えて"},
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def check(trained,base,tokenizer,output,max_new):
    if output.exists():raise FileExistsError(output)
    if not 1<=max_new<=256:raise ValueError("max_new out of range")
    report=json.loads((trained/"report.json").read_text(encoding="utf-8-sig"))
    if report.get("status")!="EXPLORATORY_TRAINING_COMPLETE":raise ValueError("experiment not completed")
    if sha(base)!=report.get("checkpoint_sha256") or sha(tokenizer)!=report.get("tokenizer_sha256"):
        raise ValueError("base/tokenizer provenance mismatch")
    paths={"Base":base}
    for arm in ("W","WR","WRP"):
        path=trained/("candidate_"+arm+".pt")
        if sha(path)!=report.get("history",{}).get(arm,{}).get("checkpoint_sha256"):
            raise ValueError("candidate sha mismatch: "+arm)
        paths[arm]=path
    return paths

def compare(trained,base,tokenizer,output,max_new=64,device_name="auto"):
    paths=check(trained,base,tokenizer,output,max_new)
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    tok=Tokenizer.load(str(tokenizer))
    if device_name=="auto":device_name="cuda" if torch.cuda.is_available() else "cpu"
    if device_name=="cuda" and not torch.cuda.is_available():raise ValueError("cuda not available")
    device=torch.device(device_name)
    data={"version":"v0.13.58.27","status":"RAW_GENERATION_DIAGNOSTIC",
          "prompt_format":"人: {user}\\nAI: ","decoder":"greedy_argmax",
          "max_new_tokens":max_new,"checkpoint_sha256":{a:sha(p) for a,p in paths.items()},
          "tokenizer_sha256":sha(tokenizer),"probes":PROBES,
          "results":{},"quality_scored":False,"training_performed":False,
          "semantic_memory_used":False,"external_evidence_used":False,
          "independent_holdout_verified":False,"human_review_approved":False,
          "production_promotion_allowed":False}
    for arm,path in paths.items():
        model,_=LanguageModel.load_checkpoint(str(path),device=device)
        if model.vocab_size!=tok.vocab_size:raise ValueError("vocab mismatch")
        arm_rows=[]
        for probe in PROBES:
            prompt=prompt_for(probe["user"])
            prompt_ids=tok.encode(prompt,add_bos=True)
            if len(prompt_ids)>model.context_length:raise ValueError("prompt too long")
            with torch.inference_mode():
                generated=model.generate(prompt_ids,max_new_tokens=max_new,eos_id=tok.eos_id,
                    temperature=0.0,repetition_penalty=1.0)
            answer_ids=generated[len(prompt_ids):]
            if answer_ids and answer_ids[-1]==tok.eos_id:answer_ids=answer_ids[:-1]
            arm_rows.append({"id":probe["id"],"category":probe["category"],
                             "user":probe["user"],"raw_answer":tok.decode(answer_ids),
                             "generated_tokens":len(generated)-len(prompt_ids),
                             "eos_reached":bool(generated and generated[-1]==tok.eos_id)})
        data["results"][arm]=arm_rows
        del model
        if torch.cuda.is_available():torch.cuda.empty_cache()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return data

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--trained-dir",type=Path,default=Path("results/jawiki_controlled_v0135825"))
    p.add_argument("--base",type=Path,default=Path("model/model-llm-try-nagato-chat-v94.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/jawiki_generation_v0135827.json"))
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    a=p.parse_args()
    result=compare(a.trained_dir,a.base,a.tokenizer,a.output,a.max_new_tokens,a.device)
    print(json.dumps({"status":result["status"],"models":list(result["results"]),
        "probes":len(result["probes"]),"quality_scored":False},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()

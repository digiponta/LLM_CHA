"""v0.13.58.35: read-only EOS and compositional literature probes.

The Stage 1 checkpoint and its report are SHA-verified before use.
EOS/continuation logits are evaluated at teacher-forced prefix positions.
This measures decoder preferences, NOT generalization or correctness.
"""
import argparse,hashlib,json
from pathlib import Path
from dialogue_format_v0135817 import prompt_for
from train_iterative_corrective_v0135832 import generate
STAGE_SHA="7e23f8164ad8e8ed9b5dfcfb177a5244ecbcd51c956fb30787bd3d5bf8128469"
PROBES=[
 {"id":"work","user":"吾輩は猫であるについて教えて","expected_terms":["吾輩は猫である","夏目漱石"]},
 {"id":"author","user":"『吾輩は猫である』の作者は誰？","expected_terms":["夏目漱石"]},
 {"id":"narrator","user":"『吾輩は猫である』の語り手は？","expected_terms":["猫"]},
 {"id":"theme","user":"『吾輩は猫である』はどんな作品？","expected_terms":["猫","人間"]},
 {"id":"author_alt","user":"夏目漱石が書いた猫の小説は？","expected_terms":["吾輩は猫である"]},
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(checkpoint,report,stages,tokenizer,output):
    if output.exists():raise FileExistsError(output)
    prior=json.loads(report.read_text(encoding="utf-8-sig"))
    if prior.get("version")!="v0.13.58.34" or prior.get("status")!="STOPPED_STAGE_LIMIT":raise ValueError("unexpected prior report")
    if sha(checkpoint)!=STAGE_SHA or sha(checkpoint)!=prior.get("latest_accepted_sha256"):raise ValueError("checkpoint provenance mismatch")
    if sha(stages)!=prior.get("stages_sha256"):raise ValueError("stage data modified")
    rows=[json.loads(s) for s in stages.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    if len(rows)!=2 or rows[0].get("id")!="literature-stage-1" or rows[1].get("id")!="literature-stage-2":raise ValueError("invalid stages")
    if not tokenizer.is_file():raise FileNotFoundError(tokenizer)
    return rows,prior
def prefix_logits(model,tok,question,prefix,device):
    """Predict next token after prompt + teacher-forced answer prefix."""
    import torch
    ids=tok.encode(prompt_for(question),add_bos=True)+tok.encode(prefix,add_bos=False)
    if len(ids)>model.context_length:raise ValueError("context limit")
    with torch.inference_mode():
        probs=torch.softmax(model(torch.tensor([ids],device=device))[0,-1].float(),dim=-1)
    k=min(8,probs.numel())
    vals,indices=torch.topk(probs,k=k)
    top=[{"id":int(i),"token":tok.decode([int(i)],skip_special_tokens=False),
          "probability":float(v)} for v,i in zip(vals.tolist(),indices.tolist())]
    eos=float(probs[tok.eos_id])
    return {"prefix":prefix,"eos_probability":eos,
            "eos_rank":int((probs>probs[tok.eos_id]).sum().item())+1,
            "top_tokens":top}
def diagnose(checkpoint,report,stages,tokenizer,output,max_new=64,device_name="auto"):
    if not 1<=max_new<=256:raise ValueError("token budget invalid")
    stage_rows,_=verify(checkpoint,report,stages,tokenizer,output)
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    dev=torch.device("cuda" if device_name=="auto" and torch.cuda.is_available() else ("cpu" if device_name=="auto" else device_name))
    if dev.type=="cuda" and not torch.cuda.is_available():raise ValueError("CUDA unavailable")
    tok=Tokenizer.load(str(tokenizer));model,_=LanguageModel.load_checkpoint(str(checkpoint),device=dev)
    if model.vocab_size!=tok.vocab_size:raise ValueError("vocab mismatch")
    question=stage_rows[0]["user"];short=stage_rows[0]["assistant"];long=stage_rows[1]["assistant"]
    # Whole short answer is a critical divergence point: EOS vs expanding answer.
    # Compare EOS with the first continuation token as actually tokenized.
    full=tok.encode(long,add_bos=False)
    short_ids=tok.encode(short,add_bos=False)
    continuation=full[len(short_ids):] if full[:len(short_ids)]==short_ids else []
    boundaries=[]
    for prefix in ("",short,long):
        info=prefix_logits(model,tok,question,prefix,dev)
        info["label"]="prompt_only" if not prefix else ("stage1_end" if prefix==short else "stage2_end")
        boundaries.append(info)
    output_rows=[]
    for p in PROBES:
        answer=generate(model,tok,p,max_new)
        output_rows.append({**p,"answer":answer,
            "expected_term_hits":[term for term in p["expected_terms"] if term in answer],
            "semantic_correctness_verified":False})
    result={"version":"v0.13.58.35","status":"LITERATURE_EOS_DIAGNOSTIC_COMPLETE",
       "checkpoint_sha256":sha(checkpoint),"tokenizer_sha256":sha(tokenizer),
       "stages_sha256":sha(stages),"max_new_tokens":max_new,
       "stage1_is_token_prefix_of_stage2":bool(continuation),
       "stage2_continuation_first_token_id":continuation[0] if continuation else None,
       "boundary_distributions":boundaries,"compositional_probes":output_rows,
       "training_performed":False,"independent_holdout_verified":False,
       "semantic_correctness_verified":False,"production_promotion_allowed":False}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkpoint",type=Path,default=Path("results/staged_literature_v0135834/literature-stage-1.pt"))
    p.add_argument("--report",type=Path,default=Path("results/staged_literature_v0135834/report.json"))
    p.add_argument("--stages",type=Path,default=Path("data/literature_stages_reviewed_v0135834.jsonl"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/literature_eos_v0135835.json"))
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    a=p.parse_args();r=diagnose(a.checkpoint,a.report,a.stages,a.tokenizer,a.output,a.max_new_tokens,a.device)
    print(json.dumps({"status":r["status"],"stage1_token_prefix":r["stage1_is_token_prefix_of_stage2"],
      "eos_at_stage1":r["boundary_distributions"][1]["eos_probability"],"probes":len(r["compositional_probes"])},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()

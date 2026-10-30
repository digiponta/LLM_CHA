"""Compare baseline vs negative-only candidate under the actual GUI evidence prompt."""
import argparse
import json
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from chat import generate_reply
from evidence_aware_route_v013588236 import generation_prompt,encode_request,decode_request
from evidence_conditioned_generation_v013588228 import retrieve_evidence,final_answer
from train_negative_only_v013588247 import read_negative_signals

def next_token_diagnostic(model,tok,prompt):
    ids=tok.encode(prompt,add_bos=True)[-model.context_length:]
    x=torch.tensor([ids],dtype=torch.long,device=next(model.parameters()).device)
    with torch.no_grad():
        p=F.softmax(model(x)[0,-1],dim=-1)
        values,indices=torch.topk(p,2)
    return {"top1_id":int(indices[0]),"top1_prob":float(values[0]),"top2_id":int(indices[1]),"top2_prob":float(values[1]),"margin":float(values[0]-values[1])}

def conditional_nll(model,tok,prompt,answer):
    prompt_ids=tok.encode(prompt,add_bos=True)
    answer_ids=tok.encode(answer,add_eos=True)
    # Truncate to exactly the model context, matching autoregressive generation.
    sequence=prompt_ids+answer_ids
    logps=[]
    device=next(model.parameters()).device
    with torch.no_grad():
        for pos in range(len(prompt_ids),len(sequence)):
            x=torch.tensor([sequence[max(0,pos-model.context_length):pos]],dtype=torch.long,device=device)
            target=sequence[pos]
            logps.append(float(F.log_softmax(model(x)[0,-1],dim=-1)[target]))
    return -sum(logps)/len(logps) if logps else None

def compare(base,candidate,tok,evidence,negatives,max_tokens=120):
    if evidence.get("status")!="EVIDENCE":raise ValueError("EVIDENCE_REQUIRED")
    topic,excerpt=decode_request(encode_request(evidence["topic"],evidence["excerpt"]))
    prompt=generation_prompt(topic,excerpt)
    cases={}
    for label,model in [("base",base),("candidate",candidate)]:
        model.eval()
        result=generate_reply(model,tok,prompt,min(max_tokens,120),0.0,0,1.0,seed=0)
        output=" ".join(result.text.splitlines()).strip() or "未学習です"
        gated=final_answer(output,evidence)
        cases[label]={"text":output,"gate":gated["gate"],"token_count":result.token_count,
                      "top_first_token":next_token_diagnostic(model,tok,prompt),
                      "negative_conditional_nll":[conditional_nll(model,tok,prompt,row["rejected_answer"]) for row in negatives]}
    return {"status":"EVIDENCE_REPLAY_DIAGNOSTIC","topic":topic,
        "source_url":evidence.get("url",""),"source_title":evidence.get("title",""),
        "wire_excerpt_chars":len(excerpt),"prompt":prompt,
        "generation_changed":cases["base"]["text"]!=cases["candidate"]["text"],
        "base":cases["base"],"candidate":cases["candidate"],
        "production_promoted":False,
        "caution":"Live evidence may change; for reproducible replay use --evidence-json snapshot. Same prompt/seed as GUI evidence candidate route. Rejected-only training has no guarantee of improved correctness."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--candidate",default="results/negative_only_v013588247_steps3.candidate.pt")
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--negative-data",default="data/negative_teacher_signals_v013588244.jsonl")
    p.add_argument("--topic",default="宇宙")
    p.add_argument("--previous",default="宇宙は膨張している。")
    p.add_argument("--evidence-json",default=None,help="Saved retrieve_evidence JSON for exact repeatability")
    p.add_argument("--snapshot-out",default="results/evidence_snapshot_v013588249.json")
    p.add_argument("--output",default="results/evidence_replay_v013588249.json")
    p.add_argument("--max-new-tokens",type=int,default=120)
    a=p.parse_args()
    if a.evidence_json:
        evidence=json.loads(Path(a.evidence_json).read_text(encoding="utf-8-sig"))
    else:
        evidence=retrieve_evidence(a.topic,a.previous)
    if evidence.get("status")!="EVIDENCE":
        raise SystemExit("NO_EVIDENCE: provide --evidence-json with a saved evidence object")
    snap=Path(a.snapshot_out);snap.parent.mkdir(parents=True,exist_ok=True)
    snap.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(a.base,device=device)
    candidate,_=LanguageModel.load_checkpoint(a.candidate,device=device)
    tok=Tokenizer.load(a.tokenizer)
    if base.vocab_size!=tok.vocab_size or candidate.vocab_size!=tok.vocab_size:
        raise ValueError("TOKENIZER_MODEL_MISMATCH")
    report=compare(base,candidate,tok,evidence,read_negative_signals(a.negative_data),a.max_new_tokens)
    report["base_model"]=a.base;report["candidate_model"]=a.candidate
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"generation_changed":report["generation_changed"],
        "base_gate":report["base"]["gate"],"candidate_gate":report["candidate"]["gate"],
        "snapshot":str(snap),"report":str(out),"production_promoted":False},ensure_ascii=False))
if __name__=="__main__":main()

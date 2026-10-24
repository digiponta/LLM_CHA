"""v0.8.0.20: leakage-guarded evaluation on externally supplied holdout Q/A.

This does not manufacture independent test evidence: records must be supplied
separately and are rejected if overlapping training questions/answers.
"""
import json
import re
from pathlib import Path

def normalized(text):
    return re.sub(r"\s+","",(text or "").strip()).rstrip("。！？?!").casefold()

def validate_holdout(data,training_rows,checkpoint_ids):
    if not isinstance(data,dict) or not isinstance(data.get("records"),list):
        raise ValueError("holdout JSON requires records list")
    training_ids=set(checkpoint_ids)
    train_questions={normalized(r["subject"]+"についてWikipediaの未検証情報は？") for r in training_rows}
    train_answers={normalized("Wikipediaの未検証情報: "+r["natural_language"]) for r in training_rows}
    # A test of unseen facts must not simply reuse an answer from training.
    seen=set()
    result=[]
    for row in data["records"]:
        if not isinstance(row,dict):raise ValueError("invalid holdout row")
        question=row.get("question")
        answer=row.get("reference_answer")
        rid=row.get("id")
        if not all(isinstance(v,str) and v.strip() for v in (rid,question,answer)):
            raise ValueError("holdout id, question and reference_answer are required")
        if rid in training_ids:raise ValueError("TRAINING_ID_LEAKAGE")
        if normalized(question) in train_questions:raise ValueError("TRAINING_QUESTION_LEAKAGE")
        if normalized(answer) in train_answers:raise ValueError("TRAINING_ANSWER_LEAKAGE")
        if rid in seen:raise ValueError("duplicate holdout id")
        seen.add(rid)
        result.append({"id":rid,"question":question,"reference_answer":answer})
    if not result:raise ValueError("EMPTY_HOLDOUT")
    return result

def evaluate_holdout(path,store,base_path,tokenizer_path,adapter_path):
    import torch
    import torch.nn.functional as F
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from dual_adapters_v073 import DualAdapterModel,frozen_digest
    from unapproved_llm_intake_v074446 import _read
    ck=torch.load(adapter_path,map_location="cpu",weights_only=True)
    if ck.get("route")!="unapproved_wikipedia" or ck.get("approved") is not False or ck.get("trusted_deployable") is not False:
        raise ValueError("invalid unapproved checkpoint")
    rows=_read(store)["candidates"]
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    records=validate_holdout(data,rows,ck.get("candidate_ids",[]))
    base,_=LanguageModel.load_checkpoint(str(base_path),device=torch.device("cpu"))
    if frozen_digest(base)!=ck.get("base_hash"):raise ValueError("base mismatch")
    tokenizer=Tokenizer.load(str(tokenizer_path))
    adapter=DualAdapterModel(base,rank=int(ck["rank"]))
    adapter.experimental.load_state_dict(ck["adapter"],strict=True)
    base.eval();adapter.eval()
    outcomes=[]
    for row in records:
        prefix=tokenizer.encode("人: "+row["question"]+"\nAI: ",add_bos=True)
        answer=tokenizer.encode(row["reference_answer"],add_eos=True)
        context=base.context_length
        if len(answer)>context:
            raise ValueError("holdout answer exceeds context (would truncate evidence)")
        if len(prefix)+len(answer)>context+1:
            prefix=prefix[-(context+1-len(answer)):]
        seq=prefix+answer
        x=torch.tensor([seq[:-1]],dtype=torch.long)
        gold=torch.tensor(answer,dtype=torch.long)
        begin=len(prefix)-1
        with torch.inference_mode():
            a=base(x)[0,begin:begin+len(answer),:]
            b=adapter(x,route="experimental")[0,begin:begin+len(answer),:]
            delta=float((F.cross_entropy(a,gold)-F.cross_entropy(b,gold)).item())
        outcomes.append({"id":row["id"],"nll_improvement":delta,"target_tokens":len(answer)})
    return {"status":"EVALUATED","records":len(outcomes),"results":outcomes,
       "mean_nll_improvement":sum(r["nll_improvement"] for r in outcomes)/len(outcomes),
       "independent_source_attested":bool(data.get("independent_source_attested") is True),
       "lexical_overlap_guard":True,
       "semantic_independence_verified":False,
       "knowledge_accuracy_measured":False,
       "truth_state":"EXTERNAL_UNVERIFIED","weights_changed":False}

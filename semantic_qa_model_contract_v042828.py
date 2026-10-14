"""v0.4.28.28: semantic QA model input/output contract, no model loaded or trained."""
import argparse,hashlib,json
from pathlib import Path
from chatgpt_qa_label_exchange_v042823 import export_packet,validate_labels

METHODS=("cross_encoder","nli")
DECISIONS=("RELEVANT","IRRELEVANT","ABSTAIN")
def design(validation,labels):
    packet=export_packet(validation)
    labeled=validate_labels(packet,labels)
    lookup={(d["id"],d["turn"]):d for d in labeled["decisions"]}
    cases=[]
    for row in packet["cases"]:
        key=(row["id"],row["turn"])
        d=lookup[key]
        cases.append({"id":key[0],"turn":key[1],"question":row["question"],
          "answer":row["final_answer"],"provisional_chatgpt_label":d["chatgpt_relevant"],
          "split":"DEVELOPMENT_ONLY","model_decision":None,"model_score":None})
    return {"version":"v0.4.28.28","mode":"MODEL_CONTRACT_ONLY",
      "methods_candidates":list(METHODS),"expected_output":list(DECISIONS),
      "score_range":[0.0,1.0],"score_interpretation":"model_specific_not_calibrated",
      "labels_used_for_prediction":False,"human_ground_truth":False,
      "independent_holdout":False,"model_trained":False,"model_inference_executed":False,
      "runtime_modified":False,"total":len(cases),"cases":cases}

def validate_predictions(contract,predictions):
    if predictions.get("schema")!="llm_cha_semantic_qa_predictions_v1":raise ValueError("invalid schema")
    if predictions.get("method") not in METHODS:raise ValueError("unknown method")
    if predictions.get("dataset_split")!="DEVELOPMENT_ONLY":raise ValueError("unverified split")
    expected={(r["id"],r["turn"]) for r in contract["cases"]}
    items=predictions.get("predictions")
    if not isinstance(items,list) or len(items)!=len(expected):raise ValueError("requires 64 predictions")
    seen=set();scores=[]
    for x in items:
        key=(x.get("id"),x.get("turn"))
        if key in seen or key not in expected:raise ValueError("invalid/duplicate key")
        seen.add(key)
        decision=x.get("decision")
        score=x.get("score")
        if decision not in DECISIONS:raise ValueError("bad decision")
        if score is not None and (type(score) not in (int,float) or not 0<=score<=1):raise ValueError("bad score")
        if decision=="ABSTAIN" and score is not None:raise ValueError("abstain must not include score")
        scores.append({"id":key[0],"turn":key[1],"decision":decision,"score":score})
    return {"schema":"llm_cha_semantic_qa_predictions_v1","method":predictions["method"],
      "source":"EXTERNAL_UNVERIFIED_MODEL","runtime_modified":False,
      "total":64,"scored":sum(x["score"] is not None for x in scores),
      "decisions":scores,"holdout_independent":False,"accuracy":"NOT_ESTABLISHED"}

def main():
    p=argparse.ArgumentParser()
    for arg in ("validation","labels","output"):p.add_argument("--"+arg,required=True)
    p.add_argument("--predictions")
    a=p.parse_args()
    try:
        inp,label,out=Path(a.validation),Path(a.labels),Path(a.output)
        if any(not x.is_file() or x.is_symlink() for x in (inp,label)) or out.exists() or out.is_symlink():
            raise ValueError("invalid input/output")
        data=json.loads(inp.read_text(encoding="utf-8-sig"))
        annotations=json.loads(label.read_text(encoding="utf-8-sig"))
        contract=design(data,annotations)
        if a.predictions:
            path=Path(a.predictions)
            if not path.is_file() or path.is_symlink():raise ValueError("invalid prediction file")
            result=validate_predictions(contract,json.loads(path.read_text(encoding="utf-8-sig")))
        else:result=contract
        result["input_sha256"]={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in (inp,label)}
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({"mode":result.get("mode","PREDICTION_VALIDATION"),"total":result["total"]}))
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        p.exit(1,f"QA model contract failed: {exc}\n")
if __name__=="__main__":main()

"""v0.4.28.23: ChatGPT labeling exchange; AI labels stay separate from human labels."""
import argparse,hashlib,json
from pathlib import Path
from review_semantic_relevance_v042813 import template

def export_packet(validation):
    rows=template(validation)
    return {"schema":"llm_cha_chatgpt_qa_v1","instructions":"Evaluate whether the FINAL answer responds appropriately to the question, not merely similar wording. Preserve id and turn. Use true, false, or null when uncertain. Provide a short reason. Do not treat this as human ground truth.","cases":[{"id":r["id"],"turn":r["turn"],"question":r["question"],"final_answer":r["final_answer"]} for r in rows]}

def validate_labels(packet,labels):
    if labels.get("schema")!="llm_cha_chatgpt_qa_v1":raise ValueError("invalid schema")
    if labels.get("label_source")!="chatgpt":raise ValueError("label_source must be chatgpt")
    expected={(r["id"],str(r["turn"])):r for r in packet["cases"]}
    decisions=labels.get("decisions")
    if not isinstance(decisions,list) or len(decisions)!=len(expected):raise ValueError("must supply one decision per case")
    checked=[];seen=set()
    for d in decisions:
        if not isinstance(d,dict):raise ValueError("invalid decision")
        key=(d.get("id"),str(d.get("turn")))
        if key not in expected or key in seen:raise ValueError("unknown or duplicate case")
        seen.add(key)
        if type(d.get("relevant")) not in (bool,type(None)):raise ValueError("relevant must be true/false/null")
        reason=d.get("reason")
        if not isinstance(reason,str) or not reason.strip():raise ValueError("reason required")
        checked.append({"id":key[0],"turn":int(key[1]),"chatgpt_relevant":d["relevant"],"reason":reason.strip()})
    return {"version":"v0.4.28.23","source":"chatgpt","human_ground_truth":False,
       "total":len(checked),"positive":sum(x["chatgpt_relevant"] is True for x in checked),
       "negative":sum(x["chatgpt_relevant"] is False for x in checked),
       "uncertain":sum(x["chatgpt_relevant"] is None for x in checked),
       "decisions":checked}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validation",required=True)
    p.add_argument("--export-packet")
    p.add_argument("--import-labels")
    p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        if bool(a.export_packet)==bool(a.import_labels):raise ValueError("choose export-packet or import-labels")
        inp,out=Path(a.validation),Path(a.output)
        if not inp.is_file() or inp.is_symlink() or out.exists() or out.is_symlink():raise ValueError("invalid path")
        validation=json.loads(inp.read_text(encoding="utf-8"))
        packet=export_packet(validation)
        if a.import_labels:
            file=Path(a.import_labels)
            if not file.is_file() or file.is_symlink():raise ValueError("invalid labels path")
            result=validate_labels(packet,json.loads(file.read_text(encoding="utf-8-sig")))
            result["validation_sha256"]=hashlib.sha256(inp.read_bytes()).hexdigest()
            result["labels_sha256"]=hashlib.sha256(file.read_bytes()).hexdigest()
        else:
            result=packet
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({"mode":"import" if a.import_labels else "export","cases":len(packet["cases"]),"output":str(out)},ensure_ascii=False))
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as e:p.exit(1,f"ChatGPT label exchange failed: {e}\n")
if __name__=="__main__":main()

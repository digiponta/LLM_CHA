"""v0.4.28.24: offline ChatGPT provisional QA label vs observed Gate diagnostics."""
import argparse,hashlib,json,math
from pathlib import Path
from chatgpt_qa_label_exchange_v042823 import export_packet,validate_labels
from evaluate_qa_lexical_shadow_v042818 import bigrams

def analyze(validation,labels,comparison):
    packet=export_packet(validation)
    labeled=validate_labels(packet,labels)
    source=comparison.get("records")
    if not isinstance(source,list) or len(source)!=64:raise ValueError("expected 64 gate records")
    gates={}
    for row in source:
        key=(row.get("id"),row.get("turn"))
        if key in gates:raise ValueError("duplicate gate record")
        gates[key]=row
    indexed={(r["id"],r["turn"]):r for r in validation["records"]}
    if set(gates)!=set(indexed):raise ValueError("gate/validation alignment mismatch")
    joined=[]
    for d in labeled["decisions"]:
        key=(d["id"],d["turn"]);original=indexed[key];gate=gates[key]
        if gate.get("human_final_relevant") is not None:
            raise ValueError("expected unlabeled human baseline; separate human and AI sources")
        agreement=gate.get("semantic_agreement")
        if agreement is not None and (not isinstance(agreement,(float,int)) or isinstance(agreement,bool) or not math.isfinite(agreement) or not 0<=agreement<=1):
            raise ValueError("invalid semantic agreement")
        q,a=original["question"],original.get("final_answer")
        qg=bigrams(q);ag=bigrams(a) if isinstance(a,str) else set()
        lexical=round(len(qg&ag)/len(qg),6) if qg and ag else None
        accept=gate.get("gate_resolution")=="ACCEPT"
        joined.append({"id":key[0],"turn":key[1],"chatgpt_relevant":d["chatgpt_relevant"],
            "chatgpt_reason":d["reason"],"gate_resolution":gate.get("gate_resolution"),
            "semantic_agreement":agreement,"lexical_overlap":lexical,
            "provisional_false_accept":accept and d["chatgpt_relevant"] is False,
            "provisional_accepted_relevant":accept and d["chatgpt_relevant"] is True})
    scores=[r for r in joined if r["semantic_agreement"] is not None]
    return {"version":"v0.4.28.24","mode":"OFFLINE_CHATGPT_PROVISIONAL_AUDIT",
      "label_source":"chatgpt","human_ground_truth":False,"independent_holdout":False,
      "runtime_modified":False,"accuracy_estimate":"UNAVAILABLE",
      "total_turns":64,"positive":labeled["positive"],"negative":labeled["negative"],"uncertain":labeled["uncertain"],
      "accepted":sum(r["gate_resolution"]=="ACCEPT" for r in joined),
      "provisional_false_accept":sum(r["provisional_false_accept"] for r in joined),
      "provisional_accepted_relevant":sum(r["provisional_accepted_relevant"] for r in joined),
      "semantic_agreement_observed":len(scores),
      "score_and_negative":sum(r["semantic_agreement"] is not None and r["chatgpt_relevant"] is False for r in joined),
      "records":joined}

def main():
    p=argparse.ArgumentParser()
    for name in ("validation","labels","comparison","output"):p.add_argument("--"+name,required=True)
    a=p.parse_args()
    try:
        paths=[Path(a.validation),Path(a.labels),Path(a.comparison)]
        dst=Path(a.output)
        if any(not x.is_file() or x.is_symlink() for x in paths):raise ValueError("invalid input")
        if dst.exists() or dst.is_symlink():raise ValueError("output exists")
        data=[json.loads(x.read_text(encoding="utf-8-sig")) for x in paths]
        report=analyze(*data)
        report["sha256"]={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:report[k] for k in ("total_turns","positive","negative","uncertain","accepted","provisional_false_accept","semantic_agreement_observed")}))
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:p.exit(1,f"ChatGPT QA audit failed: {e}\n")
if __name__=="__main__":main()

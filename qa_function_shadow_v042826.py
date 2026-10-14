"""v0.4.28.26: conservative answer-function QA shadow, NOT an embedding model.

This is an independent, explainable heuristic. It never uses ChatGPT labels or
Truth Gate data to determine decisions; ambiguous cases abstain.
"""
import argparse,hashlib,json,re
from pathlib import Path
from analyze_chatgpt_qa_gate_v042824 import analyze

UNKNOWN={"未学習です","わかりません","分かりません","知りません"}
def assess(question,answer):
    if not isinstance(question,str) or not isinstance(answer,str):
        return "ABSTAIN","MISSING_TEXT"
    q=question.strip();a=answer.strip()
    if not q or not a:return "ABSTAIN","EMPTY_TEXT"
    if a in UNKNOWN:
        return "REVIEW_CANDIDATE","UNINFORMATIVE_ABSTENTION"
    if re.search(r"^(こんにちは|おはよう|こんばんは)[。！! ]*$",q):
        if re.search(r"^(こんにちは|おはよう|こんばんは)[。！! ]*$",a):
            return "SUPPORTED","GREETING_MATCH"
    if re.search(r"(名前を教えて|あなたは誰)",q):
        if a=="長門有希。":return "SUPPORTED","IDENTITY_RESPONSE"
    if "GPU" in q.upper() and ("とは" in q or "って何" in q):
        if "並列" in a and ("処理" in a or "演算" in a):
            return "SUPPORTED","GPU_DEFINITION_ELEMENTS"
    if "LLM" in q.upper() and ("とは" in q or "って" in q):
        if "言語" in a and ("モデル" in a or "予測" in a):
            return "SUPPORTED","LLM_DEFINITION_ELEMENTS"
    return "ABSTAIN","NO_RELIABLE_FUNCTION_RULE"

def report(validation, labels, comparison):
    audit=analyze(validation,labels,comparison)
    originals={(r["id"],r["turn"]):r for r in validation["records"]}
    rows=[]
    for row in audit["records"]:
        key=(row["id"],row["turn"])
        original=originals[key]
        signal,reason=assess(original["question"],original.get("final_answer"))
        rows.append({"id":key[0],"turn":key[1],"shadow_decision":signal,
            "reason_code":reason,"chatgpt_relevant":row["chatgpt_relevant"],
            "gate_resolution":row["gate_resolution"],"semantic_agreement":row["semantic_agreement"]})
    return {"version":"v0.4.28.26","mode":"OFFLINE_ANSWER_FUNCTION_SHADOW",
        "not_embedding_semantics":True,"no_auto_rejection":True,
        "decision_uses_chatgpt_labels":False,"decision_uses_gate":False,
        "development_only":True,"human_ground_truth":False,"runtime_modified":False,
        "total":len(rows),"supported":sum(r["shadow_decision"]=="SUPPORTED" for r in rows),
        "review_candidates":sum(r["shadow_decision"]=="REVIEW_CANDIDATE" for r in rows),
        "abstained":sum(r["shadow_decision"]=="ABSTAIN" for r in rows),
        "supported_provisional_negative":sum(r["shadow_decision"]=="SUPPORTED" and r["chatgpt_relevant"] is False for r in rows),
        "review_provisional_positive":sum(r["shadow_decision"]=="REVIEW_CANDIDATE" and r["chatgpt_relevant"] is True for r in rows),
        "records":rows}

def main():
    p=argparse.ArgumentParser()
    for name in ("validation","labels","comparison","output"):p.add_argument("--"+name,required=True)
    a=p.parse_args()
    try:
        paths=[Path(a.validation),Path(a.labels),Path(a.comparison)]
        dst=Path(a.output)
        if any(not x.is_file() or x.is_symlink() for x in paths) or dst.exists() or dst.is_symlink():
            raise ValueError("invalid input or existing output")
        inputs=[json.loads(x.read_text(encoding="utf-8-sig")) for x in paths]
        result=report(*inputs)
        result["sha256"]={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("total","supported","review_candidates","abstained","supported_provisional_negative","review_provisional_positive")}))
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as e:
        p.exit(1,f"function shadow failed: {e}\n")
if __name__=="__main__":main()

"""v0.2.32.8: controlled, reviewable Semantic Memory expansion.

No LLM paraphrases are fabricated as ground truth. Curated variants need review.
The independent v0.2.32.7 evaluation remains excluded from training.
"""
import argparse,json,hashlib
from pathlib import Path
from staged_semantic_internalization_v02325 import read_memory
from semantic_backend_worker_v02326 import make_pair

# Deliberately small, pre-authored variants; no validation probe reuse.
VARIANTS={
 "learning":[
  "「{topic}」を学習するための基礎を知りたい",
  "{topic}を初めて学ぶ場合の進め方を教えて",
 ],
 "learning,development":[
  "{topic}の基礎を学んだうえで開発に進みたい",
  "{topic}を理解して、自分で実装する段取りを考えたい",
 ],
}
# Holds no exact v0.2.32.7 validation probes.
def canonical(record):
    c=record["context"]
    return {"topic":c.get("topic"),"purposes":list(c.get("purposes") or []),
            "relation":c.get("relation"),"action":c.get("action")}
def expand(record):
    if record["teacher_status"]!="APPROVED" or not record.get("approved_answer"):
        raise ValueError("Unapproved record cannot expand")
    original=make_pair(record)
    structure=canonical(record)
    key=",".join(structure["purposes"])
    variants=[{"id":record["id"]+":original","source_id":record["id"],
               "variant_type":"original","prompt":original["prompt"],
               "answer":original["answer"],"canonical":structure,
               "review_status":"APPROVED"}]
    for index,template in enumerate(VARIANTS.get(key,())):
        topic=structure["topic"]
        if not topic:continue
        user=template.format(topic=topic)
        labels=original["prompt"].split("\n人: ",1)[0]
        prompt=labels+"\n人: "+user+"\nAI: "
        variants.append({"id":record["id"]+":variant:"+str(index),
                         "source_id":record["id"],"variant_type":"paraphrase",
                         "prompt":prompt,"answer":original["answer"],
                         "canonical":structure,"review_status":"PENDING_REVIEW"})
    return variants
def all_rows(memory):
    records=read_memory(memory)
    eligible=[r for r in records.values() if r["teacher_status"]=="APPROVED"]
    return [row for rec in eligible for row in expand(rec)]
def export(memory,output):
    rows=all_rows(memory)
    prompts=[x["prompt"] for x in rows]
    if len(prompts)!=len(set(prompts)):raise ValueError("Duplicate training prompts")
    p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
    counts={s:sum(r["review_status"]==s for r in rows) for s in ("APPROVED","PENDING_REVIEW")}
    return counts
def load_rows(path):
    return [json.loads(s) for s in Path(path).read_text(encoding="utf-8").splitlines() if s.strip()]
def approve_variant(path,variant_id):
    rows=load_rows(path)
    match=[r for r in rows if r["id"]==variant_id]
    if len(match)!=1:raise KeyError(variant_id)
    record=match[0]
    if record["variant_type"]=="original":raise ValueError("Original approval belongs to Semantic Memory")
    record["review_status"]="APPROVED"
    Path(path).write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
def approved_training(path):
    return [{"id":r["id"],"prompt":r["prompt"],"answer":r["answer"]}
            for r in load_rows(path) if r["review_status"]=="APPROVED"]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("export","list","approve","training"))
    p.add_argument("--memory",default="data/dss_semantic_memory_v02325.jsonl")
    p.add_argument("--out",default="data/semantic_expansion_v02328.jsonl")
    p.add_argument("--id")
    a=p.parse_args()
    if a.action=="export":print(export(a.memory,a.out))
    elif a.action=="approve":
        if not a.id:raise ValueError("--id is required")
        approve_variant(a.out,a.id);print("APPROVED",a.id)
    elif a.action=="training":print(json.dumps(approved_training(a.out),ensure_ascii=False,indent=2))
    else:print(json.dumps(load_rows(a.out),ensure_ascii=False,indent=2))
if __name__=="__main__":main()

"""Build a dialogue-separated RSE review set without exporting original speech.

This is an annotation queue, not an independently human-verified holdout.
Text is never included in the default report or exported file.
"""
import argparse,hashlib,json,random
from pathlib import Path
from audit_real_persona_pairs_v013588292 import find_dialogues,extract_pairs,split_for_dialogue
from rse_accept_candidate_v013588307 import assess

def construct(source,speaker="CP",split="test",limit=30,seed=8308):
    if split not in ("val","test"):raise ValueError("Only val/test splits permitted")
    if limit<1:raise ValueError("limit must be positive")
    items=[]
    for file in sorted(find_dialogues(source).glob("*.json")):
        doc=json.loads(file.read_text(encoding="utf-8-sig"))
        did=str(doc.get("dialogue_id") or file.stem)
        if split_for_dialogue(did)!=split:continue
        pairs,issue=extract_pairs(doc)
        if issue:continue
        for question,answer,target in pairs:
            if target!=speaker or not question.strip() or not answer.strip():continue
            fingerprint=hashlib.sha256((question+"\n"+answer).encode("utf-8")).hexdigest()
            items.append({"id":fingerprint[:20],"dialogue_id":did,"question":question,
                          "answer":answer,"speaker":target})
    random.Random(seed).shuffle(items)
    seen=set();picked=[]
    for item in items:
        if item["id"] in seen:continue
        seen.add(item["id"]);picked.append(item)
        if len(picked)>=limit:break
    return picked,len(items)

def review_stub(items,split,total):
    return {"status":"HUMAN_LABELING_PENDING","split":split,"candidate_pool":total,
            "sampled":len(items),"independent_dialogue_split":True,
            "independent_from_training_speaker":False,
            "human_labels_verified":False,"raw_text_exported":False,
            "cases":[{"id":x["id"],"dialogue_id":x["dialogue_id"],
                      "question_chars":len(x["question"]),"answer_chars":len(x["answer"]),
                      "suitable":None} for x in items]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data-src/real-persona-chat")
    p.add_argument("--speaker",default="CP")
    p.add_argument("--split",choices=("val","test"),default="test")
    p.add_argument("--limit",type=int,default=30)
    p.add_argument("--report",default="results/rse_independent_holdout_v013588308.json")
    p.add_argument("--show-text",action="store_true",help="Print sampled dialogues locally only")
    a=p.parse_args()
    items,total=construct(a.source,a.speaker,a.split,a.limit)
    result=review_stub(items,a.split,total)
    path=Path(a.report);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="cases"},ensure_ascii=False,indent=2))
    if a.show_text:
        for x in items:
            print(json.dumps({"id":x["id"],"source_question":x["question"],
                              "source_answer":x["answer"]},ensure_ascii=False))
if __name__=="__main__":main()

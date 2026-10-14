#!/usr/bin/env python3
"""LLM_CHA v0.4.28.56: generation failure diagnostics, not a model-quality judge.
Compare raw A/B responses to the last user utterance; produce candidate cases for
independent blinded review. No training, model checkpoints or runtime changes.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

VERSION="v0.4.28.56"
GENERIC={"そうですね。","そうなんですね。","そうですよね。","そうですか?","そうですか？",
         "おいしいです。","そうですね!","そうですね！"}
PARTICLES=set("はがをにでとのもへやねかよって")
def keywords(text):
    return set(w for w in re.findall(r"[一-龥ァ-ヴー]{2,}|[A-Za-z]{3,}",text)
               if w not in GENERIC and w not in PARTICLES)
def examine(review, raw):
    if review.get("version")!="v0.4.28.52" or raw.get("version")!="v0.4.28.54":
        raise ValueError("version mismatch")
    indexed={x["id"]:x for x in review["records"]}
    if len(indexed)!=len(review["records"]):raise ValueError("duplicate review IDs")
    summary={arm:Counter() for arm in ("full_context","last_user_only")}
    cases=[]
    for row in raw["results"]:
        rid=row["id"]
        if rid not in indexed:raise ValueError("missing source review")
        source=indexed[rid]
        utterance=source["question"].splitlines()[-1]
        record={"id":rid,"source_line":row["source_line"],"last_utterance":utterance,
                "source_training_suitability":source["ratings"]["training_suitability"],
                "variants":{}}
        for arm in summary:
            variant=row["variants"][arm]
            answer=variant.get("response","").strip()
            if variant.get("status")!="generated":raise ValueError("unpaired generation")
            flags={"empty":not bool(answer),
                   "generic_exact":answer in GENERIC,
                   "short_response":len(answer)<10,
                   "topic_lexical_overlap":bool(keywords(utterance)&keywords(answer))}
            for flag,present in flags.items():summary[arm][flag]+=int(present)
            record["variants"][arm]={"response":answer,"diagnostic_flags":flags,
                    "blind_review":{"relevance":None,"fluency":None,"context_use":None}}
        cases.append(record)
    return {"version":VERSION,"mode":"CONSERVATIVE_GENERATION_DIAGNOSTICS",
            "sample_size":len(cases),"count_by_arm":{k:dict(v) for k,v in summary.items()},
            "cases":cases,"model_quality_winner":None,
            "precision":None,"human_verified":False,"train_ready":False,
            "runtime_modified":False,
            "limitations":["Lexical overlap and response length are only diagnostic heuristics, not quality scores.",
                "Final-turn-only overlap cannot measure use of earlier context.",
                "Blind manual review is needed before determining which arm performs better."]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review",required=True)
    p.add_argument("--generation",required=True)
    p.add_argument("--output",default="results/context_failure_diagnostics_v042856.json")
    a=p.parse_args()
    r=examine(json.loads(Path(a.review).read_text(encoding="utf-8")),
              json.loads(Path(a.generation).read_text(encoding="utf-8")))
    dest=Path(a.output)
    if dest.resolve() in (Path(a.review).resolve(),Path(a.generation).resolve()):
        raise ValueError("output cannot overwrite input")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:r[k] for k in ("version","sample_size","count_by_arm","model_quality_winner","train_ready")},ensure_ascii=False,indent=2))
if __name__=="__main__":main()

"""v0.7.9 isolated multi-knowledge benchmark fixture.

Synthetic facts are for experiments ONLY. Do not transfer to Approved Memory.
An independent protected QA file is required for retention certification.
"""
import argparse
import json
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory

FACTS=(
 ("v079実験で青い鍵の符号は何ですか","AO-17",
  ("v079の青い鍵の符号を教えて","青い鍵に対応するv079の符号は？")),
 ("v079実験で赤い橋の符号は何ですか","RB-42",
  ("v079の赤い橋の符号を教えて","赤い橋に対応するv079の符号は？")),
 ("v079実験で緑の時計の符号は何ですか","GC-83",
  ("v079の緑の時計の符号を教えて","緑の時計に対応するv079の符号は？")),
 ("v079実験で白い箱の符号は何ですか","WB-26",
  ("v079の白い箱の符号を教えて","白い箱に対応するv079の符号は？")),
)

def prepare(outdir):
    p=Path(outdir)
    p.mkdir(parents=True,exist_ok=True)
    approved=p/"approved.jsonl"
    candidates=p/"candidates.jsonl"
    holdouts=p/"holdouts.json"
    if any(x.exists() for x in (approved,candidates,holdouts)):
        raise FileExistsError("fixture exists: use a new output directory")
    memory=DualMemory(approved,candidates)
    rows=[]
    for i,(question,answer,variants) in enumerate(FACTS,1):
        record_id=memory.propose(question,answer,f"synthetic:v079:{i}")
        for variant in variants:
            rows.append({"question":variant,"reference":answer,
                         "candidate_id":record_id,"source_id":f"synthetic:v079:{i}"})
    from benchmark_generalization_v078 import validate_holdouts
    validate_holdouts(rows,[r["question"] for r in memory.candidates()])
    holdouts.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"candidate_count":len(FACTS),"holdout_count":len(rows),
            "approved_count":0,"candidates":str(candidates),"approved":str(approved),
            "holdouts":str(holdouts),"synthetic":True}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",default="results/multi_knowledge_v079_fixture")
    args=parser.parse_args()
    print(json.dumps(prepare(args.output_dir),ensure_ascii=False,indent=2))
if __name__=="__main__":main()

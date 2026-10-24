"""Audit a JSON list of {question, answer} dialogue turns."""
import argparse
import json
from pathlib import Path
from japanese_dialogue_audit_v074440 import audit_dialogue

def main():
    p=argparse.ArgumentParser()
    p.add_argument("dialogue_json")
    p.add_argument("--output",default="results/japanese_dialogue_audit_v074440.json")
    args=p.parse_args()
    turns=json.loads(Path(args.dialogue_json).read_text(encoding="utf-8"))
    if not isinstance(turns,list) or not all(isinstance(x,dict) for x in turns):
        raise ValueError("Expected a JSON list of dialogue turn objects")
    result=audit_dialogue(turns)
    dest=Path(args.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"total":result["total"],"flagged":result["flagged"],"output":str(dest)},ensure_ascii=False))
if __name__=="__main__":main()

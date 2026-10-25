"""Offline A/B runner for externally generated LLM candidates.

Input JSONL fields: question, topic, evidence (list[str]), baseline, candidate.
This script does not generate candidates or change runtime answers.
"""
import argparse
import json
from pathlib import Path
from grounded_generation_gate_v096 import compare

def run(input_path,output_path):
    records=[]
    for n,line in enumerate(Path(input_path).read_text(encoding="utf-8-sig").splitlines(),1):
        if not line.strip():
            continue
        item=json.loads(line)
        evidence=item.get("evidence",[])
        if not isinstance(evidence,list) or not all(isinstance(e,str) for e in evidence):
            raise ValueError(f"line {n}: evidence must be list[str]")
        result=compare(item.get("baseline",""),item.get("candidate",""),
                       item.get("question",""),item.get("topic",""),evidence)
        records.append({"line":n,"question":item.get("question",""),"topic":item.get("topic",""),
                        **result})
    out={"total":len(records),
         "accepted":sum(r["status"]=="ACCEPT_CANDIDATE" for r in records),
         "rejected":sum(r["status"]=="KEEP_BASELINE" for r in records),
         "records":records}
    Path(output_path).parent.mkdir(parents=True,exist_ok=True)
    Path(output_path).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args=parser.parse_args()
    result=run(args.input,args.output)
    print(json.dumps({k:v for k,v in result.items() if k!="records"},ensure_ascii=False))
if __name__=="__main__":main()

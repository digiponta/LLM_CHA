"""Run v0.7.14 read-only candidate/unknown audit with real Experimental Adapter."""
import argparse
import json
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from experimental_backend_v0711 import ExperimentalBackend
from multi_candidate_audit_v0714 import evaluate_probes

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--approved",default="data/approved_v071.jsonl")
    p.add_argument("--candidates",default="data/candidates_v071.jsonl")
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--adapter",default="results/adapter_sweep_v077_full/r16_e30_lr1e-03/experimental-adapter.pt")
    p.add_argument("--report",default="results/multi_candidate_audit_v0714.json")
    p.add_argument("--unknown",action="append",default=[],help="Known absent question; repeatable")
    a=p.parse_args()
    memory=DualMemory(a.approved,a.candidates)
    backend=ExperimentalBackend(a.base,a.tokenizer,a.adapter)
    result=evaluate_probes(memory,backend,unknown_questions=a.unknown)
    path=Path(a.report)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()

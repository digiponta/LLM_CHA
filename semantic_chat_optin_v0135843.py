"""v0.13.58.43: opt-in, read-only Semantic Adapter CLI.

Provides chat-like interactive use without modifying chat.py's standard loop.
Supports BOM or BOM-less UTF-8, missing stores => NOT_INITIALIZED.
Experimental fixture-only output; never promotes to production.
"""
import argparse,json
from pathlib import Path
from semantic_proposition_v1090 import Proposition
from truth_state_v10103 import TruthRecord
from runtime_semantic_adapter_v0135842 import adapter,read_manifest
from provenance_semantic_memory_v0135841 import answer

def jsonl(path):
    raw=path.read_text(encoding="utf-8-sig",errors="strict")
    return [json.loads(x) for x in raw.splitlines() if x.strip()]
def load_sources(proposition_path,truth_path,manifest_path):
    if not proposition_path.is_file() or not truth_path.is_file():
        return {"status":"NOT_INITIALIZED","eligible":[],"denied":[]}
    if not manifest_path.is_file():
        return {"status":"NO_EXPLICIT_APPROVAL_MANIFEST","eligible":[],"denied":[]}
    props=[Proposition(str(x["subject"]),str(x["value"])) for x in jsonl(proposition_path)]
    truths=[TruthRecord(concept=str(x["concept"]),state=str(x["state"]),
        reason=str(x.get("reason","")),source=str(x.get("source","manual"))) for x in jsonl(truth_path)]
    approved,denied=adapter(props,truths,read_manifest(manifest_path))
    return {"status":"READY" if approved else "NO_ELIGIBLE_FACTS",
            "eligible":approved,"denied":denied}
def respond(question,loaded):
    if loaded["status"]!="READY":
        return {"status":"ABSTAIN","reason":loaded["status"],"answer":None,"facts":[]}
    return answer(question,loaded["eligible"])
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--propositions",type=Path,default=Path("data/semantic_propositions_v1090.jsonl"))
    p.add_argument("--truth",type=Path,default=Path("data/truth_state_v10103.jsonl"))
    p.add_argument("--manifest",type=Path,default=Path("data/runtime_adapter_manifest_example_v0135842.json"))
    p.add_argument("--question")
    p.add_argument("--interactive",action="store_true")
    a=p.parse_args()
    loaded=load_sources(a.propositions,a.truth,a.manifest)
    print(json.dumps({"store_status":loaded["status"],"eligible":len(loaded["eligible"]),
                      "denied":len(loaded["denied"]),"mode":"EXPERIMENTAL_READ_ONLY"},ensure_ascii=False))
    if a.question:
        print(json.dumps(respond(a.question,loaded),ensure_ascii=False))
    if a.interactive:
        while True:
            try:q=input("Semantic> ").strip()
            except (EOFError,KeyboardInterrupt):break
            if q in ("/exit","/quit"):break
            if q:print(json.dumps(respond(q,loaded),ensure_ascii=False))
if __name__=="__main__":main()

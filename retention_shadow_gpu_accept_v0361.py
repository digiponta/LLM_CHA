"""v0.3.6.1 GPU shadow ON/OFF equivalence acceptance.

Separate subprocesses, isolated synthetic corpus/overlay/checkpoint copies.
Compare user-visible answers and Truth/Proposition/Recovery trace signatures.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import os

from context_recovery_gpu_accept_v023344 import TOPIC, execute as recovery_execute
from grounded_expansion_v0233826 import PropositionCursor
from proposition_truth_v0233827 import proposition_id
from retrieval_first_runtime_v1012161 import resolve_subject

COMPARE_PREFIXES = (
    "AI>", "[proposition-id=", "[grounded-expansion=", "[retrieval-first=",
    "[gate=", "[truth warning:", "[context-save=", "[context-load=",
    "[topic route:", "[0 generated probe tokens", "[conversation history cleared]",
)

def signature(output:str)->list[str]:
    return [line.strip() for line in output.splitlines()
            if line.strip().startswith(COMPARE_PREFIXES)]

def execute(commands, corpus, checkpoint, overlay, timeout, python, enabled):
    # Force the setting even when inherited from the caller's shell.
    env=os.environ.copy()
    env.update({
        "LLM_CHA_MULTITOPIC":"1",
        "LLM_CHA_CONTEXT_RECOVERY":"1",
        "LLM_CHA_RETENTION_ACTIVE":"0",
        "LLM_CHA_RETENTION_PINS":"",
        "LLM_CHA_CONTEXT_PATH":str(checkpoint),
        "LLM_CHA_PROPOSITION_TRUTH":str(overlay),
        "LLM_CHA_RETENTION_SHADOW":"1" if enabled else "0",
        "PYTHONIOENCODING":"utf-8",
        "PYTHONUNBUFFERED":"1",
    })
    returncode=subprocess.run(
        [python,"-u","chat.py","--corpus-memory",str(corpus)],
        input="\n".join([*commands,"/exit",""]),
        text=True,encoding="utf-8",errors="replace",
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        env=env,timeout=timeout,check=False,
    )
    return returncode.returncode,returncode.stdout

def run(source:Path, timeout=240, python=sys.executable):
    source=source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    hit=resolve_subject(source,TOPIC)
    statements=PropositionCursor.split(hit.answer) if hit.hit else []
    if len(statements)<3:
        raise ValueError("corpus needs three distinct propositions")
    ids=[proposition_id(TOPIC,text,hit.provenance) for text in statements[:3]]
    original=source.read_bytes()
    runs={}
    with tempfile.TemporaryDirectory(prefix="llm-cha-shadow-equivalence-") as directory:
        for enabled in (False,True):
            mode="on" if enabled else "off"
            root=Path(directory)/mode
            root.mkdir()
            corpus=root/"corpus.jsonl"
            checkpoint=root/"checkpoint.json"
            overlay=root/"overlay.jsonl"
            shutil.copyfile(source,corpus)
            overlay.write_text("",encoding="utf-8")
            stages={}
            commands=[
                ("save",[f"{TOPIC}について教えて","もう少し詳しく","/context-save","/retention-stats"]),
                ("restart",["/context-load","もう少し詳しく","/retention-stats"]),
            ]
            for stage,inputs in commands:
                rc,output=execute(inputs,corpus,checkpoint,overlay,timeout,python,enabled)
                stages[stage]={"code":rc,"signature":signature(output),"stdout":output}
            overlay.write_text("".join(json.dumps({
                "proposition_id":pid,"truth_state":"OUTDATED",
                "provenance":"synthetic-shadow-equivalence-fixture"
            },ensure_ascii=False)+"\n" for pid in ids[:2]),encoding="utf-8")
            rc,output=execute(["/context-load","もう少し詳しく","/retention-stats"],
                              corpus,checkpoint,overlay,timeout,python,enabled)
            stages["revoked"]={"code":rc,"signature":signature(output),"stdout":output}
            runs[mode]={"stages":stages,
                       "corpus_unchanged":corpus.read_bytes()==original,
                       "checkpoint_created":checkpoint.is_file()}
    checks={}
    for stage in ("save","restart","revoked"):
        a=runs["off"]["stages"][stage]
        b=runs["on"]["stages"][stage]
        checks[f"{stage}_both_exit_zero"]=a["code"]==b["code"]==0
        checks[f"{stage}_truth_response_equivalent"]=a["signature"]==b["signature"]
        checks[f"{stage}_shadow_enabled_banner"]="[adaptive retention shadow enabled" in b["stdout"]
        checks[f"{stage}_shadow_disabled_banner"]="[adaptive retention shadow enabled" not in a["stdout"]
    checks.update({
        "both_corpus_copies_unchanged":all(r["corpus_unchanged"] for r in runs.values()),
        "both_checkpoints_created":all(r["checkpoint_created"] for r in runs.values()),
        "original_corpus_unchanged":source.read_bytes()==original,
        "save_contains_first_id":all(f"proposition-id={ids[0]}" in runs[m]["stages"]["save"]["stdout"] for m in runs),
        "restart_contains_third_id":all(f"proposition-id={ids[2]}" in runs[m]["stages"]["restart"]["stdout"] for m in runs),
        "revoked_rejects_saved":all("[context-load=OK, retained=0, rejected=2]" in runs[m]["stages"]["revoked"]["stdout"] for m in runs),
        "on_stats_present":all('"mode": "shadow"' in runs["on"]["stages"][stage]["stdout"] for stage in ("save","restart","revoked")),
        "off_stats_disabled":all("[adaptive retention shadow disabled]" in runs["off"]["stages"][stage]["stdout"] for stage in ("save","restart","revoked")),
    })
    return {"version":"v0.3.6.1","pass":all(checks.values()),"checks":checks,
            "exit_codes":{mode:{stage:x["code"] for stage,x in data["stages"].items()} for mode,data in runs.items()},
            "signatures":{mode:{stage:x["signature"] for stage,x in data["stages"].items()} for mode,data in runs.items()}}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--corpus",default="data/subject_keyed_corpus_memory_v101216.jsonl")
    parser.add_argument("--timeout",type=int,default=240)
    parser.add_argument("--report",default="results/retention_shadow_gpu_accept_v0361.json")
    args=parser.parse_args()
    result=run(Path(args.corpus),args.timeout)
    destination=Path(args.report)
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="signatures"},ensure_ascii=False,indent=2))
    print("report:",destination)
    return 0 if result["pass"] else 1

if __name__=="__main__":
    sys.exit(main())

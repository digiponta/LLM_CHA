"""v0.2.34.4 GPU acceptance: restart recovery and changed Truth Overlay.

Three isolated chat.py subprocesses. Corpus and checkpoint are temporary copies.
Synthetic review states exercise filtering, NOT the truth of source statements.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from longterm_context_v02340 import ContextCheckpoint
from proposition_truth_v0233827 import proposition_id
from retrieval_first_runtime_v1012161 import resolve_subject
from grounded_expansion_v0233826 import PropositionCursor

TOPIC="宇宙"

def execute(commands, corpus, checkpoint, overlay, timeout, python):
    env=os.environ.copy()
    env.update({
        "LLM_CHA_MULTITOPIC":"1",
        "LLM_CHA_CONTEXT_RECOVERY":"1",
        "LLM_CHA_CONTEXT_PATH":str(checkpoint),
        "LLM_CHA_PROPOSITION_TRUTH":str(overlay),
        "PYTHONIOENCODING":"utf-8",
        "PYTHONUNBUFFERED":"1",
    })
    result=subprocess.run(
        [python,"-u","chat.py","--corpus-memory",str(corpus)],
        input="\n".join([*commands,"/exit",""]),
        encoding="utf-8",errors="replace",stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,env=env,timeout=timeout,check=False
    )
    return result.returncode,result.stdout

def run(source:Path,timeout=240,python=sys.executable):
    source=source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    hit=resolve_subject(source,TOPIC)
    parts=PropositionCursor.split(hit.answer) if hit.hit else []
    if len(parts)<3:
        raise ValueError("expected at least three distinct source propositions")
    ids=[proposition_id(TOPIC,s,hit.provenance) for s in parts[:3]]
    with tempfile.TemporaryDirectory(prefix="llm-cha-context-gpu-") as tmp:
        root=Path(tmp)
        corpus=root/"corpus.jsonl"
        checkpoint=root/"checkpoint.json"
        overlay=root/"truth.jsonl"
        shutil.copyfile(source,corpus)
        original=corpus.read_bytes()
        overlay.write_text("",encoding="utf-8")
        rc1,out1=execute(
            [f"{TOPIC}について教えて","もう少し詳しく","/context-save"],
            corpus,checkpoint,overlay,timeout,python)
        saved=checkpoint.is_file()
        saved_ids=[]
        if saved:
            try:
                saved_ids=ContextCheckpoint.restore(checkpoint.read_text(encoding="utf-8")).topics.get(TOPIC,[])
            except (ValueError,TypeError,KeyError):
                pass
        # A genuinely independent child process must continue from the third ID.
        rc2,out2=execute(["/context-load","もう少し詳しく"],
                          corpus,checkpoint,overlay,timeout,python)
        # Simulate a later review rejecting BOTH previously displayed propositions.
        # No corpus modifications and no writes to user's production overlay.
        overlay.write_text("".join(
            json.dumps({"proposition_id":pid,"truth_state":"OUTDATED",
                       "provenance":"synthetic-recovery-revocation-fixture"},
                       ensure_ascii=False)+"\n" for pid in ids[:2]
        ),encoding="utf-8")
        rc3,out3=execute(["/context-load","もう少し詳しく"],
                          corpus,checkpoint,overlay,timeout,python)
        checks={
            "save_process_exit_zero":rc1==0,
            "checkpoint_created":saved,
            "two_ids_saved":len(saved_ids)==2 and saved_ids==ids[:2],
            "save_confirmed":"[context-save=OK, topics=1]" in out1,
            "restart_process_exit_zero":rc2==0,
            "restart_restores_two":"[context-load=OK, retained=2, rejected=0]" in out2,
            "restart_third_id":f"proposition-id={ids[2]}" in out2,
            "restart_no_replay":all(f"proposition-id={i}" not in out2 for i in ids[:2]),
            "revoked_process_exit_zero":rc3==0,
            "revocation_drops_both":"[context-load=OK, retained=0, rejected=2]" in out3,
            "revoked_topic_not_reused":"参照できる話題がありません" in out3,
            "revoked_no_proposition_output":"[proposition-id=" not in out3,
            "corpus_copy_unchanged":corpus.read_bytes()==original,
            "original_corpus_unchanged":source.read_bytes()==original,
        }
        return {"version":"v0.2.34.4","pass":all(checks.values()),"checks":checks,
                "returncodes":[rc1,rc2,rc3],
                "transcripts":{"save":out1,"restart":out2,"revoked":out3}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--corpus",default="data/subject_keyed_corpus_memory_v101216.jsonl")
    p.add_argument("--timeout",type=int,default=240)
    p.add_argument("--report",default="results/context_recovery_gpu_accept_v023344.json")
    args=p.parse_args()
    result=run(Path(args.corpus),args.timeout)
    dest=Path(args.report)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="transcripts"},ensure_ascii=False,indent=2))
    print("report:",dest)
    return 0 if result["pass"] else 1

if __name__=="__main__":
    sys.exit(main())

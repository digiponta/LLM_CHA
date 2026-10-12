"""LLM_CHA v0.3.6.6 GPU grounded revisit acceptance.

Isolated corpus and overlay; verifies that evicted topics restart grounded
proposition pagination without carrying stale cursor state or free generation.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

COMMANDS = [
    "宇宙について", "もう少し詳しく",
    "GPUとは", "CPUとは", "数学とは", "文学とは", "物理とは",
    "時間とは", "小説とは", "科学とは", "化学とは",
    "/retention-stats", "宇宙について", "/retention-stats",
]

def blocks(output):
    # Piped input() does not echo the typed command.
    return re.split(r"(?m)^You> ", output)[1:]

def at(output,index):
    items=blocks(output)
    return items[index] if len(items)>index else ""

def pid(text):
    m=re.search(r"\[proposition-id=([a-f0-9]+),",text)
    return m.group(1) if m else None

def stats(text):
    for line in text.splitlines():
        if line.strip().startswith("{"):
            try:return json.loads(line)
            except json.JSONDecodeError: pass
    return None

def execute(corpus,overlay,timeout,python):
    env=os.environ.copy()
    env.update({
        "LLM_CHA_MULTITOPIC":"1",
        "LLM_CHA_RETENTION_ACTIVE":"1",
        "LLM_CHA_RETENTION_SHADOW":"0",
        "LLM_CHA_RETENTION_PINS":"",
        "LLM_CHA_CONTEXT_RECOVERY":"0",
        "LLM_CHA_PROPOSITION_TRUTH":str(overlay),
        "PYTHONIOENCODING":"utf-8",
        "PYTHONUNBUFFERED":"1",
    })
    return subprocess.run(
        [python,"-u","chat.py","--corpus-memory",str(corpus)],
        input="\n".join([*COMMANDS,"/exit",""]),
        text=True,encoding="utf-8",errors="replace",
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        env=env,timeout=timeout,check=False,
    )

def run(source,timeout=240,python=sys.executable):
    source=Path(source).resolve()
    if not source.is_file():raise FileNotFoundError(source)
    initial=source.read_bytes()
    with tempfile.TemporaryDirectory(prefix="llm-cha-revisit-") as tmp:
        corpus=Path(tmp)/"corpus.jsonl"
        overlay=Path(tmp)/"overlay.jsonl"
        shutil.copyfile(source,corpus)
        overlay.write_text("",encoding="utf-8")
        child=execute(corpus,overlay,timeout,python)
        output=child.stdout
        corpus_same=corpus.read_bytes()==initial
    first=at(output,0)
    followup=at(output,1)
    before=stats(at(output,11))
    revisit=at(output,12)
    after=stats(at(output,13))
    p_first=pid(first)
    p_followup=pid(followup)
    p_revisit=pid(revisit)
    checks={
        "process_exit_zero":child.returncode==0,
        "original_corpus_unchanged":source.read_bytes()==initial,
        "copy_corpus_unchanged":corpus_same,
        "all_commands_executed":len(blocks(output))>=len(COMMANDS),
        "initial_grounded":bool(p_first) and "[retrieval-first=HIT" in first,
        "initial_no_generation":"0 generated probe tokens" in first,
        "followup_grounded":bool(p_followup) and "[grounded-followup=HIT" in followup,
        "followup_advances":bool(p_first) and bool(p_followup) and p_first!=p_followup,
        "eviction_occurred":bool(before) and before.get("evictions",0)>0,
        "universe_evicted":bool(before) and "宇宙" not in before.get("topics",[]),
        "revisit_grounded":bool(p_revisit) and "[retrieval-first=HIT" in revisit,
        "revisit_starts_fresh":bool(p_first) and p_revisit==p_first,
        "revisit_no_generation":"0 generated probe tokens" in revisit,
        "universe_readmitted":bool(after) and "宇宙" in after.get("topics",[]),
        "truth_state_visible":"truth_state=" in first and "truth_state=" in revisit,
        "capacity_compliant":bool(after) and len(after.get("topics",[]))<=after.get("capacity",0),
    }
    return {"version":"v0.3.6.6","pass":all(checks.values()),
            "checks":checks,"returncode":child.returncode,
            "first_proposition":p_first,"followup_proposition":p_followup,
            "revisit_proposition":p_revisit,
            "before":before,"after":after,"transcript":output}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--corpus",default="data/subject_keyed_corpus_memory_v101216.jsonl")
    parser.add_argument("--timeout",type=int,default=240)
    parser.add_argument("--report",default="results/grounded_revisit_gpu_v0366.json")
    args=parser.parse_args()
    result=run(args.corpus,timeout=args.timeout)
    output=Path(args.report)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({key:value for key,value in result.items() if key!="transcript"},
                     ensure_ascii=False,indent=2))
    print("report:",output)
    return 0 if result["pass"] else 1

if __name__=="__main__":sys.exit(main())

"""v0.3.6.4 Active Retention three-mode GPU acceptance.

Separate subprocesses with forced environment, isolated overlay and corpus.
Active is compared to baseline only on decisions expected to be invariant.
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

TOPICS=("宇宙","GPU","CPU","数学","文学","物理","時間","小説","科学","化学")
COMMANDS=[*(f"{topic}とは" for topic in TOPICS),
          "/retention-stats","宇宙の話に戻って","/reset",
          "/retention-stats","それについて"]

def execute(mode,corpus,overlay,timeout,python):
    env=os.environ.copy()
    env.update({"LLM_CHA_MULTITOPIC":"1",
                "LLM_CHA_RETENTION_ACTIVE":"1" if mode=="active" else "0",
                "LLM_CHA_RETENTION_SHADOW":"1" if mode=="shadow" else "0",
                "LLM_CHA_RETENTION_PINS":"宇宙,GPU" if mode=="active" else "",
                "LLM_CHA_CONTEXT_RECOVERY":"0",
                "LLM_CHA_PROPOSITION_TRUTH":str(overlay),
                "PYTHONIOENCODING":"utf-8","PYTHONUNBUFFERED":"1"})
    process=subprocess.run([python,"-u","chat.py","--corpus-memory",str(corpus)],
        input="\n".join([*COMMANDS,"/exit",""]),text=True,encoding="utf-8",
        errors="replace",stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        env=env,timeout=timeout,check=False)
    return process.returncode,process.stdout

def segments(output):
    # input() prints "You> " but does NOT echo piped stdin.
    # Match prompts by command order, not by searching input text in stdout.
    import re
    blocks=re.split(r"(?m)^You> ",output)
    return blocks[1:]

def segment(output,command,occurrence=0):
    indices=[i for i,c in enumerate(COMMANDS) if c==command]
    if occurrence>=len(indices):return None
    blocks=segments(output)
    index=indices[occurrence]
    return blocks[index] if index<len(blocks) else None

def diagnostic(output,occurrence=0):
    block=segment(output,"/retention-stats",occurrence)
    if block is None:return None
    for line in block.splitlines():
        if line.lstrip().startswith("{"):
            try:return json.loads(line.strip())
            except json.JSONDecodeError:return None
    return None

def run(source:Path,timeout=240,python=sys.executable):
    source=source.resolve()
    if not source.is_file():raise FileNotFoundError(source)
    original=source.read_bytes()
    reports={}
    with tempfile.TemporaryDirectory(prefix="llm-cha-active-gpu-") as directory:
        for mode in ("off","shadow","active"):
            folder=Path(directory)/mode
            folder.mkdir()
            corpus=folder/"corpus.jsonl"
            overlay=folder/"overlay.jsonl"
            shutil.copyfile(source,corpus)
            overlay.write_text("",encoding="utf-8")
            code,output=execute(mode,corpus,overlay,timeout,python)
            reports[mode]={"returncode":code,"transcript":output,
                "diagnostic":diagnostic(output),
                "corpus_unchanged":corpus.read_bytes()==original}
    checks={}
    for mode in reports:
        checks[mode+"_exit_zero"]=reports[mode]["returncode"]==0
        checks[mode+"_corpus_unchanged"]=reports[mode]["corpus_unchanged"]
    checks["original_corpus_unchanged"]=source.read_bytes()==original
    active=reports["active"]
    diag=active["diagnostic"]
    checks["active_banner"]="[adaptive retention ACTIVE enabled" in active["transcript"]
    checks["active_diagnostic"]=bool(diag) and diag.get("mode")=="active"
    checks["capacity_compliant"]=bool(diag) and len(diag.get("topics",[]))<=diag.get("capacity",0)
    checks["pinned_universe"]=bool(diag) and "宇宙" in diag.get("pins",[])
    checks["pinned_gpu"]=bool(diag) and "GPU" in diag.get("pins",[])
    checks["topic_evicted"]=bool(diag) and diag.get("evictions",0)>0
    checks["return_works"]="[topic route: 宇宙]" in (segment(active["transcript"],"宇宙の話に戻って") or "")
    checks["reset_stats_empty"]=bool(segment(active["transcript"],"/reset")) and (diagnostic(active["transcript"],1) or {}).get("topics")==[]
    checks["ambiguous_after_reset"]="参照できる話題がありません" in (segment(active["transcript"],"それについて") or "")
    checks["shadow_stats"]=reports["shadow"]["diagnostic"] is not None and reports["shadow"]["diagnostic"].get("mode")=="shadow"
    checks["off_stats_disabled"]="[adaptive retention shadow disabled]" in reports["off"]["transcript"]
    # For matched, retrieval-dominant queries, truth warnings and answers must be identical.
    for command in ("宇宙とは","GPUとは","CPUとは"):
        def key_lines(text):
            if text is None:return []
            return [line.strip() for line in text.splitlines() if line.startswith(
                ("AI> ","[truth warning:","[proposition-id=","[retrieval-first=","[gate="))]
        baseline=key_lines(segment(reports["off"]["transcript"],command))
        shadow=key_lines(segment(reports["shadow"]["transcript"],command))
        candidate=key_lines(segment(active["transcript"],command))
        checks["invariant_"+command]=bool(baseline) and baseline==shadow==candidate
    return {"version":"v0.3.6.4","pass":all(checks.values()),"checks":checks,
        "exit_codes":{mode:r["returncode"] for mode,r in reports.items()},
        "diagnostics":{mode:r["diagnostic"] for mode,r in reports.items()},
        "transcripts":{mode:r["transcript"] for mode,r in reports.items()}}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--corpus",default="data/subject_keyed_corpus_memory_v101216.jsonl")
    parser.add_argument("--timeout",type=int,default=240)
    parser.add_argument("--report",default="results/active_retention_gpu_accept_v0364.json")
    args=parser.parse_args()
    result=run(Path(args.corpus),args.timeout)
    target=Path(args.report)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="transcripts"},ensure_ascii=False,indent=2))
    print("report:",target)
    return 0 if result["pass"] else 1

if __name__=="__main__":sys.exit(main())

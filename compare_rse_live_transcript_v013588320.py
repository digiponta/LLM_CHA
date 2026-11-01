"""Compare captured *actual* chat.py console dialogue against read-only Theme RSE.

Does not execute chat.py, synthesize replies or edit knowledge stores.
Require the user to capture a real console transcript first.
"""
import argparse,json,re
from pathlib import Path
from compare_rse_runtime_theme_v013588319 import compare

PROMPT=re.compile(r"^(?:You>|あなた:|User:)\s*(.*)$")
ANSWER=re.compile(r"^(?:AI>|AI:|Assistant:)\s*(.*)$")
ROUTE=re.compile(r"^\[(?:route|knowledge_state|truth_state)=[^\]]+\]")

def parse_transcript(text):
    turns=[]
    current=None
    for raw in text.splitlines():
        line=raw.strip()
        m=PROMPT.match(line)
        if m:
            if current is not None:turns.append(current)
            current={"query":m.group(1).strip(),"answer":None,"route_lines":[]}
            continue
        m=ANSWER.match(line)
        if m and current is not None:
            content=m.group(1).strip()
            if current["answer"] is None:current["answer"]=content
            else:current["answer"]+="\n"+content
        elif current is not None and ROUTE.match(line):
            current["route_lines"].append(line)
    if current is not None:turns.append(current)
    return [t for t in turns if t["query"]]

def evaluate(turns,unified,truth,candidates):
    reports=[]
    for t in turns:
        x=compare(t["query"],unified,truth,candidates)
        legacy=x["legacy_unified"]
        expected=legacy["answer"]
        actual=t["answer"]
        same=(actual==expected) if actual is not None and expected is not None else None
        rse=x["rse_shadow"]
        reports.append({
            "query":t["query"],"observed_chat_answer":actual,
            "observed_route_lines":t["route_lines"],
            "observed_answer_present":actual is not None,
            "unified_component_answer":expected,
            "observed_equals_unified":same,
            "rse_state":rse["status"],"rse_answer":rse.get("answer"),
            "unified_preserved_in_shadow":x["legacy_answer_preservation"],
            "classification":(
                "NO_OBSERVED_ANSWER" if actual is None else
                "UNIFIED_MATCH_OBSERVED" if same is True else
                "UNIFIED_DIFFERENT_OBSERVED" if same is False else
                "RSE_SUGGESTION_NOT_LIVE" if rse["status"]=="ANSWER_SELECTED" else
                "NO_UNIFIED_REFERENCE"
            )
        })
    return {"status":"REAL_TRANSCRIPT_SHADOW_COMPARISON",
            "source":"USER_CAPTURED_CHAT_PY_TRANSCRIPT",
            "cases":reports,"observed_turns":len(reports),
            "chat_py_executed_by_this_script":False,
            "runtime_modified":False,"storage_modified":False,
            "limitations":"Console logs may omit route info; source must be captured from real chat.py. Identical output does not prove which route executed."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--transcript",required=True,help="Text copied from an actual chat.py session (You>/AI> lines)")
    p.add_argument("--unified",default="data/unified_semantic_memory_v1090.jsonl")
    p.add_argument("--truth",default="data/truth_state_v10103.jsonl")
    p.add_argument("--candidates",default="data/rse_theme_examples_v013588312.json")
    p.add_argument("--output",default="results/rse_live_transcript_shadow_v013588320.json")
    a=p.parse_args()
    transcript=Path(a.transcript).read_text(encoding="utf-8-sig")
    turns=parse_transcript(transcript)
    if not turns:raise SystemExit("NO_PARSED_TURNS: check You> / AI> formatting")
    candidates=json.loads(Path(a.candidates).read_text(encoding="utf-8-sig"))["candidates"]
    report=evaluate(turns,a.unified,a.truth,candidates)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"observed_turns":len(turns),
        "cases":[{"query":t["query"],"classification":t["classification"],
                  "rse_state":t["rse_state"],"observed_answer":t["observed_chat_answer"]}
                  for t in report["cases"]]},ensure_ascii=False,indent=2))
if __name__=="__main__":main()

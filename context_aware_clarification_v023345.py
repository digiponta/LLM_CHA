"""LLM_CHA v0.2.33.45: context-aware clarification and bounded-turn audit.

Uses real purpose-confidence DSS for ordinary turns and experimental JSON
shadow candidate store. Does not alter production Semantic Memory or LLM.
Previously revealed v0.2.33.44 cases are DEVELOPMENT, not unseen evaluation.
"""
import argparse,json,re,tempfile,unicodedata
from pathlib import Path
from clarification_normalization_v023343 import NormalizedClarificationBridge
from semantic_candidate_adapter_v023337 import JsonCandidateStore

ANSWER_ALIASES={
    "cursor":("cursor","カーソル","カーソルの方","カーソル実験"),
    "semantic_memory":("semantic_memory","semantic memory","意味記憶","意味記憶の実験","セマンティックメモリ")
}
POLITE_SUFFIXES=("でお願いします","をお願いします","のほうです","の方です","がいいです","にしてください")
SWITCH_PATTERNS=(r"^(?:一旦|いったん)?(?:ほか|他|別)の話(?:をしましょう|にしましょう|がしたい)",
                 r"^(?:その前に|先に)(?:別|違う|ほか|他)(?:の)?(?:件|話|こと)(?:を)?(?:聞きたい|相談したい|話したい)",
                 r"^(?:別件|別のこと)(?:を|について)?(?:先に)?(?:相談|話)")
def norm(text):
    return unicodedata.normalize("NFKC",text).strip().lower()
def decide(text,allowed=("cursor","semantic_memory")):
    value=norm(text)
    # Reject compound and negated expressions before attempting an answer.
    if re.search(r"(ではなく|じゃなく|ではない|じゃない|いや|または|あるいは|両方|どちらも|と.*(?:カーソル|意味記憶))",value):
        return {"intent":"UNCERTAIN","canonical":None,"reason":"conflict_or_negation"}
    if any(re.search(x,value) for x in SWITCH_PATTERNS):
        return {"intent":"SWITCH","canonical":None,"reason":"new_topic"}
    variants={norm(x):key for key,strings in ANSWER_ALIASES.items() for x in strings if key in allowed}
    for alias,key in list(variants.items()):
        for suffix in POLITE_SUFFIXES:variants[alias+norm(suffix)]=key
    match=variants.get(value)
    if match:return {"intent":"ANSWER","canonical":match,"reason":"single_allowed_answer"}
    return {"intent":"UNCERTAIN","canonical":None,"reason":"unresolved"}

class ContextAwareBridge(NormalizedClarificationBridge):
    def receive(self,text,context):
        resolver=self._resolver(context)
        if resolver.pending and not resolver.pending.get("candidate"):
            d=decide(text,resolver.pending["choices"])
            if d["intent"]=="ANSWER":
                r=super().receive(d["canonical"],context)
                r["context_decision"]=d
                return r
            if d["intent"]=="SWITCH":
                resolver.clear()
                r=super().receive(text,context)
                r["context_decision"]=d
                r["interruption"]="context_aware_switch"
                return r
            # Guard against v0.2.33.43 and v0.2.33.40 fallback
            # treating a conflict as a canonical answer.
            if d["reason"]=="conflict_or_negation":
                resolver.pending["attempts"]+=1
                if resolver.pending["attempts"]>=resolver.maximum:
                    resolver.clear()
                    return {"status":"abstain","route":"reference_resolution","context_decision":d}
                return {"status":"clarify","route":"reference_resolution",
                        "response":"対象は1つですか？ CursorかSemantic Memoryを指定してください。",
                        "context_decision":d}
        return super().receive(text,context)

# Developer diagnostics: the evaluation in v0.2.33.44 has already been seen.
DEVELOPMENT=[
 ("polite_cursor","昨日の実験の続きをやって","カーソルでお願いします","confirm","cursor"),
 ("polite_memory","昨日の実験の続きをやって","意味記憶のほうです","confirm","semantic_memory"),
 ("switch_else","昨日の実験の続きをやって","一旦ほかの話をしましょう","dss",None),
 ("switch_before","昨日の実験の続きをやって","その前に違う件を聞きたい","dss",None),
 ("negation","昨日の実験の続きをやって","意味記憶ではなくカーソル","clarify",None),
 ("multiple","昨日の実験の続きをやって","カーソルと意味記憶の両方","clarify",None)]
def evaluate():
    cases=[]
    for name,first,follow,want_status,want_value in DEVELOPMENT:
        with tempfile.TemporaryDirectory() as td:
            store=JsonCandidateStore(Path(td)/"candidate.json")
            bridge=ContextAwareBridge(store)
            initial=bridge.receive(first,"evaluation")
            actual=bridge.receive(follow,"evaluation")
            rows=store._read()["records"]
            cases.append({"id":name,"expected_status":want_status,"expected_value":want_value,
                "actual_status":actual["status"],"actual_value":actual.get("value"),
                "match":actual["status"]==want_status and
                        (want_value is None or actual.get("value")==want_value),
                "approved_without_confirmation":sum(r["status"]=="approved" for r in rows),
                "additional_questions":int(actual["status"]=="clarify"),
                "trace":[initial,actual]})
    return {"version":"v0.2.33.45","evaluated_on":"previously exposed development cases",
            "correct":sum(x["match"] for x in cases),"total":len(cases),
            "false_approvals":sum(x["approved_without_confirmation"] for x in cases),
            "additional_questions":sum(x["additional_questions"] for x in cases),
            "cases":cases,"limitations":["Not independent holdout",
             "Deterministic pattern matching, not a learned semantic classifier",
             "No real DSS referent understanding; no production memory writes",
             "Further unobserved human-labelled cases required"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/context_aware_clarification_v023345.json")
    a=p.parse_args()
    path=Path(a.out)
    if path.exists():raise FileExistsError("Refusing overwrite")
    result=evaluate()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({k:result[k] for k in ("correct","total","false_approvals","additional_questions")},indent=2))
    print("Saved",path)
if __name__=="__main__":main()

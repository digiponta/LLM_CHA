"""v0.2.33.43 — explicit clarification-intent normalizer.

Three labels: ANSWER, SWITCH, UNCERTAIN. Narrow deterministic heuristics,
not general semantic classification or live Semantic Memory integration.
"""
import argparse,json,re,unicodedata
from pathlib import Path
from clarification_interruption_v023340 import InterruptibleDSSBridge
from semantic_candidate_adapter_v023337 import JsonCandidateStore

ALIASES={
 "cursor":("cursor","カーソル","カーソルの方","カーソル実験"),
 "semantic_memory":("semantic_memory","semantic memory","意味記憶","意味記憶の実験","セマンティックメモリ"),
}
SWITCH_PATTERNS=(r"^(?:別件|別のこと)(?:を|について)?(?:先に)?(?:相談|話)",
                 r"^(?:話を変えて|話題を変えて|別の話にしよう)")
UNCERTAIN_PATTERNS=(r"^(?:分からない|わからない|よく分からない|決められない|まだ迷っている)$",)
def normalize(text):
    return unicodedata.normalize("NFKC",text).strip().lower()
def classify(text):
    value=normalize(text)
    if any(re.search(p,value) for p in SWITCH_PATTERNS):
        return {"intent":"SWITCH","canonical":None,"reason":"explicit_indirect_switch"}
    if any(re.search(p,value) for p in UNCERTAIN_PATTERNS):
        return {"intent":"UNCERTAIN","canonical":None,"reason":"explicit_uncertainty"}
    candidates=[key for key,phrases in ALIASES.items()
                if any(value==normalize(phrase) for phrase in phrases)]
    if len(candidates)==1:
        return {"intent":"ANSWER","canonical":candidates[0],"reason":"unambiguous_alias"}
    return {"intent":"UNCERTAIN","canonical":None,"reason":"not_matched"}

class NormalizedClarificationBridge(InterruptibleDSSBridge):
    def receive(self,text,context):
        r=self._resolver(context)
        if r.pending and not r.pending.get("candidate"):
            decision=classify(text)
            if decision["intent"]=="ANSWER":
                output=super().receive(decision["canonical"],context)
                output["normalization"]=decision
                return output
            if decision["intent"]=="SWITCH":
                r.clear()
                # Real DSS may ask for details: do not invent a purpose.
                output=super().receive(text,context)
                output["interruption"]="indirect_switch"
                output["normalization"]=decision
                return output
        return super().receive(text,context)

def demo(path):
    b=NormalizedClarificationBridge(JsonCandidateStore(path))
    inputs=[("昨日の実験の続きをやって","A"),
            ("カーソルの方","A"),
            ("昨日の実験の続きをやって","B"),
            ("別件を先に相談したい","B"),
            ("前回の実験を再開して","C"),
            ("意味記憶の実験","C")]
    results=[]
    for text,ctx in inputs:
        results.append({"context":ctx,"input":text,"result":b.receive(text,ctx)})
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--demo",action="store_true")
    p.add_argument("--out",default="results/clarification_normalization_v023343.json")
    p.add_argument("--shadow-store",default="results/normalization_shadow_v023343.json")
    a=p.parse_args()
    if not a.demo:print("Use --demo; no production Semantic Memory writes.");return
    out=Path(a.out);shadow=Path(a.shadow_store)
    if out.exists() or shadow.exists():raise FileExistsError("Refusing overwrite")
    result={"version":"v0.2.33.43","demo":demo(shadow),
      "limits":["Rule-based normalizer, not learned semantic inference",
                "Requires explicit separate confirm() before approval",
                "Experimental JSON candidate storage only"]}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps(result["demo"],ensure_ascii=False,indent=2))
    print("Saved",out)
if __name__=="__main__":main()

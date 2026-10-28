"""Compare v0.13.58.39 raw LLM answers with v0.13.58.40 rule baseline.

This comparison is on development prompts and uses lexical target-term checks;
it does NOT establish independent generalization or semantic equivalence.
"""
import argparse,json
from pathlib import Path
from semantic_composition_v0135840 import answer
MAP={
 "paraphrase_author":["夏目漱石"],
 "paraphrase_narrator":["猫"],
 "paraphrase_theme":["人間"],
 "reverse_author":["夏目漱石"],
 "compound":["夏目漱石","猫"],
 "compound_theme":["猫","人間"],
}
def run(previous,output):
 if output.exists():raise FileExistsError(output)
 old=json.loads(previous.read_text(encoding="utf-8-sig"))
 if old.get("version")!="v0.13.58.39" or old.get("status")!="PAIRED_EVALUATION_COMPLETE":
  raise ValueError("not previous generalization evaluation")
 cases=[];found=set()
 for item in old["items"]:
  id=item["id"]
  if id not in MAP:continue
  found.add(id);text=item["by_model"]["final"]["answer"];terms=MAP[id]
  revised=answer(item["user"])
  semantic_text=revised["answer"] or ""
  cases.append({"id":id,"user":item["user"],
   "llm_answer":text,"llm_required_terms_present":all(t in text for t in terms),
   "rule_answer":revised["answer"],"rule_status":revised["status"],
   "rule_required_terms_present":all(t in semantic_text for t in terms),
   "provenance_source_ids":revised["sources"]})
 if set(MAP)!=found:raise ValueError("missing comparison cases")
 report={"version":"v0.13.58.40","status":"COMPARISON_COMPLETE",
   "comparison":"DEVELOPMENT_PROMPTS_LEXICAL_CRITERION",
   "llm_exact_semantic_accuracy_claimed":False,
   "holdout_independence_attested":False,
   "count":len(cases),
   "llm_term_hits":sum(x["llm_required_terms_present"] for x in cases),
   "rule_term_hits":sum(x["rule_required_terms_present"] for x in cases),
   "cases":cases}
 output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"count":report["count"],"llm_term_hits":report["llm_term_hits"],
  "rule_term_hits":report["rule_term_hits"]},ensure_ascii=False))
 print("report:",output)
 return report
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--previous",type=Path,default=Path("results/generalization_v0135839.json"))
 p.add_argument("--output",type=Path,default=Path("results/semantic_comparison_v0135840.json"))
 a=p.parse_args();run(a.previous,a.output)
if __name__=="__main__":main()

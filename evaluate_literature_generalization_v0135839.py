"""v0.13.58.39: no-training paired exact/heldout generation audit.

The novel questions are unexposed candidates, NOT attested independent holdout.
Reports generation and lightweight keyword hits, not semantic accuracy.
"""
import argparse,hashlib,json
from pathlib import Path
from train_iterative_corrective_v0135832 import generate,exact_match
from text_integrity_gate_v0135837 import defects

FINAL_SHA="39fc1dbb6984e7be0bc500854ed4c66f380852a7761d8d9e4af81495f4c0bea4"
BASE_SHA="7e23f8164ad8e8ed9b5dfcfb177a5244ecbcd51c956fb30787bd3d5bf8128469"
NEW=[
 ("paraphrase_author","『吾輩は猫である』を書いた作家の名前は？",["夏目漱石"]),
 ("paraphrase_narrator","この小説『吾輩は猫である』は誰の視点で語られる？",["猫"]),
 ("paraphrase_theme","『吾輩は猫である』で描かれている社会は？",["人間"]),
 ("reverse_author","『吾輩は猫である』を書いたのは漱石ですか？",["夏目漱石"]),
 ("compound","『吾輩は猫である』の著者と語り手を教えて。",["夏目漱石","猫"]),
 ("compound_theme","夏目漱石の『吾輩は猫である』の視点とテーマを説明して。",["猫","人間"]),
 ("conversational","こんにちは。最近は何を読んでいる？",[]),
 ("persona_context","長門有希はどんな環境を好む？",["静か"])
]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def jsonl(path):
 return [json.loads(line) for line in path.read_text(encoding="utf-8-sig",errors="strict").splitlines() if line.strip()]
def prepare(a):
 if a.output.exists():raise FileExistsError(a.output)
 if sha(a.final)!=FINAL_SHA or sha(a.base)!=BASE_SHA:raise ValueError("checkpoint SHA mismatch")
 rep=json.loads(a.final_report.read_text(encoding="utf-8-sig"))
 if rep.get("version")!="v0.13.58.38" or rep.get("status")!="ALL_STAGES_EXACT" or rep.get("latest_sha256")!=FINAL_SHA:
  raise ValueError("invalid final report provenance")
 if sha(a.stages)!=rep.get("stages_sha256"):raise ValueError("stage source changed")
 rows={r["id"]:r for r in jsonl(a.reviewed)}
 facts={r["id"]:r for r in jsonl(a.facts)}
 stages=jsonl(a.stages)
 earlier=jsonl(a.earlier_stages)
 seen=[rows[k] for k in ("correct-talk-001","correct-cpu-002","correct-persona-003","correct-tired-008",
  "protect-identity-005","protect-greeting-006","protect-quantum-007")]
 seen+=[earlier[0]]+[facts[k] for k in ("lit-author","lit-narrator","lit-title")]+[stages[-1]]
 seen_questions={x["user"] for x in seen}
 for p in NEW:
  if p[1] in seen_questions:raise ValueError("evaluation item repeats training prompt")
 if not 1<=a.max_new_tokens<=256:raise ValueError("invalid max tokens")
 return seen
def run(a):
 seen=prepare(a)
 import torch
 from model import LanguageModel
 from tokenizer_bpe import Tokenizer
 device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
 tok=Tokenizer.load(str(a.tokenizer))
 models={}
 for key,path in (("baseline",a.base),("final",a.final)):
  model,_=LanguageModel.load_checkpoint(str(path),device=device)
  if model.vocab_size!=tok.vocab_size:raise ValueError("vocab mismatch")
  models[key]=model
 rows=[]
 for r in seen:
  item={"id":r["id"],"user":r["user"],"group":"TRAIN_EXPOSED","reference":r["assistant"],"by_model":{}}
  for key,m in models.items():
   ans=generate(m,tok,r,a.max_new_tokens)
   item["by_model"][key]={"answer":ans,"exact":not defects(ans) and exact_match(ans,r["assistant"]),
                        "integrity_issues":defects(ans)}
  rows.append(item)
 for id,user,terms in NEW:
  item={"id":id,"user":user,"group":"UNEXPOSED_CANDIDATE_NOT_INDEPENDENT",
        "expected_terms":terms,"by_model":{}}
  for key,m in models.items():
   ans=generate(m,tok,{"user":user},a.max_new_tokens)
   item["by_model"][key]={"answer":ans,"term_hits":[x for x in terms if x in ans],
                           "all_term_hits":bool(terms) and all(x in ans for x in terms),
                           "integrity_issues":defects(ans),"semantic_correctness_verified":False}
  rows.append(item)
 summary={}
 for key in models:
  train=[r["by_model"][key] for r in rows if r["group"]=="TRAIN_EXPOSED"]
  novel=[r["by_model"][key] for r in rows if r["group"]!="TRAIN_EXPOSED"]
  summary[key]={"train_exact":sum(bool(x["exact"]) for x in train),"train_total":len(train),
    "novel_keyword_hits":sum(bool(x["all_term_hits"]) for x in novel),
    "novel_with_keywords":sum(bool(r["expected_terms"]) for r in rows if r["group"]!="TRAIN_EXPOSED"),
    "novel_integrity_failures":sum(bool(x["integrity_issues"]) for x in novel)}
 result={"version":"v0.13.58.39","status":"PAIRED_EVALUATION_COMPLETE",
  "baseline_sha256":sha(a.base),"final_sha256":sha(a.final),
  "training_performed":False,"holdout_independence_attested":False,
  "novel_questions_not_in_training_prompts":True,"semantic_accuracy_claimed":False,
  "summary":summary,"items":rows}
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":result["status"],"summary":summary},ensure_ascii=False,indent=2))
 print("report:",a.output)
 return result
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--base",type=Path,default=Path("results/staged_literature_v0135834/literature-stage-1.pt"))
 p.add_argument("--final",type=Path,default=Path("results/literature_theme_v0135838/theme-stage-3.pt"))
 p.add_argument("--final-report",type=Path,default=Path("results/literature_theme_v0135838/report.json"))
 p.add_argument("--stages",type=Path,default=Path("data/literature_theme_stages_v0135838.jsonl"))
 p.add_argument("--earlier-stages",type=Path,default=Path("data/literature_stages_reviewed_v0135834.jsonl"))
 p.add_argument("--reviewed",type=Path,default=Path("data/corrective_sft_reviewed_v0135829.jsonl"))
 p.add_argument("--facts",type=Path,default=Path("data/literature_fact_corrections_v0135836.jsonl"))
 p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
 p.add_argument("--output",type=Path,default=Path("results/generalization_v0135839.json"))
 p.add_argument("--max-new-tokens",type=int,default=64)
 run(p.parse_args())
if __name__=="__main__":main()
